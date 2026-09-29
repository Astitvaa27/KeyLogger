// Formatting + risk styling helpers.

export function formatDuration(seconds) {
  const s = Math.max(0, Math.floor(seconds || 0));
  const m = Math.floor(s / 60);
  const rem = s % 60;
  return `${String(m).padStart(2, '0')}:${String(rem).padStart(2, '0')}`;
}

export function formatDateTime(iso) {
  if (!iso) return '—';
  try {
    return new Date(iso).toLocaleString();
  } catch {
    return iso;
  }
}

export function formatTime(iso) {
  if (!iso) return '—';
  try {
    return new Date(iso).toLocaleTimeString();
  } catch {
    return iso;
  }
}

// Tailwind class fragments keyed by risk / severity level.
export const RISK_STYLES = {
  LOW: {
    text: 'text-risk-low',
    bg: 'bg-risk-low/15',
    border: 'border-risk-low/40',
    hex: '#22c55e',
  },
  MEDIUM: {
    text: 'text-risk-medium',
    bg: 'bg-risk-medium/15',
    border: 'border-risk-medium/40',
    hex: '#eab308',
  },
  HIGH: {
    text: 'text-risk-high',
    bg: 'bg-risk-high/15',
    border: 'border-risk-high/40',
    hex: '#f97316',
  },
  CRITICAL: {
    text: 'text-risk-critical',
    bg: 'bg-risk-critical/15',
    border: 'border-risk-critical/40',
    hex: '#ef4444',
  },
};

export function riskStyle(level) {
  return RISK_STYLES[level] || RISK_STYLES.LOW;
}

// Recharts-friendly categorical palette.
export const CHART_COLORS = [
  '#22d3ee',
  '#a78bfa',
  '#f472b6',
  '#facc15',
  '#4ade80',
  '#fb923c',
  '#60a5fa',
  '#f87171',
  '#2dd4bf',
  '#c084fc',
];
