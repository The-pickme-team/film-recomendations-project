import { useEffect, useMemo, useState } from 'react'
import './App.css'
import LoginPage from './LoginPage'
import PopularPage from './PopularPage'
import Profile from './Profile'
import { formatFilmYear, recommendFilms, searchFilms } from './api'

const initialFilms = Array.from({ length: 5 }, () => null)

const localStorageKeys = {
  profileFilms: 'pickfilm.profileFilms',
  recommendedFilms: 'pickfilm.recommendedFilms',
}

function loadStoredFilms(key) {
  if (typeof window === 'undefined') {
    return []
  }

  try {
    const raw = window.localStorage.getItem(key)
    const parsed = raw ? JSON.parse(raw) : []
    return Array.isArray(parsed) ? parsed : []
  } catch {
    return []
  }
}

function toProfileFilm(film) {
  const year = formatFilmYear(film.year)

  return {
    id: film.id,
    name: film.name || film.title || 'Untitled film',
    description: film.description || 'No description available',
    year,
    genres: film.genres || (film.genre ? [film.genre] : []),
    imagePath: film.imagePath || '',
  }
}

function isSameFilm(left, right) {
  return String(left.id) === String(right.id)
}

function FilmSearchModal({ open, slotIndex, onClose, onSelect }) {
  const [query, setQuery] = useState('')
  const [results, setResults] = useState([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  useEffect(() => {
    if (!open) {
      setQuery('')
      setResults([])
      setLoading(false)
      setError('')
      return undefined
    }

    const trimmed = query.trim()
    if (trimmed.length < 2) {
      setResults([])
      setError('')
      return undefined
    }

    setLoading(true)
    setError('')

    const timeoutId = window.setTimeout(async () => {
      try {
        const found = await searchFilms(trimmed)
        setResults(found)
      } catch (searchError) {
        setResults([])
        setError(searchError instanceof Error ? searchError.message : 'Search failed')
      } finally {
        setLoading(false)
      }
    }, 450)

    return () => window.clearTimeout(timeoutId)
  }, [open, query])

  if (!open) {
    return null
  }

  return (
    <div className="film-modal__overlay" onClick={onClose}>
      <div className="film-modal" onClick={(event) => event.stopPropagation()}>
        <div className="film-modal__header">
          <div>
            <p className="film-modal__eyebrow">Pick a film</p>
            <h3>Select film #{slotIndex + 1}</h3>
          </div>
          <button type="button" className="film-modal__close" onClick={onClose}>×</button>
        </div>

        <label className="film-modal__search">
          <span>Type a film name</span>
          <input
            autoFocus
            value={query}
            onChange={(event) => setQuery(event.target.value)}
            placeholder="Search films..."
          />
        </label>

        <p className="film-modal__hint">
          The search runs after you pause typing for a moment.
        </p>

        {loading && <div className="film-modal__state">Searching...</div>}
        {!loading && error && <div className="film-modal__state film-modal__state--error">{error}</div>}
        {!loading && !error && query.trim().length >= 2 && results.length === 0 && (
          <div className="film-modal__state">No films found. Try another title.</div>
        )}

        <div className="film-modal__results">
          {results.map((film) => (
            <button
              type="button"
              key={film.id}
              className="film-result"
              onClick={() => onSelect(film)}
            >
              <div className="film-result__poster">
                {film.imagePath && <img src={film.imagePath} alt={film.name} style={{width: '100%', height: '100%', objectFit: 'cover', borderRadius: 'inherit'}} />}
              </div>
              <div className="film-result__body">
                <strong>{film.name}</strong>
                <span>
                  {formatFilmYear(film.year) || 'Unknown year'}
                  {film.genres.length ? ` · ${film.genres.join(', ')}` : ''}
                </span>
                <p>{film.description}</p>
              </div>
            </button>
          ))}
        </div>
      </div>
    </div>
  )
}

function App() {
  const [films, setFilms] = useState(initialFilms)
  const [selectedFilms, setSelectedFilms] = useState([])
  const [recommendedFilms, setRecommendedFilms] = useState(() => loadStoredFilms(localStorageKeys.recommendedFilms))
  const [profileFilms, setProfileFilms] = useState(() => loadStoredFilms(localStorageKeys.profileFilms))
  const [showRecommendations, setShowRecommendations] = useState(false)
  const [generationLoading, setGenerationLoading] = useState(false)
  const [generationError, setGenerationError] = useState('')
  const [generationSuccess, setGenerationSuccess] = useState('')
  const [activePickerIndex, setActivePickerIndex] = useState(null)
  const [currentPage, setCurrentPage] = useState('home')

  useEffect(() => {
    window.localStorage.setItem(localStorageKeys.profileFilms, JSON.stringify(profileFilms))
  }, [profileFilms])

  useEffect(() => {
    window.localStorage.setItem(localStorageKeys.recommendedFilms, JSON.stringify(recommendedFilms))
  }, [recommendedFilms])

  const selectedCount = useMemo(() => selectedFilms.filter(Boolean).length, [selectedFilms])

  const closePicker = () => setActivePickerIndex(null)

  const handleAddFilm = (index) => {
    setActivePickerIndex(index)
    setGenerationError('')
    setGenerationSuccess('')
  }

  const handleResetFilm = (index) => {
    const updated = [...films]
    updated[index] = null
    const selected = [...selectedFilms]
    selected[index] = null
    setFilms(updated)
    setSelectedFilms(selected)
  }

  const handleResetAll = () => {
    setFilms(initialFilms)
    setSelectedFilms([])
    setShowRecommendations(false)
    setRecommendedFilms([])
    setGenerationError('')
    setGenerationSuccess('')
  }

  const handlePickFilm = (film) => {
    if (activePickerIndex === null) {
      return
    }

    const nextFilms = [...films]
    const nextSelected = [...selectedFilms]
    nextFilms[activePickerIndex] = film.name
    nextSelected[activePickerIndex] = film
    setFilms(nextFilms)
    setSelectedFilms(nextSelected)
    closePicker()
  }

  const handleGenerate = async () => {
    const pickedFilms = selectedFilms.filter(Boolean)

    if (pickedFilms.length === 0) {
      setGenerationError('Add at least one film before generating recommendations.')
      return
    }

    setGenerationLoading(true)
    setGenerationError('')
    setGenerationSuccess('')

    try {
      const generated = await recommendFilms(pickedFilms.map((film) => film.id))
      setRecommendedFilms(generated)
      setShowRecommendations(true)
      setGenerationSuccess('Recommendations are ready.')
      setCurrentPage('popular')
    } catch (error) {
      const fallback = pickedFilms.map((film) => ({
        ...film,
        description: film.description || 'Added by you',
      }))
      setRecommendedFilms(fallback)
      setShowRecommendations(true)
      setGenerationError(error instanceof Error ? error.message : 'Recommendation request failed')
    } finally {
      setGenerationLoading(false)
    }
  }

  const handleAddToProfile = (film) => {
    setProfileFilms((current) => {
      if (current.some((item) => isSameFilm(item, film))) {
        return current
      }

      return [...current, toProfileFilm(film)]
    })
  }

  const handleRemoveFromProfile = (filmId) => {
    setProfileFilms((current) => current.filter((film) => String(film.id) !== String(filmId)))
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

      <main className="main-content">
        {currentPage === 'login' && <LoginPage />}
        {currentPage === 'popular' && (
          <PopularPage
            profileFilms={profileFilms}
            recommendedFilms={recommendedFilms}
            onAddToProfile={handleAddToProfile}
          />
        )}
        {currentPage === 'profile' && (
          <Profile
            films={profileFilms}
            onSearch={() => setCurrentPage('home')}
            onRemoveFilm={handleRemoveFromProfile}
          />
        )}
        {currentPage === 'home' && (
          <>
            <section className="hero-section">
              <p className="eyebrow">Find your next favorite film</p>
              <h1>Choose films you love</h1>
              <p className="hero-copy">
                Click a slot, type a title, and wait a moment — the film search appears automatically.
              </p>
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
                    <div className={`picker-value ${film ? 'picker-value--selected' : ''}`}>
                      {film || 'Add film'}
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

            <button type="button" className="generate-button" onClick={handleGenerate} disabled={generationLoading}>
              {generationLoading ? 'Generating...' : 'Generate recommendation'}
            </button>

            {generationError && <p className="status-message status-message--error">{generationError}</p>}
            {generationSuccess && <p className="status-message status-message--success">{generationSuccess}</p>}
            <p className="status-message">Selected films: {selectedCount}</p>

            {showRecommendations && (
              <section className="recommendation-section">
                <h2>Your recommendations:</h2>
                <div className="recommendation-grid">
                  {recommendedFilms.map((film) => (
                    <div key={film.id} className="recommendation-card">
                      <div className="recommendation-cover">
                        {film.imagePath && <img src={film.imagePath} alt={film.name} style={{width: '100%', height: '100%', objectFit: 'cover', borderRadius: 'inherit'}} />}
                      </div>
                      <div className="recommendation-title">{film.name}</div>
                      <p className="recommendation-meta">
                        {formatFilmYear(film.year) || 'Unknown year'}
                        {film.genres?.length ? ` · ${film.genres.join(', ')}` : ''}
                      </p>
                      <button type="button" className="add-profile-button" onClick={() => handleAddToProfile(film)}>
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

      <FilmSearchModal
        open={activePickerIndex !== null}
        slotIndex={activePickerIndex ?? 0}
        onClose={closePicker}
        onSelect={handlePickFilm}
      />

      <footer className="page-footer">
        <span>Created by:</span>
        <strong>pickme team</strong>
      </footer>
    </div>
  )
}

export default App
