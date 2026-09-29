import { useEffect, useState } from 'react';
import Card from '../components/ui/Card';
import { Badge } from '../components/ui/Badge';
import { useAuth } from '../context/AuthContext';
import { useActiveSession } from '../hooks/useActiveSession';
import { formatDateTime } from '../utils/format';

export default function SettingsPage() {
  const { user } = useAuth();
  const { sessions, refresh } = useActiveSession();
  const [apiBase] = useState(
    import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api',
  );

  useEffect(() => {
    refresh();
  }, [refresh]);

  return (
    <div className="space-y-5">
      <div>
        <h1 className="text-xl font-bold text-slate-100">Settings</h1>
        <p className="text-sm text-slate-400">Account, environment, and safety information.</p>
      </div>

      <div className="grid grid-cols-1 gap-5 lg:grid-cols-2">
        <Card title="Account">
          <dl className="text-sm space-y-2">
            <Row k="Username" v={user?.username} />
            <Row k="Email" v={user?.email} />
            <Row k="Full name" v={user?.full_name || '—'} />
            <Row k="Role" v={user?.is_superuser ? 'Administrator' : 'Analyst'} />
            <Row k="Member since" v={formatDateTime(user?.created_at)} />
          </dl>
        </Card>

        <Card title="Environment">
          <dl className="text-sm space-y-2">
            <Row k="API base URL" v={<span className="font-mono text-xs">{apiBase}</span>} />
            <Row k="Sessions" v={sessions.length} />
            <Row k="Mode" v={<Badge tone="accent">Educational / Defensive</Badge>} />
          </dl>
        </Card>
      </div>

      <Card title="Safety & scope">
        <div className="space-y-2 text-sm text-slate-400">
          <p>
            This platform is an educational, defensive simulation. It contains{' '}
            <span className="text-slate-200">no real keylogging capability</span>.
          </p>
          <ul className="list-disc pl-5 space-y-1">
            <li>Keystroke capture is limited to the in-app Lab textarea while a test is active.</li>
            <li>Only key category + timing metadata is stored — never the characters typed.</li>
            <li>Threat telemetry is fully synthetic; nothing reads the real OS or network.</li>
            <li>All actions are recorded in an audit log for accountability.</li>
          </ul>
        </div>
      </Card>
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
