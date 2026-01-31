"""
Uber Shopping Ranking - Explanation Generator

Generates natural-language explanations for why products are ranked.
Makes the ranking transparent and trustworthy.
"""

from typing import Dict, List


class ExplanationGenerator:
    """
    Generates human-readable explanations for ranking decisions.
    Uber-style: transparent, concise, actionable.
    """
    
    # Highlight templates based on score breakdown
    HIGHLIGHTS = {
        "best_match": "🎯 Best Match",
        "top_rated": "⭐ Top Rated",
        "best_value": "💰 Best Value",
        "popular_choice": "🔥 Popular Choice",
        "category_match": "📦 Category Match",
        "in_stock": "✅ In Stock"
    }
    
    def generate_explanation(
        self,
        rank: int,
        product: dict,
        score_breakdown: dict,
        query: str
    ) -> dict:
        """
        Generate explanation for a single ranked product.
        
        Returns:
            {
                "short": "One sentence explanation",
                "highlights": ["Badge 1", "Badge 2"],
                "factors": {"factor": "contribution description"}
            }
        """
        # Determine primary ranking factors
        factors = []
        highlights = []
        
        # Text similarity (query match)
        text_sim = score_breakdown.get("text_similarity", 0)
        if text_sim > 0.7:
            factors.append(f"closely matches your search '{query}'")
            highlights.append(self.HIGHLIGHTS["best_match"])
        elif text_sim > 0.5:
            factors.append("matches your search query")
        
        # Rating
        rating_score = score_breakdown.get("rating_score", 0)
        if rating_score > 0.8:
            factors.append(f"highly rated ({product.get('rating', 0)}★)")
            highlights.append(self.HIGHLIGHTS["top_rated"])
        elif rating_score > 0.6:
            factors.append("well rated by customers")
        
        # Price
        price_score = score_breakdown.get("price_score", 0)
        if price_score > 0.7:
            factors.append("competitively priced")
            highlights.append(self.HIGHLIGHTS["best_value"])
        
        # Popularity
        popularity = score_breakdown.get("popularity_score", 0)
        if popularity > 0.7:
            factors.append(f"popular in {product.get('category', 'this category')}")
            highlights.append(self.HIGHLIGHTS["popular_choice"])
        
        # Category match
        if score_breakdown.get("category_match", 0) > 0:
            factors.append(f"exact category match ({product.get('subcategory', '')})")
            highlights.append(self.HIGHLIGHTS["category_match"])
        
        # In stock
        if product.get("in_stock", False):
            highlights.append(self.HIGHLIGHTS["in_stock"])
        
        # Build short explanation
        if rank == 1:
            prefix = "Ranked #1 because it"
        elif rank <= 3:
            prefix = "Top result because it"
        elif rank <= 10:
            prefix = "Highly ranked because it"
        else:
            prefix = "Ranked here because it"
        
        if factors:
            short = f"{prefix} {', '.join(factors[:3])}."
        else:
            short = f"{prefix} is a good match for your search."
        
        # Dedupe highlights
        highlights = list(dict.fromkeys(highlights))[:4]
        
        return {
            "short": short,
            "highlights": highlights,
            "detailed_factors": {
                "query_match": f"{text_sim*100:.0f}% match",
                "price_competitiveness": f"{price_score*100:.0f}% score",
                "popularity": f"{popularity*100:.0f}% popular",
                "rating": f"{product.get('rating', 0)}★ ({product.get('review_count', 0)} reviews)"
            }
        }
    
    def generate_batch_explanations(
        self,
        results: List[dict],
        query: str
    ) -> List[dict]:
        """
        Generate explanations for a list of ranked results.
        """
        explained_results = []
        
        for result in results:
            explanation = self.generate_explanation(
                rank=result["rank"],
                product=result,
                score_breakdown=result.get("score_breakdown", {}),
                query=query
            )
            
            explained_results.append({
                **result,
                "explanation": explanation
            })
        
        return explained_results
    
    def generate_recommendation_reason(
        self,
        source_product: dict,
        recommended_product: dict,
        rec_type: str = "similar"
    ) -> str:
        """
        Generate explanation for why a product is recommended.
        
        Args:
            source_product: The product user is viewing
            recommended_product: The recommended product
            rec_type: "similar" or "complementary"
        """
        if rec_type == "similar":
            if source_product.get("category") == recommended_product.get("category"):
                if source_product.get("subcategory") == recommended_product.get("subcategory"):
                    return f"Similar {recommended_product.get('subcategory', 'product')} you might like"
                else:
                    return f"Also in {recommended_product.get('category', 'this category')}"
            else:
                return "Similar product based on your interest"
        
        elif rec_type == "complementary":
            return f"Pairs well with {source_product.get('title', 'your selection')[:30]}"
        
        return "You might also like"


# Singleton instance
_explainer_instance = None

def get_explainer() -> ExplanationGenerator:
    """Get or create the explainer singleton."""
    global _explainer_instance
    if _explainer_instance is None:
        _explainer_instance = ExplanationGenerator()
    return _explainer_instance
