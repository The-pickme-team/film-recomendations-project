// Profile.jsx - Profile page component with inline styles

// Movie data
const movies = [
  {
    description: 'Dominant features: cinematography and visual effects. A stunning visual spectacle with groundbreaking technology and immersive cinematography.',
    genre: 'Cinematography',
    year: 2024,
  },
  {
    description: 'Dominant features: cinematography and visual effects',
    genre: 'Science Fiction',
    year: 2023,
  },
  {
    description: 'Dominant features: cinematography and visual effects',
    genre: 'Drama',
    year: 2024,
  },
]

function Profile({ onSearch }) {
  // Page container styles
  const pageStyle = {
    minHeight: '100vh',
    backgroundColor: '#120112',
    padding: '24px',
    fontFamily: "'Segoe UI', system-ui, sans-serif",
    color: '#f8d2ff',
  }

  // Main content styles
  const mainContentStyle = {
    maxWidth: '1120px',
    margin: '0 auto',
  }

  // "Added films" title styles
  const titleStyle = {
    fontSize: '2.5rem',
    color: '#ffffff',
    fontFamily: 'Georgia, serif',
    marginBottom: '8px',
    fontWeight: '400',
    letterSpacing: '-0.02em',
  }

  // Subtitle styles
  const subtitleStyle = {
    fontSize: '0.95rem',
    color: 'rgba(248, 210, 255, 0.55)',
    marginBottom: '32px',
    lineHeight: '1.6',
  }

  // Movie cards container styles
  const moviesContainerStyle = {
    display: 'flex',
    flexDirection: 'column',
    gap: '24px',
  }

  // Movie card styles
  const movieCardStyle = {
    display: 'flex',
    gap: '24px',
    alignItems: 'flex-start',
    padding: '24px',
    borderRadius: '16px',
    backgroundColor: 'rgba(255, 255, 255, 0.02)',
  }

  // Movie poster placeholder styles
  const posterStyle = {
    width: '120px',
    height: '160px',
    minWidth: '120px',
    backgroundColor: '#9b7ba6',
    borderRadius: '20px',
    flexShrink: 0,
  }

  // Movie info block styles
  const infoStyle = {
    flex: 1,
    display: 'flex',
    flexDirection: 'column',
    gap: '12px',
  }

  // Label styles (Description, Genre, Year)
  const labelStyle = {
    fontSize: '0.9rem',
    color: '#e0b0ff',
    fontWeight: '600',
    letterSpacing: '0.05em',
    margin: '0 0 4px 0',
  }

  // Text styles under labels
  const textStyle = {
    fontSize: '0.95rem',
    color: 'rgba(248, 210, 255, 0.65)',
    margin: '0',
    lineHeight: '1.5',
  }

  return (
    <div style={pageStyle}>
      <main style={mainContentStyle}>
        <h1 style={titleStyle}>Added films</h1>
        <p style={subtitleStyle}>The films you add influence your Popular for you page</p>

        <div style={moviesContainerStyle}>
          {movies.map((movie, index) => (
            <div key={index} style={movieCardStyle}>
              <div style={posterStyle} />

              <div style={infoStyle}>
                <div>
                  <p style={labelStyle}>Description</p>
                  <p style={textStyle}>{movie.description}</p>
                </div>

                <div>
                  <p style={labelStyle}>Genre</p>
                  <p style={textStyle}>{movie.genre}</p>
                </div>

                <div>
                  <p style={labelStyle}>Release year</p>
                  <p style={textStyle}>{movie.year}</p>
                </div>
              </div>
            </div>
          ))}
        </div>
      </main>
    </div>
  )
}

export default Profile
