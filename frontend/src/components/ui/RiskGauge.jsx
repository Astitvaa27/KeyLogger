import { riskStyle } from '../../utils/format';

// Circular risk gauge showing score 0–100 and its level.
export default function RiskGauge({ score = 0, level = 'LOW', size = 160 }) {
  const s = riskStyle(level);
  const radius = (size - 16) / 2;
  const circ = 2 * Math.PI * radius;
  const clamped = Math.max(0, Math.min(100, score));
  const offset = circ - (clamped / 100) * circ;

  return (
    <div className="flex flex-col items-center gap-2">
      <div className="relative" style={{ width: size, height: size }}>
        <svg width={size} height={size} className="-rotate-90">
          <circle
            cx={size / 2}
            cy={size / 2}
            r={radius}
            fill="none"
            stroke="#1c2b4a"
            strokeWidth="12"
          />
          <circle
            cx={size / 2}
            cy={size / 2}
            r={radius}
            fill="none"
            stroke={s.hex}
            strokeWidth="12"
            strokeLinecap="round"
            strokeDasharray={circ}
            strokeDashoffset={offset}
            style={{ transition: 'stroke-dashoffset 0.6s ease' }}
          />
        </svg>
        <div className="absolute inset-0 grid place-items-center">
          <div className="text-center">
            <div className={`text-3xl font-bold ${s.text}`}>{clamped}</div>
            <div className="text-[10px] uppercase tracking-widest text-slate-500">
              / 100
            </div>
          </div>
        </div>
      </div>
      <span className={`badge ${s.bg} ${s.text} border ${s.border} text-sm`}>
        {level}
      </span>
    </div>
  );
}
