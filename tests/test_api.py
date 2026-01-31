"""
Uber Shopping Ranking - API Test Suite

Comprehensive tests for all endpoints.
"""

import requests
import time
import json

BASE_URL = "http://localhost:8000"


def test_health():
    """Test health endpoint."""
    print("\n🏥 Testing /health...")
    resp = requests.get(f"{BASE_URL}/health")
    assert resp.status_code == 200, f"Expected 200, got {resp.status_code}"
    data = resp.json()
    assert data["status"] == "healthy"
    print(f"   ✅ Status: {data['status']}, Service: {data['service']}")
    return True


def test_stats():
    """Test stats endpoint."""
    print("\n📊 Testing /stats...")
    resp = requests.get(f"{BASE_URL}/stats")
    assert resp.status_code == 200
    data = resp.json()
    print(f"   ✅ Total products: {data['total_products']}")
    print(f"   ✅ Index size: {data['index_size']}")
    print(f"   ✅ Embedding dim: {data['embedding_dimension']}")
    print(f"   ✅ Categories: {data['categories']}")
    return True


def test_categories():
    """Test categories endpoint."""
    print("\n📁 Testing /categories...")
    resp = requests.get(f"{BASE_URL}/categories")
    assert resp.status_code == 200
    data = resp.json()
    print(f"   ✅ Categories: {len(data['categories'])}")
    print(f"   ✅ Subcategories: {len(data['subcategories'])}")
    print(f"   ✅ Sample: {data['categories'][:3]}")
    return True


def test_search_basic():
    """Test basic search."""
    print("\n🔍 Testing /search (basic)...")
    resp = requests.get(f"{BASE_URL}/search", params={
        "query": "wireless headphones",
        "top_k": 5
    })
    assert resp.status_code == 200
    data = resp.json()
    
    print(f"   ✅ Query: {data['query']}")
    print(f"   ✅ Results: {data['total_results']}")
    print(f"   ✅ Latency: {data['latency_ms']:.2f}ms")
    
    # Check first result
    if data['results']:
        r = data['results'][0]
        print(f"   ✅ Top result: {r['title'][:50]}...")
        print(f"   ✅ Score: {r['final_score']:.4f}")
        print(f"   ✅ Explanation: {r['explanation']['short'][:60]}...")
        print(f"   ✅ Highlights: {r['explanation']['highlights']}")
    
    return True


def test_search_with_budget():
    """Test search with budget filter."""
    print("\n💰 Testing /search (with budget)...")
    resp = requests.get(f"{BASE_URL}/search", params={
        "query": "laptop",
        "top_k": 5,
        "budget": 500
    })
    assert resp.status_code == 200
    data = resp.json()
    
    print(f"   ✅ Query: laptop (budget: $500)")
    print(f"   ✅ Results: {data['total_results']}")
    
    # Verify budget constraint helps ranking
    if data['results']:
        prices = [r['price'] for r in data['results']]
        print(f"   ✅ Prices: {prices}")
    
    return True


def test_search_with_category():
    """Test search with category filter."""
    print("\n📦 Testing /search (with category)...")
    resp = requests.get(f"{BASE_URL}/search", params={
        "query": "running shoes",
        "top_k": 5,
        "category": "Clothing"
    })
    assert resp.status_code == 200
    data = resp.json()
    
    print(f"   ✅ Query: running shoes (category: Clothing)")
    print(f"   ✅ Results: {data['total_results']}")
    
    # Verify category constraint
    if data['results']:
        categories = set(r['category'] for r in data['results'])
        print(f"   ✅ Categories in results: {categories}")
    
    return True


def test_product_detail():
    """Test product detail endpoint."""
    print("\n📋 Testing /product/{id}...")
    resp = requests.get(f"{BASE_URL}/product/P0001")
    assert resp.status_code == 200
    data = resp.json()
    
    print(f"   ✅ Product: {data['title'][:50]}...")
    print(f"   ✅ Category: {data['category']}")
    print(f"   ✅ Price: ${data['price']}")
    print(f"   ✅ Rating: {data['rating']}★")
    
    return True


def test_product_not_found():
    """Test product not found."""
    print("\n❌ Testing /product (not found)...")
    resp = requests.get(f"{BASE_URL}/product/INVALID")
    assert resp.status_code == 404
    print(f"   ✅ Correctly returns 404 for invalid product")
    return True


def test_similar_products():
    """Test similar products endpoint."""
    print("\n🔗 Testing /similar/{id}...")
    resp = requests.get(f"{BASE_URL}/similar/P0001", params={"top_k": 5})
    assert resp.status_code == 200
    data = resp.json()
    
    print(f"   ✅ Similar products found: {len(data)}")
    if data:
        print(f"   ✅ Top similar: {data[0]['title'][:40]}...")
        print(f"   ✅ Similarity: {data[0]['similarity_score']:.4f}")
    
    return True


def test_complementary_products():
    """Test complementary products endpoint."""
    print("\n🎁 Testing /complementary/{id}...")
    resp = requests.get(f"{BASE_URL}/complementary/P0001", params={"top_k": 5})
    assert resp.status_code == 200
    data = resp.json()
    
    print(f"   ✅ Complementary products found: {len(data)}")
    if data:
        print(f"   ✅ Recommendation: {data[0]['title'][:40]}...")
        print(f"   ✅ Reason: {data[0]['reason']}")
    
    return True


def test_multiple_queries():
    """Test various shopping queries."""
    print("\n🛒 Testing multiple shopping queries...")
    
    queries = [
        "cheap bluetooth speaker",
        "premium laptop for gaming",
        "comfortable running shoes",
        "kitchen appliances",
        "skincare products organic"
    ]
    
    for query in queries:
        resp = requests.get(f"{BASE_URL}/search", params={"query": query, "top_k": 3})
        assert resp.status_code == 200
        data = resp.json()
        top = data['results'][0] if data['results'] else None
        
        if top:
            print(f"   ✅ '{query}' → {top['title'][:35]}... (score: {top['final_score']:.3f})")
        else:
            print(f"   ⚠️ '{query}' → No results")
    
    return True


def test_latency():
    """Test response latency."""
    print("\n⏱️ Testing latency (10 requests)...")
    
    latencies = []
    for _ in range(10):
        start = time.time()
        resp = requests.get(f"{BASE_URL}/search", params={"query": "headphones", "top_k": 20})
        latencies.append((time.time() - start) * 1000)
    
    avg_latency = sum(latencies) / len(latencies)
    min_latency = min(latencies)
    max_latency = max(latencies)
    
    print(f"   ✅ Avg latency: {avg_latency:.2f}ms")
    print(f"   ✅ Min latency: {min_latency:.2f}ms")
    print(f"   ✅ Max latency: {max_latency:.2f}ms")
    
    return True


def run_all_tests():
    """Run all tests."""
    print("=" * 60)
    print("🧪 UBER SHOPPING RANKING - API TEST SUITE")
    print("=" * 60)
    
    tests = [
        ("Health Check", test_health),
        ("System Stats", test_stats),
        ("Categories", test_categories),
        ("Basic Search", test_search_basic),
        ("Search with Budget", test_search_with_budget),
        ("Search with Category", test_search_with_category),
        ("Product Detail", test_product_detail),
        ("Product Not Found", test_product_not_found),
        ("Similar Products", test_similar_products),
        ("Complementary Products", test_complementary_products),
        ("Multiple Queries", test_multiple_queries),
        ("Latency Test", test_latency),
    ]
    
    passed = 0
    failed = 0
    
    for name, test_fn in tests:
        try:
            test_fn()
            passed += 1
        except AssertionError as e:
            print(f"   ❌ FAILED: {e}")
            failed += 1
        except Exception as e:
            print(f"   ❌ ERROR: {e}")
            failed += 1
    
    print("\n" + "=" * 60)
    print(f"📊 TEST RESULTS: {passed} passed, {failed} failed")
    print("=" * 60)
    
    if failed == 0:
        print("🎉 ALL TESTS PASSED!")
    else:
        print("⚠️ Some tests failed - check output above")
    
    return failed == 0


if __name__ == "__main__":
    run_all_tests()
