import { useState } from 'react';
import { Link, Navigate, useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { Spinner } from '../components/ui/States';
import { AuthShell } from './LoginPage';

export default function RegisterPage() {
  const { register, isAuthenticated } = useAuth();
  const navigate = useNavigate();
  const [form, setForm] = useState({
    full_name: '',
    username: '',
    email: '',
    password: '',
    confirm: '',
  });
  const [error, setError] = useState(null);
  const [submitting, setSubmitting] = useState(false);

  if (isAuthenticated) return <Navigate to="/dashboard" replace />;

  async function onSubmit(e) {
    e.preventDefault();
    setError(null);
    if (form.password !== form.confirm) {
      setError('Passwords do not match.');
      return;
    }
    if (form.password.length < 8) {
      setError('Password must be at least 8 characters.');
      return;
    }
    setSubmitting(true);
    try {
      await register({
        full_name: form.full_name || null,
        username: form.username,
        email: form.email,
        password: form.password,
      });
      navigate('/dashboard', { replace: true });
    } catch (err) {
      setError(err?.response?.data?.detail || 'Registration failed.');
    } finally {
      setSubmitting(false);
    }
  }

  const set = (k) => (e) => setForm({ ...form, [k]: e.target.value });

  return (
    <AuthShell subtitle="Create your analyst account">
      <form onSubmit={onSubmit} className="space-y-4">
        <div>
          <label className="label">Full name (optional)</label>
          <input className="input" value={form.full_name} onChange={set('full_name')} />
        </div>
        <div>
          <label className="label">Username</label>
          <input className="input" value={form.username} onChange={set('username')} required minLength={3} />
        </div>
        <div>
          <label className="label">Email</label>
          <input className="input" type="email" value={form.email} onChange={set('email')} required />
        </div>
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
          <div>
            <label className="label">Password</label>
            <input className="input" type="password" value={form.password} onChange={set('password')} required minLength={8} />
          </div>
          <div>
            <label className="label">Confirm</label>
            <input className="input" type="password" value={form.confirm} onChange={set('confirm')} required />
          </div>
        </div>
        {error && <p className="text-sm text-risk-critical">{error}</p>}
        <button className="btn-primary w-full" disabled={submitting}>
          {submitting ? <Spinner /> : 'Create account'}
        </button>
      </form>
      <p className="mt-6 text-center text-sm text-slate-400">
        Already registered?{' '}
        <Link to="/login" className="text-accent hover:underline">
          Sign in
        </Link>
      </p>
    </AuthShell>
  );
}
