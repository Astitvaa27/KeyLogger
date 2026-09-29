import { formatDateTime } from '../utils/format';
import { Badge } from './ui/Badge';

// Compact control for choosing / starting the working session, reused by the
// Lab, Simulation, and Detection pages.
export default function SessionPicker({
  sessions,
  activeId,
  onSelect,
  onStart,
  onStop,
  busy,
}) {
  const active = sessions.find((s) => s.id === activeId);
  return (
    <div className="card">
      <div className="flex flex-col gap-3 sm:flex-row sm:items-end sm:justify-between">
        <div className="flex-1">
          <label className="label">Working session</label>
          <select
            className="input"
            value={activeId || ''}
            onChange={(e) => onSelect(Number(e.target.value) || null)}
          >
            <option value="">— select a session —</option>
            {sessions.map((s) => (
              <option key={s.id} value={s.id}>
                #{s.id} · {s.label || 'session'} · {s.status} ·{' '}
                {formatDateTime(s.started_at)}
              </option>
            ))}
          </select>
        </div>
        <div className="flex items-center gap-2">
          {active && (
            <Badge tone={active.status === 'ACTIVE' ? 'success' : 'neutral'}>
              {active.status}
            </Badge>
          )}
          <button className="btn-primary" onClick={() => onStart()} disabled={busy}>
            + New session
          </button>
          {active?.status === 'ACTIVE' && onStop && (
            <button className="btn-ghost" onClick={() => onStop(active.id)} disabled={busy}>
              Stop
            </button>
          )}
        </div>
      </div>
    </div>
  );
}
