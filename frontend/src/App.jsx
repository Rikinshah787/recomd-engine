import { useState, useEffect } from 'react'
import './App.css'

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'

// Clean SVG Icons - No emojis per UI guidelines
const SearchIcon = () => (
  <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round">
    <circle cx="11" cy="11" r="8" />
    <path d="m21 21-4.35-4.35" />
  </svg>
)

const StarIcon = () => (
  <svg width="18" height="18" viewBox="0 0 24 24" fill="currentColor">
    <path d="M12 2l3.09 6.26L22 9.27l-5 4.87 1.18 6.88L12 17.77l-6.18 3.25L7 14.14 2 9.27l6.91-1.01L12 2z" />
  </svg>
)

const UberLogo = () => (
  <svg width="24" height="24" viewBox="0 0 24 24" fill="currentColor">
    <path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm-1 17.93c-3.95-.49-7-3.85-7-7.93 0-.62.08-1.21.21-1.79L9 15v1c0 1.1.9 2 2 2v1.93zm6.9-2.54c-.26-.81-1-1.39-1.9-1.39h-1v-3c0-.55-.45-1-1-1H8v-2h2c.55 0 1-.45 1-1V7h2c1.1 0 2-.9 2-2v-.41c2.93 1.19 5 4.06 5 7.41 0 2.08-.8 3.97-2.1 5.39z" />
  </svg>
)

function App() {
  const [query, setQuery] = useState('')
  const [results, setResults] = useState([])
  const [loading, setLoading] = useState(false)
  const [latency, setLatency] = useState(null)
  const [budget, setBudget] = useState('')
  const [category, setCategory] = useState('')
  const [categories, setCategories] = useState([])
  const [stats, setStats] = useState(null)
  const [selectedProduct, setSelectedProduct] = useState(null)
  const [similarProducts, setSimilarProducts] = useState([])

  useEffect(() => {
    fetchCategories()
    fetchStats()
  }, [])

  const fetchCategories = async () => {
    try {
      const res = await fetch(`${API_URL}/categories`)
      const data = await res.json()
      setCategories(data.categories || [])
    } catch (err) {
      console.error('Failed to fetch categories:', err)
    }
  }

  const fetchStats = async () => {
    try {
      const res = await fetch(`${API_URL}/stats`)
      const data = await res.json()
      setStats(data)
    } catch (err) {
      console.error('Failed to fetch stats:', err)
    }
  }

  const handleSearch = async (e) => {
    e?.preventDefault()
    if (!query.trim()) return

    setLoading(true)
    setSelectedProduct(null)
    setSimilarProducts([])

    try {
      const params = new URLSearchParams({ query, top_k: 20 })
      if (budget) params.append('budget', budget)
      if (category) params.append('category', category)

      const res = await fetch(`${API_URL}/search?${params}`)
      const data = await res.json()

      setResults(data.results || [])
      setLatency(data.latency_ms)
    } catch (err) {
      console.error('Search failed:', err)
      setResults([])
    } finally {
      setLoading(false)
    }
  }

  const handleProductClick = async (product) => {
    setSelectedProduct(product)

    try {
      const res = await fetch(`${API_URL}/similar/${product.product_id}?top_k=6`)
      const data = await res.json()
      setSimilarProducts(data)
    } catch (err) {
      console.error('Failed to fetch similar:', err)
    }
  }

  return (
    <div className="app">
      {/* Header */}
      <header className="header">
        <div className="header-content">
          <div className="logo">
            <div className="logo-icon">
              <UberLogo />
            </div>
            <span>Uber Shopping</span>
          </div>

          {/* Search */}
          <form className="search-container" onSubmit={handleSearch}>
            <div className="search-input-wrapper">
              <span className="search-icon"><SearchIcon /></span>
              <input
                type="text"
                className="search-input"
                placeholder="Search for anything..."
                value={query}
                onChange={(e) => setQuery(e.target.value)}
              />
              <button type="submit" className="search-btn" disabled={loading}>
                {loading ? 'Searching' : 'Search'}
              </button>
            </div>
          </form>

          {/* Filters */}
          <div className="filters">
            <select
              className="filter-select"
              value={category}
              onChange={(e) => setCategory(e.target.value)}
            >
              <option value="">All Categories</option>
              {categories.map(cat => (
                <option key={cat} value={cat}>{cat}</option>
              ))}
            </select>
            <input
              type="number"
              className="filter-input"
              placeholder="Max price"
              value={budget}
              onChange={(e) => setBudget(e.target.value)}
            />
          </div>
        </div>
      </header>

      {/* Stats Bar */}
      {stats && (
        <div className="stats-bar">
          <div className="stat-item">
            <span>Products</span>
            <span className="stat-value">{stats.total_products.toLocaleString()}</span>
          </div>
          <div className="stat-item">
            <span>Vector Dimensions</span>
            <span className="stat-value">{stats.embedding_dimension}</span>
          </div>
          <div className="stat-item">
            <span>Categories</span>
            <span className="stat-value">{stats.categories}</span>
          </div>
        </div>
      )}

      {/* Main Content */}
      <main className="main">
        {/* Results Header */}
        {results.length > 0 && (
          <div className="results-header">
            <div className="results-count">
              <strong>{results.length}</strong> results for "<strong>{query}</strong>"
            </div>
            {latency && (
              <div className="latency">
                {latency.toFixed(0)}ms
              </div>
            )}
          </div>
        )}

        {/* Loading State */}
        {loading && (
          <div className="loading">
            <div className="loading-spinner"></div>
            <p>AI-powered ranking in progress...</p>
          </div>
        )}

        {/* Empty State */}
        {!loading && results.length === 0 && !query && (
          <div className="empty-state">
            <div className="empty-icon">
              <SearchIcon />
            </div>
            <h2 className="empty-title">Search for products</h2>
            <p>Try "wireless headphones", "laptop", or "running shoes"</p>
          </div>
        )}

        {/* Results Grid */}
        {!loading && results.length > 0 && (
          <div className="products-grid">
            {results.map((product) => (
              <div
                key={product.product_id}
                className="product-card"
                onClick={() => handleProductClick(product)}
              >
                <img
                  src={product.image_url}
                  alt={product.title}
                  className="product-image"
                  onError={(e) => { e.target.src = `https://picsum.photos/seed/${product.product_id}/400/240` }}
                />
                <div className="product-content">
                  <div className="product-header">
                    <span className="product-rank">#{product.rank}</span>
                    <span className="product-score">{(product.final_score * 100).toFixed(0)}%</span>
                  </div>

                  <h3 className="product-title">{product.title}</h3>

                  <div className="product-meta">
                    <span className="product-category">{product.category}</span>
                    <span className="product-brand">{product.brand}</span>
                  </div>

                  <div className="product-pricing">
                    <span className="product-price">${product.price.toFixed(2)}</span>
                    <span className="product-rating">
                      <StarIcon /> {product.rating}
                      <span>({product.review_count})</span>
                    </span>
                  </div>

                  {/* Highlights */}
                  {product.explanation?.highlights && product.explanation.highlights.length > 0 && (
                    <div className="highlights">
                      {product.explanation.highlights.slice(0, 3).map((h, i) => (
                        <span key={i} className="highlight">{h}</span>
                      ))}
                    </div>
                  )}

                  {/* Explanation */}
                  {product.explanation?.short && (
                    <div className="explanation">
                      {product.explanation.short}
                    </div>
                  )}
                </div>
              </div>
            ))}
          </div>
        )}

        {/* Similar Products */}
        {selectedProduct && similarProducts.length > 0 && (
          <section className="similar-section">
            <h2 className="section-title">
              Similar to {selectedProduct.title.slice(0, 35)}...
            </h2>
            <div className="similar-grid">
              {similarProducts.map((product) => (
                <div key={product.product_id} className="similar-card">
                  <h4 className="similar-title">{product.title}</h4>
                  <div className="similar-price">${product.price.toFixed(2)}</div>
                  <div className="product-rating" style={{ marginTop: '12px' }}>
                    <StarIcon /> {product.rating}
                  </div>
                </div>
              ))}
            </div>
          </section>
        )}
      </main>
    </div>
  )
}

export default App
