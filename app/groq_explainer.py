"""
Uber Shopping Ranking - Groq-Powered Explanation Generator

Uses Groq's fast LLM API for dynamic, contextual explanations.
"""

import os
from typing import Optional
import httpx

# Groq API configuration
GROQ_API_URL = "https://api.groq.com/openai/v1/chat/completions"
GROQ_MODEL = "llama-3.1-8b-instant"  # Fast and free


class GroqExplainer:
    """
    Generates dynamic AI-powered explanations using Groq.
    Falls back to template-based explanations if API unavailable.
    """
    
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv("GROQ_API_KEY")
        self.enabled = bool(self.api_key)
        
        if not self.enabled:
            print("⚠️ GROQ_API_KEY not set - using template explanations")
    
    async def generate_explanation(
        self,
        rank: int,
        product: dict,
        score_breakdown: dict,
        query: str
    ) -> dict:
        """
        Generate AI-powered explanation for a product's ranking.
        """
        if not self.enabled:
            return self._template_explanation(rank, product, score_breakdown, query)
        
        try:
            prompt = self._build_prompt(rank, product, score_breakdown, query)
            response = await self._call_groq(prompt)
            
            return {
                "short": response,
                "highlights": self._extract_highlights(score_breakdown, product),
                "ai_generated": True
            }
        except Exception as e:
            print(f"Groq API error: {e}")
            return self._template_explanation(rank, product, score_breakdown, query)
    
    def _build_prompt(self, rank: int, product: dict, score_breakdown: dict, query: str) -> str:
        """Build the prompt for Groq."""
        return f"""You are a shopping assistant explaining product rankings.

User searched for: "{query}"
Product ranked #{rank}:
- Title: {product.get('title', '')}
- Category: {product.get('category', '')} > {product.get('subcategory', '')}
- Brand: {product.get('brand', '')}
- Price: ${product.get('price', 0):.2f}
- Rating: {product.get('rating', 0)}★

Ranking scores:
- Query match: {score_breakdown.get('text_similarity', 0)*100:.0f}%
- Price competitiveness: {score_breakdown.get('price_score', 0)*100:.0f}%
- Popularity: {score_breakdown.get('popularity_score', 0)*100:.0f}%

Write a single, concise sentence (max 20 words) explaining why this product is ranked #{rank} for this search.
Focus on the most relevant factors. Be specific and helpful.
Do not use phrases like "This product" - start directly with the reason."""

    async def _call_groq(self, prompt: str) -> str:
        """Call Groq API."""
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "model": GROQ_MODEL,
            "messages": [
                {"role": "system", "content": "You are a helpful shopping assistant that explains product rankings concisely."},
                {"role": "user", "content": prompt}
            ],
            "max_tokens": 60,
            "temperature": 0.7
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                GROQ_API_URL,
                headers=headers,
                json=payload,
                timeout=5.0
            )
            response.raise_for_status()
            data = response.json()
            
            return data["choices"][0]["message"]["content"].strip()
    
    def _extract_highlights(self, score_breakdown: dict, product: dict) -> list:
        """Extract highlight badges based on scores."""
        highlights = []
        
        if score_breakdown.get("text_similarity", 0) > 0.7:
            highlights.append("🎯 Best Match")
        
        if product.get("rating", 0) >= 4.5:
            highlights.append("⭐ Top Rated")
        
        if score_breakdown.get("price_score", 0) > 0.7:
            highlights.append("💰 Best Value")
        
        if score_breakdown.get("popularity_score", 0) > 0.7:
            highlights.append("🔥 Popular Choice")
        
        if product.get("in_stock", False):
            highlights.append("✅ In Stock")
        
        return highlights[:4]
    
    def _template_explanation(self, rank: int, product: dict, score_breakdown: dict, query: str) -> dict:
        """Fallback template-based explanation."""
        factors = []
        highlights = self._extract_highlights(score_breakdown, product)
        
        text_sim = score_breakdown.get("text_similarity", 0)
        if text_sim > 0.7:
            factors.append(f"closely matches '{query}'")
        elif text_sim > 0.5:
            factors.append("matches your search")
        
        if product.get("rating", 0) >= 4.5:
            factors.append(f"highly rated ({product.get('rating')}★)")
        
        if score_breakdown.get("price_score", 0) > 0.7:
            factors.append("competitively priced")
        
        if score_breakdown.get("popularity_score", 0) > 0.7:
            factors.append(f"popular in {product.get('category', 'this category')}")
        
        prefix = f"Ranked #{rank} because it " if rank <= 5 else "Ranked here because it "
        short = prefix + ", ".join(factors[:3]) + "." if factors else f"{prefix}is a good match."
        
        return {
            "short": short,
            "highlights": highlights,
            "ai_generated": False
        }


# Singleton
_groq_explainer = None

def get_groq_explainer() -> GroqExplainer:
    global _groq_explainer
    if _groq_explainer is None:
        _groq_explainer = GroqExplainer()
    return _groq_explainer
