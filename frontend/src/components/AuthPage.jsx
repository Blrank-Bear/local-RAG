import React, { useState } from 'react'
import { api } from '../services/api'
import { useStore } from '../store/useStore'
import './AuthPage.css'

export default function AuthPage() {
  const setAuth = useStore((s) => s.setAuth)
  const [mode, setMode] = useState('login')   // 'login' | 'register'
  const [form, setForm] = useState({ username: '', email: '', password: '' })
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)

  const update = (field) => (e) => setForm((f) => ({ ...f, [field]: e.target.value }))

  const submit = async (e) => {
    e.preventDefault()
    setError('')
    setLoading(true)

    try {
      let data
      if (mode === 'register') {
        data = await api.register(form.username, form.email, form.password)
      } else {
        data = await api.login(form.username, form.password)
      }
      setAuth(data.access_token, { user_id: data.user_id, username: data.username })
    } catch (err) {
      const detail = err?.response?.data?.detail
      if (Array.isArray(detail)) {
        setError(detail.map((d) => d.msg).join(' '))
      } else {
        setError(detail || 'Something went wrong. Please try again.')
      }
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="auth-page">
      <div className="auth-card">
        {/* Brand */}
        <div className="auth-card__brand">
          <span className="auth-card__logo">⬡</span>
          <span className="auth-card__title">AgentOS</span>
        </div>

        <p className="auth-card__subtitle">
          {mode === 'login' ? 'Sign in to your account' : 'Create a new account'}
        </p>

        {/* Tab switcher */}
        <div className="auth-card__tabs">
          <button
            className={`auth-card__tab ${mode === 'login' ? 'auth-card__tab--active' : ''}`}
            onClick={() => { setMode('login'); setError('') }}
            type="button"
          >
            Sign In
          </button>
          <button
            className={`auth-card__tab ${mode === 'register' ? 'auth-card__tab--active' : ''}`}
            onClick={() => { setMode('register'); setError('') }}
            type="button"
          >
            Register
          </button>
        </div>

        <form className="auth-card__form" onSubmit={submit} noValidate>
          <div className="auth-card__field">
            <label className="auth-card__label" htmlFor="auth-username">
              {mode === 'login' ? 'Username or Email' : 'Username'}
            </label>
            <input
              id="auth-username"
              className="auth-card__input"
              type="text"
              autoComplete={mode === 'login' ? 'username' : 'username'}
              value={form.username}
              onChange={update('username')}
              placeholder={mode === 'login' ? 'username or email' : 'your_username'}
              required
              disabled={loading}
            />
          </div>

          {mode === 'register' && (
            <div className="auth-card__field">
              <label className="auth-card__label" htmlFor="auth-email">
                Email
              </label>
              <input
                id="auth-email"
                className="auth-card__input"
                type="email"
                autoComplete="email"
                value={form.email}
                onChange={update('email')}
                placeholder="you@example.com"
                required
                disabled={loading}
              />
            </div>
          )}

          <div className="auth-card__field">
            <label className="auth-card__label" htmlFor="auth-password">
              Password
            </label>
            <input
              id="auth-password"
              className="auth-card__input"
              type="password"
              autoComplete={mode === 'login' ? 'current-password' : 'new-password'}
              value={form.password}
              onChange={update('password')}
              placeholder={mode === 'register' ? 'at least 8 characters' : '••••••••'}
              required
              disabled={loading}
            />
          </div>

          {error && (
            <div className="auth-card__error" role="alert">
              {error}
            </div>
          )}

          <button
            className="auth-card__submit"
            type="submit"
            disabled={loading}
          >
            {loading
              ? <span className="auth-card__spinner" />
              : mode === 'login' ? 'Sign In' : 'Create Account'}
          </button>
        </form>

        <p className="auth-card__switch">
          {mode === 'login' ? "Don't have an account?" : 'Already have an account?'}
          {' '}
          <button
            className="auth-card__switch-btn"
            type="button"
            onClick={() => { setMode(mode === 'login' ? 'register' : 'login'); setError('') }}
          >
            {mode === 'login' ? 'Register' : 'Sign In'}
          </button>
        </p>
      </div>
    </div>
  )
}
