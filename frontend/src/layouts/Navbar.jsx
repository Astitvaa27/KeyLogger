import { useAuth } from '../context/AuthContext';

export default function Navbar({ onToggleSidebar }) {
  const { user, logout } = useAuth();
  return (
    <header className="sticky top-0 z-30 flex h-16 items-center justify-between border-b border-base-700 bg-base-900/80 px-4 backdrop-blur lg:px-6">
      <div className="flex items-center gap-3">
        <button
          className="btn-ghost lg:hidden px-2 py-1"
          onClick={onToggleSidebar}
          aria-label="Toggle navigation"
        >
          ☰
        </button>
        <div className="hidden sm:flex items-center gap-2">
          <span className="badge bg-risk-low/15 text-risk-low border border-risk-low/40">
            ● LIVE
          </span>
          <span className="text-xs text-slate-500">
            Security Operations Console
          </span>
        </div>
      </div>
      <div className="flex items-center gap-3">
        <div className="text-right hidden sm:block">
          <p className="text-sm text-slate-200 leading-tight">
            {user?.full_name || user?.username}
          </p>
          <p className="text-[11px] text-slate-500">{user?.email}</p>
        </div>
        <div className="h-9 w-9 rounded-full bg-accent/20 text-accent grid place-items-center font-semibold">
          {(user?.username || '?').slice(0, 1).toUpperCase()}
        </div>
        <button className="btn-ghost px-3 py-1.5" onClick={logout}>
          Logout
        </button>
      </div>
    </header>
  );
}
