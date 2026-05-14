import { useState } from 'react'
import './LoginPage.css'

function LoginPage() {
  const [isSignUp, setIsSignUp] = useState(false)

  return (
    <div className="login-wrap">
      <div className="login-card">

        {isSignUp ? (
          <>
            <h2 className="login-title">Welcome</h2>
            <p className="login-subtitle">Create your account to save your favorite films</p>

            <div className="login-field">
              <label htmlFor="signup-email">Email</label>
              <input
                id="signup-email"
                type="email"
                placeholder="your@email.com"
              />
            </div>

            <div className="login-field">
              <label htmlFor="signup-password">Password</label>
              <input
                id="signup-password"
                type="password"
                placeholder="••••••••"
              />
            </div>

            <div className="login-field">
              <label htmlFor="signup-confirm">Confirm password</label>
              <input
                id="signup-confirm"
                type="password"
                placeholder="••••••••"
              />
            </div>

            <button type="button" className="login-btn">
              Sign up
            </button>

            <div className="login-divider">or</div>

            <p className="signup-text">
              Already have an account?{' '}
              <span className="signup-link" onClick={() => setIsSignUp(false)}>Log in</span>
            </p>
          </>
        ) : (
          <>
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
              <span className="signup-link" onClick={() => setIsSignUp(true)}>Sign up</span>
            </p>
          </>
        )}

      </div>
    </div>
  )
}

export default LoginPage
