const API_BASE = 'http://127.0.0.1/api'

async function readJson(response) {
  const text = await response.text()

  if (!text) {
    return null
  }

  try {
    return JSON.parse(text)
  } catch {
    return text
  }
}

export function normalizeFilm(film) {
  const name = film.name ?? film.title ?? 'Untitled film'
  const year = film.year_of_release ?? film.year ?? ''
  let imagePath = film.image_path ?? film.imagePath ?? ''

  if (!imagePath) {
    imagePath = createPosterDataUri(name, year)
  }

  return {
    id: String(film.id),
    name,
    description: film.description ?? '',
    year,
    imagePath,
    genres: Array.isArray(film.genres) ? film.genres : [],
  }
}

function createPosterDataUri(name, year) {
  const title = (name || 'Untitled').slice(0, 30)
  const yr = year ? String(year) : ''
  const svg = `<?xml version="1.0" encoding="UTF-8"?>
<svg xmlns='http://www.w3.org/2000/svg' width='400' height='600' viewBox='0 0 400 600'>
  <defs>
    <linearGradient id='g' x1='0' x2='0' y1='0' y2='1'>
      <stop offset='0' stop-color='#ff9de6' stop-opacity='0.92'/>
      <stop offset='1' stop-color='#6b21a8' stop-opacity='0.92'/>
    </linearGradient>
  </defs>
  <rect width='100%' height='100%' fill='url(#g)' rx='18' />
  <text x='50%' y='46%' font-family='Arial, Helvetica, sans-serif' font-size='20' fill='white' text-anchor='middle'>${escapeXml(title)}</text>
  <text x='50%' y='54%' font-family='Arial, Helvetica, sans-serif' font-size='14' fill='rgba(255,255,255,0.9)' text-anchor='middle'>${escapeXml(yr)}</text>
</svg>`

  return `data:image/svg+xml;utf8,${encodeURIComponent(svg)}`
}

function escapeXml(s) {
  return String(s).replace(/[&<>"']/g, (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]))
}

export function extractErrorMessage(payload, fallback) {
  if (typeof payload === 'string' && payload.trim()) {
    return payload
  }

  if (payload && typeof payload === 'object') {
    return payload.detail || payload.message || payload.error || fallback
  }

  return fallback
}

export function formatFilmYear(value) {
  if (value === null || value === undefined || value === '') {
    return ''
  }

  if (typeof value === 'number') {
    return String(value)
  }

  const text = String(value).trim()
  if (/^\d{4}$/.test(text)) {
    return text
  }

  const parsed = new Date(text)
  if (!Number.isNaN(parsed.getTime())) {
    return String(parsed.getFullYear())
  }

  return text
}

export async function fetchPopularFilms(limit = 15) {
  try {
    const response = await fetch(`${API_BASE}/films/popular?limit=${encodeURIComponent(limit)}`)
    const payload = await readJson(response)

    if (!response.ok) {
      throw new Error('Failed to fetch popular films')
    }

    return Array.isArray(payload) ? payload.map(normalizeFilm) : []
  } catch (error) {
    console.warn('Backend popular films fetch failed:', error)
    throw error
  }
}

export async function searchFilms(query) {
  try {
    const response = await fetch(`${API_BASE}/films/search?film_name=${encodeURIComponent(query)}`, {
      signal: AbortSignal.timeout(5000),
    })
    const payload = await readJson(response)

    if (!response.ok) {
      throw new Error(extractErrorMessage(payload, 'Search failed'))
    }

    const results = Array.isArray(payload) ? payload.map(normalizeFilm) : []
    if (results.length > 0) {
      return results
    }
  } catch (error) {
    console.warn('Backend search failed, using local demo films:', error)
  }

  const lowerQuery = query.toLowerCase()
  return DEMO_FILMS.filter(
    (film) =>
      film.name.toLowerCase().includes(lowerQuery) ||
      film.genres.some((g) => g.toLowerCase().includes(lowerQuery)) ||
      film.description.toLowerCase().includes(lowerQuery)
  )
}

export async function recommendFilms(filmIds, limit = 3) {
  if (!filmIds || filmIds.length === 0) {
    throw new Error('No film IDs provided for recommendations')
  }

  const url = `${API_BASE}/films/recommend?limit=${encodeURIComponent(limit)}`

  console.log('Recommend URL:', url)
  console.log('Film IDs:', filmIds)

  try {
    const response = await fetch(url, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(filmIds),
    })

    const payload = await readJson(response)
    console.log('Recommend response status:', response.status, 'payload:', payload)

    if (!response.ok) {
      const errorMsg = extractErrorMessage(payload, `Recommendation failed (${response.status})`)
      console.error('Backend error:', errorMsg)
      throw new Error(errorMsg)
    }

    return Array.isArray(payload) ? payload.map(normalizeFilm) : []
  } catch (error) {
    console.error('recommendFilms error:', error)
    throw error
  }
}

export const DEMO_FILMS = [
  {
    id: '1',
    name: 'The Shawshank Redemption',
    description: 'Two imprisoned men bond over a number of years, finding solace and eventual redemption through acts of common decency.',
    year_of_release: '1994',
    image_path: '',
    genres: ['Drama'],
  },
  {
    id: '2',
    name: 'The Godfather',
    description: 'The aging patriarch of an organized crime dynasty transfers control of his clandestine empire to his reluctant youngest son.',
    year_of_release: '1972',
    image_path: '',
    genres: ['Crime', 'Drama'],
  },
  {
    id: '3',
    name: 'The Dark Knight',
    description: 'Batman faces a new nemesis, the Joker, a criminal mastermind who wants to plunge Gotham into chaos.',
    year_of_release: '2008',
    image_path: '',
    genres: ['Action', 'Crime', 'Drama'],
  },
  {
    id: '4',
    name: 'Inception',
    description: 'A thief who steals corporate secrets through dream-sharing technology is given the inverse task of planting an idea.',
    year_of_release: '2010',
    image_path: '',
    genres: ['Action', 'Sci-Fi', 'Thriller'],
  },
  {
    id: '5',
    name: 'Pulp Fiction',
    description: 'The lives of four mobsters, two hit men, a gangster and his wife intertwine in four tales of violence and redemption.',
    year_of_release: '1994',
    image_path: '',
    genres: ['Crime', 'Drama'],
  },
  {
    id: '6',
    name: 'Avatar',
    description: 'A paraplegic Marine dispatched to the moon Pandora becomes torn between following his orders and protecting the world he feels is his home.',
    year_of_release: '2009',
    image_path: '',
    genres: ['Action', 'Adventure', 'Sci-Fi'],
  },
  {
    id: '7',
    name: 'Interstellar',
    description: 'A team of explorers travel through a wormhole in space in an attempt to ensure humanity\'s survival.',
    year_of_release: '2014',
    image_path: '',
    genres: ['Adventure', 'Drama', 'Sci-Fi'],
  },
  {
    id: '8',
    name: 'The Matrix',
    description: 'A computer hacker learns from mysterious rebels about the true nature of his reality and his role in the war against its controllers.',
    year_of_release: '1999',
    image_path: '',
    genres: ['Action', 'Sci-Fi'],
  },
]
