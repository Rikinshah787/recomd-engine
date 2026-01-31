"""
Uber Shopping Ranking Engine

Core ranking pipeline:
1. Candidate Retrieval (FAISS vector similarity)
2. Feature Enrichment (price, popularity, category match)
3. Weighted Scoring (configurable weights)
4. Re-ranking (top-K selection)
"""

import json
import numpy as np
from pathlib import Path
from typing import Optional
from sentence_transformers import SentenceTransformer
import faiss


class ShoppingRankingEngine:
    """
    Shopping-focused ranking engine.
    Combines semantic similarity with shopping signals.
    """
    
    # Default ranking weights (Uber-style)
    DEFAULT_WEIGHTS = {
        "text_similarity": 0.40,    # How well query matches product
        "price_score": 0.20,        # Competitive pricing
        "popularity_score": 0.20,   # Market demand signal
        "rating_score": 0.10,       # Quality signal
        "review_trust": 0.05,       # Trust signal
        "in_stock_bonus": 0.05      # Availability
    }
    
    def __init__(self, data_dir: str = None):
        """Initialize the ranking engine."""
        if data_dir is None:
            data_dir = Path(__file__).parent.parent / "data"
        else:
            data_dir = Path(data_dir)
        
        self.data_dir = data_dir
        self._load_resources()
    
    def _load_resources(self):
        """Load all required resources."""
        print("🔄 Loading ranking engine resources...")
        
        # Load embedding model
        print("   Loading embedding model...")
        self.model = SentenceTransformer('all-MiniLM-L6-v2')
        
        # Load FAISS index
        print("   Loading FAISS index...")
        index_path = self.data_dir / "product_index.faiss"
        self.index = faiss.read_index(str(index_path))
        
        # Load embeddings for recommendations
        print("   Loading embeddings...")
        embeddings_path = self.data_dir / "embeddings.npy"
        self.embeddings = np.load(embeddings_path)
        
        # Load products
        print("   Loading products...")
        products_path = self.data_dir / "products_clean.json"
        with open(products_path, "r", encoding="utf-8") as f:
            self.products = json.load(f)
        
        # Create product lookup
        self.product_lookup = {p["product_id"]: p for p in self.products}
        
        # Load features
        print("   Loading features...")
        features_path = self.data_dir / "products_features.json"
        with open(features_path, "r", encoding="utf-8") as f:
            self.features = json.load(f)
        
        # Load ID mappings
        print("   Loading ID mappings...")
        mappings_path = self.data_dir / "id_mappings.json"
        with open(mappings_path, "r", encoding="utf-8") as f:
            mappings = json.load(f)
        self.id_to_idx = {k: int(v) for k, v in mappings["id_to_idx"].items()}
        self.idx_to_id = {int(k): v for k, v in mappings["idx_to_id"].items()}
        
        # Extract unique categories for matching
        self.categories = list(set(p["category"] for p in self.products))
        self.subcategories = list(set(p["subcategory"] for p in self.products))
        
        print("✅ Ranking engine ready!")
    
    def _embed_query(self, query: str) -> np.ndarray:
        """Embed user query."""
        return self.model.encode([query], normalize_embeddings=True)
    
    def _retrieve_candidates(self, query_embedding: np.ndarray, top_k: int = 100) -> list:
        """
        Stage 1: Candidate Retrieval
        Fast approximate nearest neighbor search using FAISS.
        """
        distances, indices = self.index.search(query_embedding, top_k)
        
        candidates = []
        for dist, idx in zip(distances[0], indices[0]):
            product_id = self.idx_to_id[idx]
            candidates.append({
                "product_id": product_id,
                "vector_similarity": float(dist),
                "index": idx
            })
        
        return candidates
    
    def _infer_category_intent(self, query: str) -> Optional[str]:
        """
        Infer category from query using keyword matching.
        In production, this would use ML classification.
        """
        query_lower = query.lower()
        
        category_keywords = {
            "Electronics": ["phone", "laptop", "headphone", "speaker", "camera", "tablet", "watch", "gaming", "bluetooth", "wireless"],
            "Clothing": ["shirt", "pants", "dress", "jacket", "shoes", "clothing", "wear", "fashion", "jeans"],
            "Home & Kitchen": ["kitchen", "cook", "appliance", "home", "furniture", "bedding", "storage"],
            "Sports & Outdoors": ["sport", "fitness", "gym", "outdoor", "running", "yoga", "cycling", "camping"],
            "Beauty & Personal Care": ["beauty", "skincare", "makeup", "hair", "fragrance", "grooming"],
            "Books & Media": ["book", "reading", "novel", "guide", "audiobook"],
            "Toys & Games": ["toy", "game", "puzzle", "lego", "kids", "children"]
        }
        
        for category, keywords in category_keywords.items():
            if any(kw in query_lower for kw in keywords):
                return category
        
        return None
    
    def _infer_price_intent(self, query: str) -> Optional[str]:
        """
        Infer price preference from query.
        Returns: 'budget', 'mid', 'premium', or None
        """
        query_lower = query.lower()
        
        if any(kw in query_lower for kw in ["cheap", "budget", "affordable", "low price", "deal"]):
            return "budget"
        elif any(kw in query_lower for kw in ["premium", "luxury", "high-end", "best", "top"]):
            return "premium"
        
        return None
    
    def _enrich_features(
        self,
        candidates: list,
        query: str,
        category_intent: Optional[str] = None,
        price_intent: Optional[str] = None,
        user_budget: Optional[float] = None
    ) -> list:
        """
        Stage 2: Feature Enrichment
        Add shopping-specific features to each candidate.
        """
        enriched = []
        
        for candidate in candidates:
            product_id = candidate["product_id"]
            product = self.product_lookup[product_id]
            features = self.features[product_id]
            
            # Base features from pre-computed
            enriched_candidate = {
                **candidate,
                "product": product,
                "text_similarity": candidate["vector_similarity"],
                "price_score": features["price_score"],
                "popularity_score": features["popularity_score"],
                "rating_score": features["rating_score"],
                "review_trust": features["review_trust_score"],
                "in_stock_bonus": features["in_stock"]
            }
            
            # Category match bonus
            if category_intent and product["category"] == category_intent:
                enriched_candidate["category_match"] = 1.0
            else:
                enriched_candidate["category_match"] = 0.0
            
            # Price intent adjustment
            if price_intent == "budget":
                # Boost cheaper products
                enriched_candidate["price_score"] = enriched_candidate["price_score"] * 1.5
            elif price_intent == "premium":
                # Boost more expensive products (invert price score)
                enriched_candidate["price_score"] = 1 - enriched_candidate["price_score"]
            
            # Budget match (if user specified budget)
            if user_budget:
                if product["price"] <= user_budget:
                    enriched_candidate["budget_match"] = 1.0
                else:
                    # Penalize over-budget items proportionally
                    over_ratio = product["price"] / user_budget
                    enriched_candidate["budget_match"] = max(0, 1 - (over_ratio - 1))
            else:
                enriched_candidate["budget_match"] = 0.5
            
            enriched.append(enriched_candidate)
        
        return enriched
    
    def _compute_final_score(
        self,
        candidates: list,
        weights: dict = None
    ) -> list:
        """
        Stage 3: Weighted Scoring
        Compute final ranking score for each candidate.
        """
        if weights is None:
            weights = self.DEFAULT_WEIGHTS
        
        for candidate in candidates:
            final_score = (
                weights.get("text_similarity", 0.4) * candidate["text_similarity"] +
                weights.get("price_score", 0.2) * min(1.0, candidate["price_score"]) +
                weights.get("popularity_score", 0.2) * candidate["popularity_score"] +
                weights.get("rating_score", 0.1) * candidate["rating_score"] +
                weights.get("review_trust", 0.05) * candidate["review_trust"] +
                weights.get("in_stock_bonus", 0.05) * candidate["in_stock_bonus"]
            )
            
            # Category match bonus (additive)
            if candidate.get("category_match", 0) > 0:
                final_score += 0.1
            
            candidate["final_score"] = round(final_score, 4)
            candidate["score_breakdown"] = {
                "text_similarity": round(candidate["text_similarity"], 4),
                "price_score": round(min(1.0, candidate["price_score"]), 4),
                "popularity_score": round(candidate["popularity_score"], 4),
                "rating_score": round(candidate["rating_score"], 4),
                "category_match": candidate.get("category_match", 0)
            }
        
        return candidates
    
    def _rerank(self, candidates: list, top_k: int = 20) -> list:
        """
        Stage 4: Re-ranking
        Sort by final score and return top-K.
        """
        sorted_candidates = sorted(candidates, key=lambda x: x["final_score"], reverse=True)
        return sorted_candidates[:top_k]
    
    def search(
        self,
        query: str,
        top_k: int = 20,
        candidate_pool: int = 100,
        user_budget: Optional[float] = None,
        category_filter: Optional[str] = None,
        weights: dict = None
    ) -> list:
        """
        Full ranking pipeline.
        
        Args:
            query: User search query
            top_k: Number of results to return
            candidate_pool: Size of initial candidate set
            user_budget: Optional max price filter
            category_filter: Optional category filter
            weights: Optional custom ranking weights
        
        Returns:
            List of ranked products with scores and explanations
        """
        # Embed query
        query_embedding = self._embed_query(query)
        
        # Stage 1: Retrieve candidates
        candidates = self._retrieve_candidates(query_embedding, candidate_pool)
        
        # Apply category filter if specified
        if category_filter:
            candidates = [
                c for c in candidates
                if self.product_lookup[c["product_id"]]["category"] == category_filter
            ]
        
        # Infer intents from query
        category_intent = self._infer_category_intent(query) or category_filter
        price_intent = self._infer_price_intent(query)
        
        # Stage 2: Enrich features
        candidates = self._enrich_features(
            candidates,
            query,
            category_intent=category_intent,
            price_intent=price_intent,
            user_budget=user_budget
        )
        
        # Stage 3: Compute scores
        candidates = self._compute_final_score(candidates, weights)
        
        # Stage 4: Re-rank
        ranked = self._rerank(candidates, top_k)
        
        # Format results
        results = []
        for rank, candidate in enumerate(ranked, 1):
            product = candidate["product"]
            results.append({
                "rank": rank,
                "product_id": product["product_id"],
                "title": product["title"],
                "description": product["description"],
                "category": product["category"],
                "subcategory": product["subcategory"],
                "brand": product["brand"],
                "price": product["price"],
                "rating": product["rating"],
                "review_count": product["review_count"],
                "in_stock": product["in_stock"],
                "image_url": product["image_url"],
                "final_score": candidate["final_score"],
                "score_breakdown": candidate["score_breakdown"]
            })
        
        return results
    
    def get_product(self, product_id: str) -> Optional[dict]:
        """Get a single product by ID."""
        return self.product_lookup.get(product_id)
    
    def get_similar_products(self, product_id: str, top_k: int = 10) -> list:
        """
        Find similar products using embedding similarity.
        For recommendations: "Similar items you might like"
        """
        if product_id not in self.id_to_idx:
            return []
        
        idx = self.id_to_idx[product_id]
        product_embedding = self.embeddings[idx:idx+1]
        
        # Search for nearest neighbors (k+1 because it includes itself)
        distances, indices = self.index.search(product_embedding, top_k + 1)
        
        results = []
        for dist, neighbor_idx in zip(distances[0], indices[0]):
            neighbor_id = self.idx_to_id[neighbor_idx]
            if neighbor_id != product_id:  # Exclude the product itself
                product = self.product_lookup[neighbor_id]
                results.append({
                    "product_id": neighbor_id,
                    "title": product["title"],
                    "category": product["category"],
                    "price": product["price"],
                    "rating": product["rating"],
                    "image_url": product["image_url"],
                    "similarity_score": round(float(dist), 4)
                })
        
        return results[:top_k]
    
    def get_complementary_products(self, product_id: str, top_k: int = 5) -> list:
        """
        Find complementary products.
        For recommendations: "Frequently bought together"
        """
        if product_id not in self.product_lookup:
            return []
        
        product = self.product_lookup[product_id]
        category = product["category"]
        subcategory = product["subcategory"]
        
        # Complementary category mappings (shopping-style)
        complements = {
            "Laptops": ["Headphones", "Speakers", "Gaming"],
            "Smartphones": ["Headphones", "Smartwatches", "Speakers"],
            "Headphones": ["Smartphones", "Laptops", "Speakers"],
            "Cameras": ["Tablets", "Laptops", "Gaming"],
            "T-Shirts": ["Jeans", "Shoes", "Accessories"],
            "Jeans": ["T-Shirts", "Shoes", "Jackets"],
            "Shoes": ["T-Shirts", "Jeans", "Activewear"],
            "Cookware": ["Appliances", "Storage", "Cleaning"],
            "Fitness": ["Running", "Yoga", "Swimming"],
            "Skincare": ["Haircare", "Bath & Body", "Makeup"]
        }
        
        # Get complementary subcategories
        complement_subs = complements.get(subcategory, [])
        
        # Find products in complementary categories
        candidates = []
        for p in self.products:
            if p["product_id"] != product_id:
                if p["subcategory"] in complement_subs or (p["category"] == category and p["subcategory"] != subcategory):
                    candidates.append(p)
        
        # Sort by popularity and rating
        candidates.sort(key=lambda x: (x["popularity_score"], x["rating"]), reverse=True)
        
        results = []
        for p in candidates[:top_k]:
            results.append({
                "product_id": p["product_id"],
                "title": p["title"],
                "category": p["category"],
                "subcategory": p["subcategory"],
                "price": p["price"],
                "rating": p["rating"],
                "image_url": p["image_url"],
                "reason": f"Pairs well with {subcategory}"
            })
        
        return results


# Singleton instance for FastAPI
_engine_instance = None

def get_engine() -> ShoppingRankingEngine:
    """Get or create the ranking engine singleton."""
    global _engine_instance
    if _engine_instance is None:
        _engine_instance = ShoppingRankingEngine()
    return _engine_instance
