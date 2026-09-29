import { useCallback, useEffect, useState } from 'react';
import Card from '../components/ui/Card';
import StatCard from '../components/ui/StatCard';
import { EmptyState, ErrorState, LoadingState } from '../components/ui/States';
import {
  CategoryBarChart,
  CategoryPieChart,
} from '../components/charts/Charts';
import { useActiveSession } from '../hooks/useActiveSession';
import { keystrokeApi } from '../services/endpoints';
import { CATEGORY_LABELS } from '../utils/keystroke';

export default function AnalyticsPage() {
  const { sessions, activeId, selectSession, loading: sessLoading } = useActiveSession();
  const [stats, setStats] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const load = useCallback(async () => {
    if (!activeId) {
      setStats(null);
      return;
    }
    setLoading(true);
    setError(null);
    try {
      setStats(await keystrokeApi.statistics(activeId));
    } catch (e) {
      setError(e?.response?.data?.detail || 'Failed to load statistics');
    } finally {
      setLoading(false);
    }
  }, [activeId]);

  useEffect(() => {
    load();
  }, [load]);

  const distribution =
    stats?.category_distribution?.map((c) => ({
      name: CATEGORY_LABELS[c.category] || c.category,
      value: c.count,
    })) || [];

  return (
    <div className="space-y-5">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <h1 className="text-xl font-bold text-slate-100">Keystroke Analytics</h1>
          <p className="text-sm text-slate-400">
            Behavioral statistics computed from keystroke metadata.
          </p>
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
                #{s.id} · {s.label || 'session'} ({s.total_keystrokes} keys)
              </option>
            ))}
          </select>
          <button className="btn-ghost" onClick={load} disabled={!activeId}>
            Refresh
          </button>
        </div>
      </div>

      {sessLoading || loading ? (
        <LoadingState />
      ) : error ? (
        <ErrorState message={error} onRetry={load} />
      ) : !activeId ? (
        <EmptyState title="No session selected" hint="Choose a session to view analytics." />
      ) : !stats || stats.total_keystrokes === 0 ? (
        <EmptyState
          title="No keystroke data yet"
          hint="Run a test in the Virtual Keylogger Lab to generate analytics."
        />
      ) : (
        <>
          <div className="grid grid-cols-2 gap-4 lg:grid-cols-4">
            <StatCard label="Total keystrokes" value={stats.total_keystrokes} icon="⌨️" accent="text-slate-100" />
            <StatCard label="Keystrokes / min" value={stats.keystrokes_per_minute} icon="⚡" />
            <StatCard label="Typing speed" value={`${stats.typing_speed_wpm} WPM`} icon="📝" accent="text-slate-100" />
            <StatCard label="Duration" value={`${stats.duration_seconds}s`} icon="⏱️" accent="text-slate-100" />
            <StatCard label="Avg interval" value={`${stats.average_interval_ms} ms`} icon="📏" accent="text-slate-100" />
            <StatCard label="Median interval" value={`${stats.median_interval_ms} ms`} icon="📐" accent="text-slate-100" />
            <StatCard label="Backspace rate" value={`${(stats.backspace_rate * 100).toFixed(1)}%`} icon="⌫" accent="text-risk-medium" />
            <StatCard label="Modifier freq." value={`${(stats.modifier_frequency * 100).toFixed(1)}%`} icon="⇧" accent="text-slate-100" />
          </div>

          <div className="grid grid-cols-1 gap-5 lg:grid-cols-2">
            <Card title="Key category distribution" subtitle="Counts by key category">
              <CategoryBarChart data={distribution} />
            </Card>
            <Card title="Category share" subtitle="Proportion of each category">
              <CategoryPieChart data={distribution} />
            </Card>
          </div>

          <div className="grid grid-cols-1 gap-5 lg:grid-cols-3">
            <Card title="Editing behavior">
              <dl className="text-sm space-y-2">
                <Row k="Backspace / delete count" v={stats.backspace_count} />
                <Row k="Backspace rate" v={`${(stats.backspace_rate * 100).toFixed(1)}%`} />
                <Row k="Total pause time" v={`${(stats.total_pause_ms / 1000).toFixed(1)} s`} />
              </dl>
            </Card>
            <Card title="Timing">
              <dl className="text-sm space-y-2">
                <Row k="Average inter-key" v={`${stats.average_interval_ms} ms`} />
                <Row k="Median inter-key" v={`${stats.median_interval_ms} ms`} />
                <Row k="Keystrokes / minute" v={stats.keystrokes_per_minute} />
              </dl>
            </Card>
            <Card title="Modifier usage">
              <dl className="text-sm space-y-2">
                <Row k="Modifier key count" v={stats.modifier_count} />
                <Row k="Modifier frequency" v={`${(stats.modifier_frequency * 100).toFixed(1)}%`} />
                <Row k="Typing speed" v={`${stats.typing_speed_wpm} WPM`} />
              </dl>
            </Card>
          </div>
        </>
      )}
    </div>
  );
}

function Row({ k, v }) {
  return (
    <div className="flex items-center justify-between border-b border-base-800 pb-1.5">
      <dt className="text-slate-400">{k}</dt>
      <dd className="font-medium text-slate-100">{v}</dd>
    </div>
  );
}
