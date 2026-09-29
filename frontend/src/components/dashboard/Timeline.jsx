import { formatTime } from '../../utils/format';

const KIND_META = {
  simulation: { dot: 'bg-accent', icon: '🧪' },
  detection: { dot: 'bg-risk-high', icon: '🛡️' },
  keystroke: { dot: 'bg-risk-low', icon: '⌨️' },
};

export default function Timeline({ points = [] }) {
  if (!points.length) {
    return <p className="text-sm text-slate-500">No recent events.</p>;
  }
  return (
    <ol className="relative border-l border-base-700 ml-2">
      {points.map((p, i) => {
        const meta = KIND_META[p.kind] || KIND_META.keystroke;
        return (
          <li key={i} className="mb-4 ml-4">
            <span
              className={`absolute -left-[7px] mt-1.5 h-3 w-3 rounded-full ${meta.dot} ring-2 ring-base-900`}
            />
            <div className="flex items-center justify-between gap-3">
              <p className="text-sm text-slate-200">
                <span className="mr-1">{meta.icon}</span>
                {p.label}
              </p>
              <time className="shrink-0 text-xs text-slate-500">
                {formatTime(p.timestamp)}
              </time>
            </div>
          </li>
        );
      })}
    </ol>
  );
}
