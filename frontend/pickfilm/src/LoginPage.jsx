import './LoginPage.css'

function LoginPage({ onNavigate }) {
  return (
    <div className="login-wrap">
      <div className="login-card">

        <h2 className="login-title">Welcome back!</h2>
        <p className="login-subtitle">Log in to access your film list</p>

        <div className="login-field">
          <label htmlFor="login-email">Email</label>
          <input
            id="login-email"
            type="email"
            placeholder="your@email.com"
          />
        </div>

        <div className="login-field">
          <label htmlFor="login-password">Password</label>
          <input
            id="login-password"
            type="password"
            placeholder="••••••••"
          />
          <span className="forgot-link">Forgot password?</span>
        </div>

        <button type="button" className="login-btn">
          Log in
        </button>

        <div className="login-divider">or</div>

        <p className="signup-text">
          Don't have an account?{' '}
          <span className="signup-link">Sign up</span>
        </p>

      </div>
    </div>
  )
}

export default LoginPage