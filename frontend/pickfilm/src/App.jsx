import { useState } from 'react'
import './App.css'
import LoginPage from './LoginPage'
import PopularPage from './PopularPage'

const initialFilms = Array.from({ length: 5 }, () => '')

function App() {
  const [films, setFilms] = useState(initialFilms)
  const [showRecommendations, setShowRecommendations] = useState(false)
  const [currentPage, setCurrentPage] = useState('home')

  const handleAddFilm = (index) => {
    const title = window.prompt('Enter a film you love:', films[index] || '')
    if (title === null) return
    const updated = [...films]
    updated[index] = title.trim()
    setFilms(updated)
  }

  const handleResetFilm = (index) => {
    const updated = [...films]
    updated[index] = ''
    setFilms(updated)
  }

  const handleResetAll = () => {
    setFilms(initialFilms)
    setShowRecommendations(false)
  }

  const handleGenerate = () => {
    setShowRecommendations(true)
  }

  return (
    <div className="page-shell">
      <header className="topbar">
        <div className="brand" onClick={() => setCurrentPage('home')} style={{ cursor: 'pointer' }}>Pickfilm</div>
        <nav className="navigation">
          <a href="#">Search</a>
          <span className="divider">|</span>
          <a href="#">Profile</a>
          <span className="divider">|</span>
          <button type="button" className={`nav-btn ${currentPage === 'popular' ? 'nav-btn--active' : ''}`} onClick={() => setCurrentPage('popular')}>Popular</button>
          <span className="divider">|</span>
          <button type="button" className={`nav-btn ${currentPage === 'login' ? 'nav-btn--active' : ''}`} onClick={() => setCurrentPage('login')}>Log in</button>
        </nav>
      </header>

      <main className="main-content">
        {currentPage === 'login' && <LoginPage />}
        {currentPage === 'popular' && <PopularPage />}
        {currentPage === 'home' && (
          <>
            <section className="hero-section">
              <p className="eyebrow">Find your next favorite film</p>
              <h1>Enter films you love</h1>
            </section>

            <section className="picker-section">
              <div className="picker-grid">
                {films.map((film, index) => (
                  <div key={index} className="picker-card">
                    <button
                      type="button"
                      className="picker-button"
                      onClick={() => handleAddFilm(index)}
                    >
                      <span className="plus">+</span>
                    </button>
                    <div className="picker-value">{film || 'Add film'}</div>
                    <button
                      type="button"
                      className="reset-small"
                      onClick={() => handleResetFilm(index)}
                    >
                      Reset
                    </button>
                  </div>
                ))}
              </div>
            </section>

            <button type="button" className="generate-button" onClick={handleGenerate}>
              Generate recommendation
            </button>

            {showRecommendations && (
              <section className="recommendation-section">
                <h2>Your recommendations:</h2>
                <div className="recommendation-grid">
                  {[1, 2, 3].map((item) => (
                    <div key={item} className="recommendation-card">
                      <div className="recommendation-cover" />
                      <button type="button" className="add-profile-button">
                        Add to profile
                      </button>
                    </div>
                  ))}
                </div>
                <button type="button" className="reset-all" onClick={handleResetAll}>
                  Clear
                </button>
              </section>
            )}
          </>
        )}
      </main>

      <footer className="page-footer">
        <span>Created by:</span>
        <strong>pickme team</strong>
      </footer>
    </div>
  )
}

export default App
