import './App.css'

function Profile({ films, onSearch, onRemoveFilm }) {
  return (
    <section className="profile-page">
      <div className="profile-header">
        <div>
          <p className="eyebrow">Your profile</p>
          <h1>Added films</h1>
          <p className="profile-copy">The films you add shape your recommendations.</p>
        </div>
        <button type="button" className="generate-button profile-search-button" onClick={onSearch}>
          Add more films
        </button>
      </div>

      {!films.length ? (
        <div className="empty-state">
          <h2>No films added yet</h2>
          <p>Choose a film on the search page and it will appear here.</p>
        </div>
      ) : (
        <div className="profile-grid">
          {films.map((film) => (
            <article key={film.id} className="profile-card">
                <div className="profile-card__poster">
                  {film.imagePath ? (
                    <img src={film.imagePath} alt={film.name} />
                  ) : (
                    <span>{film.name}</span>
                  )}
                </div>
              <div className="profile-card__body">
                <h3>{film.name}</h3>
                <p>{film.description}</p>
                <div className="profile-card__meta">
                  <span>{film.year || 'Unknown year'}</span>
                  <span>{film.genres?.length ? film.genres.join(', ') : 'No genres yet'}</span>
                </div>
                <button type="button" className="profile-card__remove" onClick={() => onRemoveFilm(film.id)}>
                  Remove from profile
                </button>
              </div>
            </article>
          ))}
        </div>
      )}
    </section>
  )
}

export default Profile
