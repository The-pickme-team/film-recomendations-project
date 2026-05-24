import { useRef } from 'react'
import { formatFilmYear, DEMO_FILMS, normalizeFilm } from './api'
import './PopularPage.css'

// Temporary films for the "popular right now" section
const POPULAR_NOW = [
  {id: 1, title: 'Dune: Part Two', year: 2024, rating: '9.1', genre: 'Sci-Fi'},
  {id: 2, title: 'Oppenheimer', year: 2023, rating: '8.9', genre: 'Drama'},
  {id: 3, title: 'Poor Things', year: 2023, rating: '8.3', genre: 'Drama'},
  {id: 4, title: 'Deadpool & Wolverine', year: 2024, rating: '8.7', genre: 'Action'},
  {id: 5, title: 'Alien: Romulus', year: 2024, rating: '7.8', genre: 'Horror'},
  {id: 6, title: 'Inside Out 2', year: 2024, rating: '7.9', genre: 'Comedy'},
  {id: 7, title: 'Civil War',  year: 2024, rating: '7.4', genre: 'Action'},
  {id: 8, title: 'The Substance', year: 2024, rating: '7.6', genre: 'Horror'},
]

// Temporary films for the "personal recommendations" section
const RECOMMENDED = [
  {id: 9,  title: 'A Quiet Place: Day One', year: 2024, rating: '7.2', genre: 'Horror'},
  {id: 10, title: 'Furiosa', year: 2024, rating: '7.8', genre: 'Action'},
  {id: 11, title: 'Challengers', year: 2024, rating: '7.5', genre: 'Drama'},
  {id: 12, title: 'Hit Man', year: 2024, rating: '7.4', genre: 'Comedy'},
  {id: 13, title: 'Longlegs', year: 2024, rating: '6.8', genre: 'Horror'},
  {id: 14, title: 'Twisters', year: 2024, rating: '7.2', genre: 'Action'},
  {id: 15, title: 'Monkey Man', year: 2024, rating: '7.0', genre: 'Action'},
  {id: 16, title: 'I Saw the TV Glow', year: 2024, rating: '6.9', genre: 'Drama'},
]

function getFilmTitle(movie) {
  return movie.title ?? movie.name ?? 'Untitled film'
}

function getFilmMeta(movie) {
  const year = formatFilmYear(movie.year ?? movie.year_of_release ?? '')
  const genre = movie.genre ?? (Array.isArray(movie.genres) ? movie.genres.join(', ') : '')
  const rating = movie.rating ?? ''

  return { year, genre, rating }
}

function PopularPage({ profileFilms, recommendedFilms, onAddToProfile }) {
  const scrollRef = useRef(null)
  const getScrollStep = () => {
    const track = scrollRef.current
    if (!track) {
      return null
    }
    const card = track.querySelector('.pop-card')
    if (!(card instanceof HTMLElement)) {
      return null
    }
    const styles = window.getComputedStyle(track)
    const gap = Number.parseFloat(styles.columnGap || styles.gap || '0')
    if (Number.isNaN(gap)) {
      return card.offsetWidth
    }
    return card.offsetWidth + gap
  }

  const scrollLeft = () => {
    const step = getScrollStep()
    if (step === null) {
      return
    }
    scrollRef.current.scrollBy({ left: -step, behavior: 'smooth' })
  }

  const scrollRight = () => {
    const step = getScrollStep()
    if (step === null) {
      return
    }
    scrollRef.current.scrollBy({ left: step, behavior: 'smooth' })
  }

  return (
    <div className="popular-page">

      <section className="pop-section">
        <h2 className="pop-section__title">🔥 Popular right now!</h2>
        <p className="pop-section__sub">If you want to see pictures here, buy a pro+ subscription. ↴</p>

        <div className="slider-wrap">
          <button type="button" className="slider-arrow left" onClick={scrollLeft}>
            ‹
          </button>

          <div className="slider-track" ref={scrollRef}>
            {POPULAR_NOW.map(movie => (
              <div key={movie.id} className="pop-card pop-card--small">
                <div className="pop-card__poster" style={{background: `linear-gradient(135deg, hsl(${movie.id * 45}, 70%, 50%), hsl(${movie.id * 45 + 60}, 70%, 60%))`}} />
                <div className="pop-card__info">
                  <strong className="pop-card__title">{movie.title}</strong>
                  <div className="pop-card__meta">
                    <span>{movie.year} · {movie.genre}</span>
                    <span className="pop-card__rating">★ {movie.rating}</span>
                  </div>
                  <button type="button" className="pop-card__btn" onClick={() => onAddToProfile(movie)}>+ Add to profile</button>
                </div>
              </div>
            ))}
          </div>

          <button type="button" className="slider-arrow right" onClick={scrollRight}>
            ›
          </button>
        </div>
      </section>

      <div className="pop-divider" />

      <section className="pop-section">
        <h2 className="pop-section__title">🎯 Recommendations based on your added movies</h2>
        <p className="pop-section__sub">If you want to see pictures here, buy a pro+ subscription ❤︎⁠</p>
        <div className="popular-context">
          <span>{profileFilms.length ? `${profileFilms.length} films in your profile` : 'No films added yet'}</span>
        </div>

        <div className="pop-grid--large">
          {(recommendedFilms.length ? recommendedFilms : DEMO_FILMS.map(normalizeFilm).slice(0, 8)).map(movie => {
            const meta = getFilmMeta(movie)

            return (
              <div key={movie.id} className="pop-card pop-card--large">
                <div className="pop-card__poster" style={{background: movie.imagePath ? `url(${movie.imagePath}) center/cover` : `linear-gradient(135deg, hsl(${(movie.id ?? movie.rating ?? 1) * 45}, 70%, 50%), hsl(${(movie.id ?? movie.rating ?? 1) * 45 + 60}, 70%, 60%))`}}>
                  {movie.imagePath && <img src={movie.imagePath} alt={getFilmTitle(movie)} style={{width: '100%', height: '100%', objectFit: 'cover'}} />}
                </div>
                <div className="pop-card__info">
                  <strong className="pop-card__title">{getFilmTitle(movie)}</strong>
                  <div className="pop-card__meta">
                    <span>{meta.year || 'Unknown year'}{meta.genre ? ` · ${meta.genre}` : ''}</span>
                    <span className="pop-card__rating">{meta.rating ? `★ ${meta.rating}` : '★ —'}</span>
                  </div>
                  <button type="button" className="pop-card__btn" onClick={() => onAddToProfile(movie)}>+ Add to profile</button>
                </div>
              </div>
          )})}
        </div>
      </section>

    </div>
  )
}

export default PopularPage
