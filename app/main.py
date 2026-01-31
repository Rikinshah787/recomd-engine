"""
Uber Shopping Ranking - FastAPI Backend

RESTful API for the Shopping Ranking & Recommendation System.
Endpoints:
- /search - Ranked product search with explanations
- /similar/{product_id} - Similar product recommendations  
- /complementary/{product_id} - Complementary product recommendations
- /product/{product_id} - Product details
"""

from fastapi import FastAPI, Query, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List
import time

from .ranking_engine import get_engine
from .explainer import get_explainer


# Initialize FastAPI
app = FastAPI(
    title="Uber Shopping Ranking API",
    description="AI-powered product ranking and recommendation system",
    version="1.0.0"
)

# CORS middleware for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Response models
class ScoreBreakdown(BaseModel):
    text_similarity: float
    price_score: float
    popularity_score: float
    rating_score: float
    category_match: float


class Explanation(BaseModel):
    short: str
    highlights: List[str]
    detailed_factors: dict


class RankedProduct(BaseModel):
    rank: int
    product_id: str
    title: str
    description: str
    category: str
    subcategory: str
    brand: str
    price: float
    rating: float
    review_count: int
    in_stock: bool
    image_url: str
    final_score: float
    score_breakdown: ScoreBreakdown
    explanation: Optional[Explanation] = None


class SearchResponse(BaseModel):
    query: str
    total_results: int
    latency_ms: float
    results: List[RankedProduct]


class SimilarProduct(BaseModel):
    product_id: str
    title: str
    category: str
    price: float
    rating: float
    image_url: str
    similarity_score: float


class ComplementaryProduct(BaseModel):
    product_id: str
    title: str
    category: str
    subcategory: str
    price: float
    rating: float
    image_url: str
    reason: str


class ProductDetail(BaseModel):
    product_id: str
    title: str
    description: str
    category: str
    subcategory: str
    brand: str
    price: float
    rating: float
    review_count: int
    in_stock: bool
    image_url: str
    popularity_score: float


# Health check
@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "service": "uber-shopping-ranking"}


# Search endpoint
@app.get("/search", response_model=SearchResponse)
async def search_products(
    query: str = Query(..., description="Search query"),
    top_k: int = Query(20, ge=1, le=100, description="Number of results"),
    budget: Optional[float] = Query(None, description="Max price filter"),
    category: Optional[str] = Query(None, description="Category filter")
):
    """
    Search and rank products.
    
    Returns ranked products with explanations for each ranking position.
    """
    start_time = time.time()
    
    # Get ranking engine and explainer
    engine = get_engine()
    explainer = get_explainer()
    
    # Execute search
    results = engine.search(
        query=query,
        top_k=top_k,
        user_budget=budget,
        category_filter=category
    )
    
    # Add explanations
    explained_results = explainer.generate_batch_explanations(results, query)
    
    latency_ms = (time.time() - start_time) * 1000
    
    return SearchResponse(
        query=query,
        total_results=len(explained_results),
        latency_ms=round(latency_ms, 2),
        results=explained_results
    )


# Similar products endpoint
@app.get("/similar/{product_id}", response_model=List[SimilarProduct])
async def get_similar_products(
    product_id: str,
    top_k: int = Query(10, ge=1, le=50, description="Number of results")
):
    """
    Get similar products based on embedding similarity.
    
    Use case: "Similar items you might like"
    """
    engine = get_engine()
    
    # Check if product exists
    product = engine.get_product(product_id)
    if not product:
        raise HTTPException(status_code=404, detail=f"Product {product_id} not found")
    
    similar = engine.get_similar_products(product_id, top_k)
    
    return similar


# Complementary products endpoint
@app.get("/complementary/{product_id}", response_model=List[ComplementaryProduct])
async def get_complementary_products(
    product_id: str,
    top_k: int = Query(5, ge=1, le=20, description="Number of results")
):
    """
    Get complementary products.
    
    Use case: "Frequently bought together" or "Pairs well with"
    """
    engine = get_engine()
    
    # Check if product exists
    product = engine.get_product(product_id)
    if not product:
        raise HTTPException(status_code=404, detail=f"Product {product_id} not found")
    
    complementary = engine.get_complementary_products(product_id, top_k)
    
    return complementary


# Product detail endpoint
@app.get("/product/{product_id}", response_model=ProductDetail)
async def get_product_detail(product_id: str):
    """
    Get detailed information about a single product.
    """
    engine = get_engine()
    
    product = engine.get_product(product_id)
    if not product:
        raise HTTPException(status_code=404, detail=f"Product {product_id} not found")
    
    return ProductDetail(**product)


# Categories endpoint
@app.get("/categories")
async def get_categories():
    """
    Get list of available categories.
    """
    engine = get_engine()
    return {
        "categories": engine.categories,
        "subcategories": engine.subcategories
    }


# Stats endpoint
@app.get("/stats")
async def get_stats():
    """
    Get system statistics.
    """
    engine = get_engine()
    return {
        "total_products": len(engine.products),
        "index_size": engine.index.ntotal,
        "embedding_dimension": engine.embeddings.shape[1],
        "categories": len(engine.categories),
        "subcategories": len(engine.subcategories)
    }


# Startup event
@app.on_event("startup")
async def startup_event():
    """Load resources on startup."""
    print("🚀 Starting Uber Shopping Ranking API...")
    # Pre-load the engine
    get_engine()
    print("✅ API ready!")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
