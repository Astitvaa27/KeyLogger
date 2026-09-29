import { useCallback, useEffect, useState } from 'react';
import Card from '../components/ui/Card';
import RiskGauge from '../components/ui/RiskGauge';
import { SeverityBadge } from '../components/ui/Badge';
import { EmptyState, LoadingState } from '../components/ui/States';
import SessionPicker from '../components/SessionPicker';
import { useActiveSession } from '../hooks/useActiveSession';
import { detectionApi } from '../services/endpoints';
import { formatDateTime, riskStyle } from '../utils/format';

export default function DetectionPage() {
  const { sessions, activeId, selectSession, startSession, loading } = useActiveSession();
  const [rules, setRules] = useState([]);
  const [result, setResult] = useState(null);
  const [history, setHistory] = useState([]);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState(null);

  useEffect(() => {
    detectionApi.rules().then(setRules).catch(() => setRules([]));
  }, []);

  const loadResults = useCallback(async () => {
    if (!activeId) {
      setHistory([]);
      setResult(null);
      return;
    }
    try {
      const res = await detectionApi.results(activeId);
      setHistory(res);
      setResult(res[0] || null);
    } catch {
      setHistory([]);
    }
  }, [activeId]);

  useEffect(() => {
    loadResults();
  }, [loadResults]);

  async function runAnalysis() {
    setBusy(true);
    setError(null);
    try {
      let sid = activeId;
      if (!sid) {
        const s = await startSession('Detection run');
        sid = s.id;
      }
      const res = await detectionApi.analyze(sid);
      setResult(res);
      await loadResults();
    } catch (e) {
      setError(e?.response?.data?.detail || 'Analysis failed');
    } finally {
      setBusy(false);
    }
  }

  if (loading) return <LoadingState />;

  const triggered = result?.triggered_rules || [];

  return (
    <div className="space-y-5">
      <div>
        <h1 className="text-xl font-bold text-slate-100">Detection & Risk Scoring</h1>
        <p className="text-sm text-slate-400">
          Rule-based engine over synthetic telemetry, with a transparent score breakdown.
        </p>
      </div>

      <SessionPicker
        sessions={sessions}
        activeId={activeId}
        onSelect={selectSession}
        onStart={() => startSession('Detection run')}
        busy={busy}
      />

      <div className="flex items-center gap-2">
        <button className="btn-primary" onClick={runAnalysis} disabled={busy}>
          {busy ? 'Analyzing…' : '▶ Run detection analysis'}
        </button>
        {error && <span className="text-sm text-risk-critical">{error}</span>}
      </div>

      {result ? (
        <div className="grid grid-cols-1 gap-5 lg:grid-cols-3">
          <Card title="Current risk" className="lg:col-span-1">
            <div className="flex flex-col items-center gap-3 py-2">
              <RiskGauge score={result.risk_score} level={result.risk_level} />
              <p className="text-xs text-slate-500">
                Analyzed {formatDateTime(result.created_at)}
              </p>
            </div>
          </Card>

          <Card
            title="Score breakdown"
            subtitle="Exactly which rules contributed — no black box"
            className="lg:col-span-2"
          >
            {triggered.length === 0 ? (
              <EmptyState
                title="No rules triggered"
                hint="This session's synthetic telemetry did not match any detection rule (score 0 / LOW)."
              />
            ) : (
              <ul className="space-y-3">
                {triggered.map((t) => {
                  const s = riskStyle(t.severity);
                  return (
                    <li
                      key={t.rule_id}
                      className={`rounded-lg border ${s.border} ${s.bg} p-3`}
                    >
                      <div className="flex items-start justify-between gap-3">
                        <div>
                          <p className="text-sm font-semibold text-slate-100">
                            <span className="font-mono text-accent">{t.rule_id}</span> ·{' '}
                            {t.name}
                          </p>
                          <p className="text-xs text-slate-400 mt-0.5">{t.description}</p>
                        </div>
                        <div className="text-right shrink-0">
                          <SeverityBadge level={t.severity} />
                          <p className={`mt-1 text-lg font-bold ${s.text}`}>
                            +{t.contribution}
                          </p>
                        </div>
                      </div>
                      <p className="mt-2 text-xs text-slate-300">
                        <span className="text-slate-500">Evidence:</span> {t.evidence}
                      </p>
                      <p className="mt-1 text-xs text-slate-300">
                        <span className="text-slate-500">Recommendation:</span>{' '}
                        {t.recommendation}
                      </p>
                    </li>
                  );
                })}
              </ul>
            )}
          </Card>
        </div>
      ) : (
        <EmptyState
          title="No detection results yet"
          hint="Generate synthetic telemetry in Threat Simulation, then run analysis here."
        />
      )}

      <Card title="Detection rule catalog" subtitle="The full rule set and scoring weights">
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="text-left text-xs uppercase tracking-wide text-slate-500 border-b border-base-700">
                <th className="py-2 pr-3">Rule</th>
                <th className="py-2 pr-3">Name</th>
                <th className="py-2 pr-3">Severity</th>
                <th className="py-2 pr-3">Weight</th>
                <th className="py-2 pr-3">Recommendation</th>
              </tr>
            </thead>
            <tbody>
              {rules.map((r) => (
                <tr key={r.rule_id} className="border-b border-base-800/60 align-top">
                  <td className="py-2 pr-3 font-mono text-accent">{r.rule_id}</td>
                  <td className="py-2 pr-3 text-slate-200">{r.name}</td>
                  <td className="py-2 pr-3"><SeverityBadge level={r.severity} /></td>
                  <td className="py-2 pr-3 font-semibold">+{r.weight}</td>
                  <td className="py-2 pr-3 text-slate-400 max-w-md">{r.recommendation}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </Card>

      {history.length > 1 && (
        <Card title="Analysis history" subtitle="Previous detection runs for this session">
          <ul className="space-y-2 text-sm">
            {history.map((h) => {
              const s = riskStyle(h.risk_level);
              return (
                <li
                  key={h.id}
                  className="flex items-center justify-between border-b border-base-800 pb-2"
                >
                  <span className="text-slate-400">{formatDateTime(h.created_at)}</span>
                  <span className="flex items-center gap-2">
                    <span className={`font-semibold ${s.text}`}>{h.risk_score}</span>
                    <SeverityBadge level={h.risk_level} />
                  </span>
                </li>
              );
            })}
          </ul>
        </Card>
      )}
    </div>
  );
}
