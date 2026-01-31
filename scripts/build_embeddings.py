"""
Uber Shopping Ranking - Embedding & Feature Builder

Generates text embeddings using Sentence-Transformers and builds FAISS index.
Computes normalized features for ranking.
"""

import json
import numpy as np
from pathlib import Path
from sentence_transformers import SentenceTransformer
import faiss


def load_products(data_path: Path) -> list:
    """Load products from JSON."""
    with open(data_path, "r", encoding="utf-8") as f:
        return json.load(f)


def create_text_for_embedding(product: dict) -> str:
    """
    Create searchable text representation for embedding.
    Focus on what shoppers actually search for.
    """
    return f"{product['title']} {product['category']} {product['subcategory']} {product['brand']} {product['description']}"


def compute_normalized_features(products: list) -> dict:
    """
    Compute normalized features for ranking.
    
    Shopping-focused normalization:
    - Price: Lower is better (inverted, normalized 0-1)
    - Popularity: Higher is better (already 0-1)
    - Rating: Higher is better (normalized 0-1)
    - Review count: Log-normalized (more reviews = more trust)
    """
    # Extract raw values
    prices = [p["price"] for p in products]
    ratings = [p["rating"] for p in products]
    review_counts = [p["review_count"] for p in products]
    
    # Price normalization (inverted - lower price = higher score)
    min_price, max_price = min(prices), max(prices)
    price_range = max_price - min_price
    
    # Rating normalization (3.0 to 5.0 -> 0 to 1)
    min_rating, max_rating = min(ratings), max(ratings)
    rating_range = max_rating - min_rating
    
    # Review count log normalization
    log_reviews = [np.log1p(r) for r in review_counts]
    min_log, max_log = min(log_reviews), max(log_reviews)
    log_range = max_log - min_log
    
    features = {}
    for i, p in enumerate(products):
        # Price score: inverted (cheaper = higher score)
        price_score = 1 - (p["price"] - min_price) / price_range if price_range > 0 else 0.5
        
        # Rating score: normalized
        rating_score = (p["rating"] - min_rating) / rating_range if rating_range > 0 else 0.5
        
        # Review trust score: log-normalized
        review_score = (log_reviews[i] - min_log) / log_range if log_range > 0 else 0.5
        
        features[p["product_id"]] = {
            "price_score": round(price_score, 4),
            "popularity_score": p["popularity_score"],
            "rating_score": round(rating_score, 4),
            "review_trust_score": round(review_score, 4),
            "in_stock": 1.0 if p["in_stock"] else 0.0,
            "category": p["category"],
            "subcategory": p["subcategory"],
            "brand": p["brand"],
            "price": p["price"]
        }
    
    return features


def build_faiss_index(embeddings: np.ndarray) -> faiss.IndexFlatIP:
    """
    Build FAISS index for fast similarity search.
    Using Inner Product (cosine similarity with normalized vectors).
    """
    # Normalize embeddings for cosine similarity
    faiss.normalize_L2(embeddings)
    
    # Create index
    dimension = embeddings.shape[1]
    index = faiss.IndexFlatIP(dimension)  # Inner product = cosine sim for normalized vectors
    index.add(embeddings)
    
    return index


def main():
    """Main execution."""
    print("🔢 Uber Shopping Ranking - Embedding Builder")
    print("=" * 50)
    
    # Paths
    data_dir = Path(__file__).parent.parent / "data"
    products_path = data_dir / "products_clean.json"
    
    # Load products
    print("\n📦 Loading products...")
    products = load_products(products_path)
    print(f"   Loaded {len(products)} products")
    
    # Create text representations
    print("\n📝 Creating text representations...")
    texts = [create_text_for_embedding(p) for p in products]
    
    # Load embedding model
    print("\n🤖 Loading Sentence-Transformer model...")
    print("   Model: all-MiniLM-L6-v2 (384 dimensions, fast, free)")
    model = SentenceTransformer('all-MiniLM-L6-v2')
    
    # Generate embeddings
    print("\n⚡ Generating embeddings (this may take 1-2 minutes)...")
    embeddings = model.encode(
        texts,
        show_progress_bar=True,
        convert_to_numpy=True,
        normalize_embeddings=True  # Pre-normalize for cosine similarity
    )
    print(f"   Generated embeddings: {embeddings.shape}")
    
    # Build FAISS index
    print("\n🔍 Building FAISS index...")
    index = build_faiss_index(embeddings.copy())  # Copy because normalize_L2 modifies in place
    print(f"   Index size: {index.ntotal} vectors")
    
    # Compute normalized features
    print("\n📊 Computing normalized features...")
    features = compute_normalized_features(products)
    
    # Create product ID to index mapping
    id_to_idx = {p["product_id"]: i for i, p in enumerate(products)}
    idx_to_id = {i: p["product_id"] for i, p in enumerate(products)}
    
    # Save everything
    print("\n💾 Saving artifacts...")
    
    # Save FAISS index
    index_path = data_dir / "product_index.faiss"
    faiss.write_index(index, str(index_path))
    print(f"   Saved FAISS index to {index_path}")
    
    # Save embeddings as numpy array (for recommendations)
    embeddings_path = data_dir / "embeddings.npy"
    np.save(embeddings_path, embeddings)
    print(f"   Saved embeddings to {embeddings_path}")
    
    # Save features
    features_path = data_dir / "products_features.json"
    with open(features_path, "w", encoding="utf-8") as f:
        json.dump(features, f, indent=2)
    print(f"   Saved features to {features_path}")
    
    # Save ID mappings
    mappings = {"id_to_idx": id_to_idx, "idx_to_id": idx_to_id}
    mappings_path = data_dir / "id_mappings.json"
    with open(mappings_path, "w", encoding="utf-8") as f:
        json.dump(mappings, f, indent=2)
    print(f"   Saved ID mappings to {mappings_path}")
    
    print("\n✅ Embedding pipeline complete!")
    print("\n📁 Generated files:")
    print(f"   - {index_path.name} (FAISS vector index)")
    print(f"   - {embeddings_path.name} (raw embeddings)")
    print(f"   - {features_path.name} (normalized features)")
    print(f"   - {mappings_path.name} (product ID mappings)")
    
    # Quick test
    print("\n🧪 Quick test - searching for 'wireless headphones'...")
    test_query = "wireless headphones bluetooth"
    query_embedding = model.encode([test_query], normalize_embeddings=True)
    
    distances, indices = index.search(query_embedding, 5)
    print("   Top 5 results:")
    for i, (dist, idx) in enumerate(zip(distances[0], indices[0]), 1):
        product_id = idx_to_id[idx]
        product = products[idx]
        print(f"   {i}. [{product_id}] {product['title'][:50]}... (score: {dist:.4f})")


if __name__ == "__main__":
    main()
