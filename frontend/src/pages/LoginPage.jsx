import { useState } from 'react';
import { Link, Navigate, useLocation, useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { Spinner } from '../components/ui/States';

export default function LoginPage() {
  const { login, isAuthenticated } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();
  const [form, setForm] = useState({ identifier: '', password: '' });
  const [error, setError] = useState(null);
  const [submitting, setSubmitting] = useState(false);

  if (isAuthenticated) {
    const dest = location.state?.from?.pathname || '/dashboard';
    return <Navigate to={dest} replace />;
  }

  async function onSubmit(e) {
    e.preventDefault();
    setError(null);
    setSubmitting(true);
    try {
      await login(form.identifier, form.password);
      navigate(location.state?.from?.pathname || '/dashboard', { replace: true });
    } catch (err) {
      setError(err?.response?.data?.detail || 'Login failed. Check your credentials.');
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <AuthShell subtitle="Sign in to the Security Operations Console">
      <form onSubmit={onSubmit} className="space-y-4">
        <div>
          <label className="label">Username or Email</label>
          <input
            className="input"
            autoComplete="username"
            value={form.identifier}
            onChange={(e) => setForm({ ...form, identifier: e.target.value })}
            required
          />
        </div>
        <div>
          <label className="label">Password</label>
          <input
            className="input"
            type="password"
            autoComplete="current-password"
            value={form.password}
            onChange={(e) => setForm({ ...form, password: e.target.value })}
            required
          />
        </div>
        {error && <p className="text-sm text-risk-critical">{error}</p>}
        <button className="btn-primary w-full" disabled={submitting}>
          {submitting ? <Spinner /> : 'Sign in'}
        </button>
      </form>
      <p className="mt-6 text-center text-sm text-slate-400">
        No account?{' '}
        <Link to="/register" className="text-accent hover:underline">
          Register
        </Link>
      </p>
    </AuthShell>
  );
}

export function AuthShell({ subtitle, children }) {
  return (
    <div className="min-h-screen grid place-items-center bg-base-950 px-4">
      <div className="w-full max-w-md">
        <div className="mb-6 text-center">
          <div className="text-4xl">🔐</div>
          <h1 className="mt-2 text-2xl font-bold text-slate-100">KeyLogger</h1>
          <p className="text-sm text-slate-400">{subtitle}</p>
        </div>
        <div className="card">{children}</div>
        <p className="mt-4 text-center text-[11px] text-slate-600">
          Educational defensive platform — no real keylogging capability.
        </p>
      </div>
    </div>
  );
}
