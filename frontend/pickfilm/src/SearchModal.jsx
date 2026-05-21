import { useState, useEffect, useRef } from 'react'
import './App.css'

const API_BASE = import.meta.env.VITE_API_BASE || 'http://localhost:8000'

function SearchModal({ onClose, onSelect }) {
  const [query, setQuery] = useState('')
  const [loading, setLoading] = useState(false)
  const [result, setResult] = useState(null)
  const [error, setError] = useState(null)
  const timerRef = useRef(null)
  const abortRef = useRef(null)

  useEffect(() => {
    if (timerRef.current) clearTimeout(timerRef.current)
    if (!query || query.length < 2) {
      setResult(null)
      setError(null)
      setLoading(false)
      return
    }

    setLoading(true)
    setError(null)

    timerRef.current = setTimeout(() => {
      if (abortRef.current) abortRef.current.abort()
      abortRef.current = new AbortController()
      fetch(`${API_BASE}/films/${encodeURIComponent(query)}`, {
        signal: abortRef.current.signal,
      })
        .then(async (res) => {
          if (!res.ok) {
            const txt = await res.text()
            throw new Error(txt || res.statusText)
          }
          return res.json()
        })
        .then((data) => {
          setResult(data)
        })
        .catch((err) => {
          if (err.name === 'AbortError') return
          setError(err.message || 'Error')
          setResult(null)
        })
        .finally(() => setLoading(false))
    }, 500)

    return () => {
      if (timerRef.current) clearTimeout(timerRef.current)
      if (abortRef.current) abortRef.current.abort()
    }
  }, [query])

  return (
    <div className="search-modal-overlay" onClick={onClose}>
      <div className="search-modal" onClick={(e) => e.stopPropagation()}>
        <div className="search-modal__header">
          <h3 className="search-modal__title">Search films</h3>
          <button className="search-modal__close" onClick={onClose}>✕</button>
        </div>

        <div className="search-modal__content">
          <div className="search-input-wrapper">
            <input
              autoFocus
              className="search-input"
              placeholder="Type to search (min 2 chars)..."
              value={query}
              onChange={(e) => setQuery(e.target.value)}
            />
            {loading && <div className="search-spinner">⏳</div>}
          </div>

          {error && <div className="search-error">{error}</div>}

          <div className="search-results">
            {loading && <div className="search-loading">Searching...</div>}
            {!loading && result && (
              <div className="results-list">
                <div
                  role="button"
                  tabIndex={0}
                  className="result-item"
                  onClick={() => onSelect(result.name)}
                >
                  <div className="result-item__info">
                    <div className="result-item__title">{result.name}</div>
                    <div className="result-item__meta">{result.year_of_release?.slice(0,4) || ''}</div>
                  </div>
                  <div className="result-item__action">+</div>
                </div>
              </div>
            )}

            {!loading && !result && !error && query && query.length >= 2 && (
              <div className="no-results">
                <p>No film found</p>
                <p className="no-results__hint">Try a different title or check backend connection.</p>
              </div>
            )}
          </div>
        </div>

        <div className="search-modal__footer">
          <button className="btn-secondary" onClick={onClose}>Close</button>
        </div>
      </div>
    </div>
  )
}

export default SearchModal
