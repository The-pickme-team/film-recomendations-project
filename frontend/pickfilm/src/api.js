const API_BASE = ''

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

function normalizeFilm(film) {
  return {
    id: String(film.id),
    name: film.name ?? film.title ?? 'Untitled film',
    description: film.description ?? '',
    year: film.year_of_release ?? film.year ?? '',
    imagePath: film.image_path ?? film.imagePath ?? '',
    genres: Array.isArray(film.genres) ? film.genres : [],
  }
}

function extractErrorMessage(payload, fallback) {
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

  // Fallback to local demo search
  const lowerQuery = query.toLowerCase()
  return DEMO_FILMS.filter(
    (film) =>
      film.name.toLowerCase().includes(lowerQuery) ||
      film.genres.some((g) => g.toLowerCase().includes(lowerQuery)) ||
      film.description.toLowerCase().includes(lowerQuery)
  )
}


export async function recommendFilms(filmIds, limit = 12) {
  const attempts = [
    JSON.stringify(filmIds),
    JSON.stringify({ film_ids: filmIds, limit }),
  ]

  let lastError = null

  for (const body of attempts) {
    const response = await fetch(`${API_BASE}/films/recommend?limit=${limit}`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body,
    })

    const payload = await readJson(response)

    if (response.ok) {
      return Array.isArray(payload) ? payload.map(normalizeFilm) : []
    }

    lastError = new Error(extractErrorMessage(payload, 'Recommendation request failed'))
  }

  throw lastError || new Error('Recommendation request failed')
}

// Fallback demo films for when backend is empty or unavailable
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
