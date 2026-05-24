import { useEffect, useMemo, useRef, useState } from 'react'
import './App.css'
import LoginPage from './LoginPage'
import PopularPage from './PopularPage'
import Profile from './Profile'
import {
  DEMO_FILMS,
  normalizeFilm,
  recommendFilms,
  searchFilms,
} from './api'

const initialFilms = Array.from({ length: 5 }, () => null)

function makeManualFilm(title, index) {
  return normalizeFilm({
    id: `${index}-${Date.now()}`,
    name: title,
    description: 'Added manually',
    year_of_release: '',
    image_path: '',
    genres: [],
  })
}

function App() {
  const [films, setFilms] = useState(initialFilms)
  const [showRecommendations, setShowRecommendations] = useState(false)
  const [currentPage, setCurrentPage] = useState('home')
  const [profileFilms, setProfileFilms] = useState([])
  const [recommendedFilms, setRecommendedFilms] = useState([])
  const [statusMessage, setStatusMessage] = useState('')
  const [filmModalOpen, setFilmModalOpen] = useState(false)
  const [filmModalIndex, setFilmModalIndex] = useState(null)
  const [filmModalQuery, setFilmModalQuery] = useState('')
  const [filmModalResults, setFilmModalResults] = useState([])
  const [filmModalLoading, setFilmModalLoading] = useState(false)
  const [filmModalError, setFilmModalError] = useState('')
  const statusTimerRef = useRef(null)
  const filmModalTimerRef = useRef(null)



  const profileFilmIds = useMemo(
    () => new Set(profileFilms.map((film) => String(film.id))),
    [profileFilms]
  )

  const isFilmInProfile = (filmId) => profileFilmIds.has(String(filmId))

  const upsertStatus = (message) => {
    setStatusMessage(message)
    if (statusTimerRef.current) {
      window.clearTimeout(statusTimerRef.current)
    }
    statusTimerRef.current = window.setTimeout(() => {
      setStatusMessage('')
    }, 2600)
  }

  useEffect(() => () => {
    if (statusTimerRef.current) {
      window.clearTimeout(statusTimerRef.current)
    }
  }, [])

  const handleAddFilm = async (index) => {
    // Open the film search modal for a nicer search experience
    setFilmModalIndex(index)
    setFilmModalQuery(films[index]?.name || '')
    setFilmModalResults([])
    setFilmModalError('')
    setFilmModalOpen(true)
  }

  const handleResetFilm = (index) => {
    const updated = [...films]
    updated[index] = null
    setFilms(updated)
  }

  const handleResetAll = () => {
    setFilms(initialFilms)
    setShowRecommendations(false)
    setRecommendedFilms([])
    setStatusMessage('')
  }

  // Film modal: perform search when query changes (debounced)
  useEffect(() => {
    if (!filmModalOpen) return undefined

    if (!filmModalQuery) {
      setFilmModalResults([])
      setFilmModalError('')
      return undefined
    }

    setFilmModalLoading(true)
    setFilmModalError('')

    if (filmModalTimerRef.current) {
      clearTimeout(filmModalTimerRef.current)
    }

    filmModalTimerRef.current = setTimeout(() => {
      searchFilms(filmModalQuery)
        .then((res) => {
          setFilmModalResults(res)
        })
        .catch((err) => {
          setFilmModalError(err.message || 'Search failed')
        })
        .finally(() => setFilmModalLoading(false))
    }, 280)

    return () => {
      if (filmModalTimerRef.current) clearTimeout(filmModalTimerRef.current)
    }
  }, [filmModalQuery, filmModalOpen])

  const closeFilmModal = () => {
    setFilmModalOpen(false)
    setFilmModalIndex(null)
    setFilmModalQuery('')
    setFilmModalResults([])
    setFilmModalError('')
  }

  const selectFilmFromModal = (film) => {
    const updated = [...films]
    updated[filmModalIndex] = normalizeFilm(film)
    setFilms(updated)
    upsertStatus(`Selected: ${film.name}`)
    closeFilmModal()
  }

  const handleGenerate = async () => {
    const selectedFilms = profileFilms.filter(Boolean)
    const filmIds = selectedFilms.map((film) => film.id)

    setShowRecommendations(true)

    if (!filmIds.length) {
      setRecommendedFilms([])
      upsertStatus('Add at least one film to profile first')
      setCurrentPage('home')
      return
    }

    try {
      const generated = await recommendFilms(filmIds, 12)
      setRecommendedFilms(generated)
      upsertStatus('Recommendations updated')
    } catch (error) {
      console.error('Generate recommendations failed:', error)
      setRecommendedFilms(DEMO_FILMS.map(normalizeFilm).slice(0, 3))
      upsertStatus(`Failed to fetch recommendations: ${error.message}`)
    }
    setCurrentPage('home')
  }

  const handleAddToProfile = (movie) => {
    const selected = normalizeFilm(movie)
    let notification = `${selected.name} added to profile`

    setProfileFilms((current) => {
      const exists = current.some((film) => String(film.id) === selected.id)
      if (exists) {
        notification = `${selected.name} is already in profile`
        return current
      }

      return [...current, selected]
    })

    upsertStatus(notification)
  }

  return (
    <div className="page-shell">
      <header className="topbar">
        <div className="brand" onClick={() => setCurrentPage('home')} style={{ cursor: 'pointer' }}>Pickfilm</div>
        <nav className="navigation">
          <button type="button" className={`nav-btn ${currentPage === 'home' ? 'nav-btn--active' : ''}`} onClick={() => setCurrentPage('home')}>Search</button>
          <span className="divider">|</span>
          <button type="button" className={`nav-btn ${currentPage === 'profile' ? 'nav-btn--active' : ''}`} onClick={() => setCurrentPage('profile')}>Profile</button>
          <span className="divider">|</span>
          <button type="button" className={`nav-btn ${currentPage === 'popular' ? 'nav-btn--active' : ''}`} onClick={() => setCurrentPage('popular')}>Popular</button>
          <span className="divider">|</span>
          <button type="button" className={`nav-btn ${currentPage === 'login' ? 'nav-btn--active' : ''}`} onClick={() => setCurrentPage('login')}>Log in</button>
        </nav>
      </header>

      {statusMessage && (
        <div className="status-toast" role="status" aria-live="polite">
          {statusMessage}
        </div>
      )}

      <main className="main-content">
        {currentPage === 'login' && <LoginPage />}
        {currentPage === 'popular' && (
          <PopularPage
            profileFilms={profileFilms}
            recommendedFilms={recommendedFilms}
            onAddToProfile={handleAddToProfile}
            isFilmInProfile={isFilmInProfile}
          />
        )}
        {currentPage === 'profile' && (
          <Profile
            films={profileFilms}
            onSearch={() => setCurrentPage('home')}
            onRemoveFilm={(filmId) => {
              setProfileFilms((current) => current.filter((film) => String(film.id) !== String(filmId)))
              upsertStatus('Film removed from profile')
            }}
          />
        )}
        {currentPage === 'home' && (
          <>
            <section className="hero-section">
              <p className="eyebrow">Find your next favorite film</p>
              <h1>Enter films you love</h1>
            </section>

            {filmModalOpen && (
              <div className="film-modal__overlay" role="presentation" onClick={closeFilmModal}>
                <div className="film-modal" role="dialog" aria-modal="true" onClick={(e) => e.stopPropagation()}>
                  <div className="film-modal__header">
                    <div>
                      <p className="film-modal__eyebrow">Search films</p>
                      <h3>Select a film</h3>
                    </div>
                    <button type="button" className="film-modal__close" onClick={closeFilmModal}>×</button>
                  </div>

                  <div className="film-modal__search">
                    <span>Type a film title</span>
                    <input
                      value={filmModalQuery}
                      onChange={(e) => setFilmModalQuery(e.target.value)}
                      placeholder="Search movies..."
                    />
                    <p className="film-modal__hint">Press enter or pick a result below</p>
                  </div>

                  <div className="film-modal__state">
                    {filmModalLoading && <div>Searching…</div>}
                    {filmModalError && <div className="film-modal__state--error">{filmModalError}</div>}
                  </div>

                  <div className="film-modal__results">
                    {filmModalResults.map((r) => (
                      <button key={r.id} type="button" className="film-result" onClick={() => selectFilmFromModal(r)}>
                        <div className="film-result__poster" style={r.imagePath ? { backgroundImage: `url(${r.imagePath})`, backgroundSize: 'cover' } : undefined}>
                          {!r.imagePath && <div style={{padding:12}}>{r.name}</div>}
                        </div>
                        <div className="film-result__body">
                          <strong>{r.name}</strong>
                          <span>{r.genres?.join(', ') || ''}</span>
                          <p>{r.description}</p>
                        </div>
                      </button>
                    ))}
                  </div>
                </div>
              </div>
            )}

            <section className="picker-section">
              <div className="picker-grid">
                {films.map((film, index) => (
                  <div key={index} className="picker-card">
                    <button
                      type="button"
                      className={`picker-button ${film ? 'picker-button--selected' : ''}`}
                      style={film?.imagePath ? { backgroundImage: `url(${film.imagePath})` } : undefined}
                      onClick={() => handleAddFilm(index)}
                    >
                      {film ? (
                        <div className="picker-poster picker-poster--fallback">
                          {!film.imagePath && <span>{film.name}</span>}
                        </div>
                      ) : (
                        <span className="plus">+</span>
                      )}
                    </button>
                    <div className={`picker-value ${film ? 'picker-value--selected' : ''}`}>
                      {film ? film.name : 'Add film'}
                    </div>
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
                  {(recommendedFilms.length ? recommendedFilms : DEMO_FILMS.slice(0, 3).map(normalizeFilm)).map((item) => {
                    const inProfile = isFilmInProfile(item.id)

                    return (
                      <div key={item.id} className="recommendation-card">
                        <div className="recommendation-cover">
                          {item.imagePath ? (
                            <img
                              src={item.imagePath}
                              alt={item.name}
                              style={{ width: '100%', height: '100%', objectFit: 'cover', display: 'block' }}
                            />
                          ) : (
                            <span>{item.name}</span>
                          )}
                        </div>
                        <button
                          type="button"
                          className={`add-profile-button ${inProfile ? 'add-profile-button--added' : ''}`}
                          onClick={() => handleAddToProfile(item)}
                          disabled={inProfile}
                        >
                          {inProfile ? 'Added to profile ✓' : 'Add to profile'}
                        </button>
                      </div>
                    )
                  })}
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
