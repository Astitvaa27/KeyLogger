import { NavLink } from 'react-router-dom';

const NAV = [
  { to: '/dashboard', label: 'SOC Dashboard', icon: '📊' },
  { to: '/keylogger-lab', label: 'Keylogger Lab', icon: '⌨️' },
  { to: '/analytics', label: 'Analytics', icon: '📈' },
  { to: '/threat-simulation', label: 'Threat Simulation', icon: '🧪' },
  { to: '/detection', label: 'Detection & Risk', icon: '🛡️' },
  { to: '/events', label: 'Events', icon: '🗂️' },
  { to: '/settings', label: 'Settings', icon: '⚙️' },
];

export default function Sidebar({ open, onNavigate }) {
  return (
    <aside
      className={`fixed inset-y-0 left-0 z-40 w-64 transform bg-base-900 border-r border-base-700
        transition-transform duration-200 lg:translate-x-0 ${
          open ? 'translate-x-0' : '-translate-x-full'
        }`}
    >
      <div className="flex h-16 items-center gap-2 px-5 border-b border-base-700">
        <span className="text-xl">🔐</span>
        <div>
          <p className="text-sm font-bold text-slate-100 leading-tight">KeyLogger</p>
          <p className="text-[10px] uppercase tracking-widest text-accent">SOC Platform</p>
        </div>
      </div>
      <nav className="p-3 space-y-1">
        {NAV.map((item) => (
          <NavLink
            key={item.to}
            to={item.to}
            onClick={onNavigate}
            className={({ isActive }) =>
              `flex items-center gap-3 rounded-lg px-3 py-2 text-sm transition-colors ${
                isActive
                  ? 'bg-accent/15 text-accent font-medium'
                  : 'text-slate-300 hover:bg-base-800'
              }`
            }
          >
            <span className="text-base">{item.icon}</span>
            {item.label}
          </NavLink>
        ))}
      </nav>
      <div className="absolute bottom-0 w-full p-4 border-t border-base-700">
        <p className="text-[10px] leading-relaxed text-slate-500">
          Educational defensive platform. No real keylogging — in-app test capture only.
        </p>
      </div>
    </aside>
  );
}
