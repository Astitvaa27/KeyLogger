import { useCallback, useEffect, useState } from 'react';
import Card from '../components/ui/Card';
import { Badge } from '../components/ui/Badge';
import { EmptyState, LoadingState } from '../components/ui/States';
import { useActiveSession } from '../hooks/useActiveSession';
import { simulationApi, detectionApi } from '../services/endpoints';
import { formatDateTime } from '../utils/format';

// Unified event log: merges synthetic telemetry + detection runs for a session.
export default function EventsPage() {
  const { sessions, activeId, selectSession, loading: sessLoading } = useActiveSession();
  const [rows, setRows] = useState([]);
  const [loading, setLoading] = useState(false);
  const [filter, setFilter] = useState('all');

  const load = useCallback(async () => {
    if (!activeId) {
      setRows([]);
      return;
    }
    setLoading(true);
    try {
      const [sim, det] = await Promise.all([
        simulationApi.events(activeId).catch(() => []),
        detectionApi.results(activeId).catch(() => []),
      ]);
      const merged = [
        ...sim.map((e) => ({
          id: `sim-${e.id}`,
          kind: 'simulation',
          time: e.created_at,
          title: `Synthetic telemetry — ${e.process_name}`,
          detail: `${e.keyboard_events} kb events · rate ${e.event_rate_per_min}/min`,
          indicators: e.risk_indicators,
        })),
        ...det.map((d) => ({
          id: `det-${d.id}`,
          kind: 'detection',
          time: d.created_at,
          title: `Detection run — score ${d.risk_score}`,
          detail: `${d.triggered_rules.length} rule(s) triggered`,
          level: d.risk_level,
        })),
      ].sort((a, b) => new Date(b.time) - new Date(a.time));
      setRows(merged);
    } finally {
      setLoading(false);
    }
  }, [activeId]);

  useEffect(() => {
    load();
  }, [load]);

  const filtered = rows.filter((r) => filter === 'all' || r.kind === filter);

  return (
    <div className="space-y-5">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <h1 className="text-xl font-bold text-slate-100">Events</h1>
          <p className="text-sm text-slate-400">Unified activity log for a session.</p>
        </div>
        <div className="flex items-center gap-2">
          <select
            className="input max-w-xs"
            value={activeId || ''}
            onChange={(e) => selectSession(Number(e.target.value) || null)}
          >
            <option value="">— select session —</option>
            {sessions.map((s) => (
              <option key={s.id} value={s.id}>
                #{s.id} · {s.label || 'session'}
              </option>
            ))}
          </select>
          <button className="btn-ghost" onClick={load} disabled={!activeId}>
            Refresh
          </button>
        </div>
      </div>

      <div className="flex gap-2">
        {['all', 'simulation', 'detection'].map((f) => (
          <button
            key={f}
            onClick={() => setFilter(f)}
            className={`btn ${filter === f ? 'bg-accent text-base-950' : 'btn-ghost'}`}
          >
            {f[0].toUpperCase() + f.slice(1)}
          </button>
        ))}
      </div>

      <Card>
        {sessLoading || loading ? (
          <LoadingState />
        ) : !activeId ? (
          <EmptyState title="No session selected" hint="Choose a session to view its events." />
        ) : !filtered.length ? (
          <EmptyState title="No events" hint="Generate telemetry or run detection to populate this log." />
        ) : (
          <ul className="divide-y divide-base-800">
            {filtered.map((r) => (
              <li key={r.id} className="flex items-start justify-between gap-4 py-3">
                <div className="min-w-0">
                  <div className="flex items-center gap-2">
                    <Badge tone={r.kind === 'detection' ? 'warn' : 'accent'}>
                      {r.kind}
                    </Badge>
                    <p className="text-sm font-medium text-slate-100 truncate">{r.title}</p>
                  </div>
                  <p className="text-xs text-slate-400 mt-1">{r.detail}</p>
                  {r.indicators?.length ? (
                    <div className="mt-1 flex flex-wrap gap-1">
                      {r.indicators.map((i) => (
                        <span key={i} className="badge bg-base-800 text-slate-300 border border-base-600">
                          {i}
                        </span>
                      ))}
                    </div>
                  ) : null}
                </div>
                <time className="shrink-0 text-xs text-slate-500">
                  {formatDateTime(r.time)}
                </time>
              </li>
            ))}
          </ul>
        )}
      </Card>
    </div>
  );
}
