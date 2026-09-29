import { Link } from 'react-router-dom';
import Card from '../components/ui/Card';
import StatCard from '../components/ui/StatCard';
import RiskGauge from '../components/ui/RiskGauge';
import { Badge } from '../components/ui/Badge';
import { ErrorState, LoadingState } from '../components/ui/States';
import Timeline from '../components/dashboard/Timeline';
import { useDashboard } from '../hooks/useDashboard';

export default function DashboardPage() {
  const { summary, loading, error, live, reload } = useDashboard();

  if (loading) return <LoadingState label="Loading SOC dashboard…" />;
  if (error) return <ErrorState message={error} onRetry={reload} />;

  const s = summary;

  return (
    <div className="space-y-5">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <h1 className="text-xl font-bold text-slate-100">SOC Dashboard</h1>
          <p className="text-sm text-slate-400">
            Real-time security operations overview.
          </p>
        </div>
        <div className="flex items-center gap-2">
          <Badge tone={live ? 'success' : 'warn'}>
            {live ? '● LIVE (WebSocket)' : '○ Polling'}
          </Badge>
          <button className="btn-ghost" onClick={reload}>
            Refresh
          </button>
        </div>
      </div>

      <div className="grid grid-cols-1 gap-5 lg:grid-cols-3">
        <Card title="Current risk level" className="flex flex-col items-center">
          <RiskGauge score={s.current_risk_score} level={s.current_risk_level} />
        </Card>

        <div className="lg:col-span-2 grid grid-cols-2 gap-4 sm:grid-cols-3 content-start">
          <StatCard label="Events detected" value={s.events_detected} icon="🧪" accent="text-slate-100" />
          <StatCard label="Rules triggered" value={s.detection_rules_triggered} icon="🛡️" accent="text-risk-high" />
          <StatCard label="Suspicious processes" value={s.suspicious_processes} icon="⚠️" accent="text-risk-critical" />
          <StatCard label="Keyboard events" value={s.total_keyboard_events} icon="⌨️" accent="text-slate-100" />
          <StatCard label="Total sessions" value={s.total_sessions} icon="🗂️" accent="text-slate-100" />
          <StatCard
            label="Active test session"
            value={s.active_test_session ? `#${s.active_session_id}` : 'None'}
            icon="🎯"
            accent={s.active_test_session ? 'text-risk-low' : 'text-slate-400'}
          />
        </div>
      </div>

      <div className="grid grid-cols-1 gap-5 lg:grid-cols-3">
        <Card
          title="Event timeline"
          subtitle="Most recent activity"
          className="lg:col-span-2"
        >
          <Timeline points={s.timeline} />
        </Card>

        <Card title="Operations status">
          <div className="space-y-3 text-sm">
            <StatusRow
              label="Threat simulation"
              value={s.simulation_status}
              tone={s.simulation_status === 'RUNNING' ? 'success' : 'neutral'}
            />
            <StatusRow
              label="Active capture session"
              value={s.active_test_session ? 'ACTIVE' : 'IDLE'}
              tone={s.active_test_session ? 'success' : 'neutral'}
            />
            <StatusRow
              label="Highest risk"
              value={s.current_risk_level}
              tone={
                s.current_risk_level === 'CRITICAL' || s.current_risk_level === 'HIGH'
                  ? 'danger'
                  : s.current_risk_level === 'MEDIUM'
                    ? 'warn'
                    : 'success'
              }
            />
          </div>
          <div className="mt-5 space-y-2">
            <Link to="/keylogger-lab" className="btn-primary w-full">
              Open Keylogger Lab
            </Link>
            <Link to="/threat-simulation" className="btn-ghost w-full">
              Run threat simulation
            </Link>
            <Link to="/detection" className="btn-ghost w-full">
              View detection & risk
            </Link>
          </div>
        </Card>
      </div>
    </div>
  );
}

function StatusRow({ label, value, tone }) {
  return (
    <div className="flex items-center justify-between border-b border-base-800 pb-2">
      <span className="text-slate-400">{label}</span>
      <Badge tone={tone}>{value}</Badge>
    </div>
  );
}
