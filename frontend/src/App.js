import React, { useState, useEffect } from 'react';
import axios from 'axios';
import './App.css';

const API_URL = process.env.REACT_APP_API_URL || 'http://localhost:5000';

function App() {
  const [email, setEmail] = useState('demo@example.com');
  const [password, setPassword] = useState('password123');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const [apiStatus, setApiStatus] = useState('checking');

  useEffect(() => {
    axios.get(`${API_URL}/favicon.ico`)
      .then(() => setApiStatus('online'))
      .catch(() => setApiStatus('offline'));
  }, []);

  const handleLogin = (e) => {
    e.preventDefault();
    setError('');
    setLoading(true);

    const formData = new URLSearchParams();
    formData.append('email', email);
    formData.append('password', password);

    fetch(`${API_URL}/login`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
      body: formData,
      credentials: 'include',
    })
      .then((res) => {
        if (res.redirected || res.status === 302 || res.status === 200) {
          window.location.href = `${API_URL}/dashboard`;
        } else {
          setError('Login failed. Try the full app below.');
          setLoading(false);
        }
      })
      .catch(() => {
        setError('Cannot reach backend. It may be starting up.');
        setLoading(false);
      });
  };

  return (
    <div className="App">
      <header className="app-header">
        <h1>🌱 Plant AI Health Monitor</h1>
        <div className="status-badge">
          <span className={`dot ${apiStatus}`}></span>
          {apiStatus === 'online' ? 'Backend Online' :
           apiStatus === 'offline' ? 'Backend Starting...' : 'Checking...'}
        </div>
      </header>

      <div className="login-container">
        <div className="login-card">
          <div className="logo">🌿</div>
          <h2>Welcome Back</h2>
          <p className="subtitle">AI-powered plant disease detection</p>

          {error && <p className="error">{error}</p>}

          <form onSubmit={handleLogin}>
            <input
              type="email"
              placeholder="Email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              required
            />
            <input
              type="password"
              placeholder="Password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              required
            />
            <button type="submit" disabled={loading}>
              {loading ? 'Logging in...' : 'Login'}
            </button>
          </form>

          <div className="divider">OR</div>

          <a href={`${API_URL}/login/google`} className="google-btn">
            🔐 Sign in with Google
          </a>

          <a href={API_URL} className="full-app-link" target="_blank" rel="noreferrer">
            Open Full Application →
          </a>

          <p className="hint">Demo: demo@example.com / password123</p>
        </div>
      </div>

      <footer className="app-footer">
        <p>
          🌱 Plant AI Health Monitor | AI Agriculture Disease Detection System{' '}
          <a href={API_URL} target="_blank" rel="noreferrer">
            Launch Full App →
          </a>
        </p>
      </footer>
    </div>
  );
}

export default App;