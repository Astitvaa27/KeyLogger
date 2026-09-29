import { Link } from 'react-router-dom';

export default function NotFoundPage() {
  return (
    <div className="min-h-screen grid place-items-center bg-base-950 px-4 text-center">
      <div>
        <p className="text-6xl font-bold text-accent">404</p>
        <p className="mt-2 text-slate-300">This page could not be found.</p>
        <Link to="/dashboard" className="btn-primary mt-6 inline-flex">
          Back to dashboard
        </Link>
      </div>
    </div>
  );
}
