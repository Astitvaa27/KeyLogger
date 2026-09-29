import { riskStyle } from '../../utils/format';

export function SeverityBadge({ level }) {
  const s = riskStyle(level);
  return (
    <span className={`badge ${s.bg} ${s.text} border ${s.border}`}>{level}</span>
  );
}

export function Badge({ children, tone = 'neutral' }) {
  const tones = {
    neutral: 'bg-base-800 text-slate-300 border border-base-600',
    accent: 'bg-accent/15 text-accent border border-accent/40',
    success: 'bg-risk-low/15 text-risk-low border border-risk-low/40',
    warn: 'bg-risk-medium/15 text-risk-medium border border-risk-medium/40',
    danger: 'bg-risk-critical/15 text-risk-critical border border-risk-critical/40',
  };
  return <span className={`badge ${tones[tone] || tones.neutral}`}>{children}</span>;
}
