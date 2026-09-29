export default function StatCard({ label, value, hint, accent = 'text-accent', icon }) {
  return (
    <div className="card flex items-center gap-4">
      {icon && (
        <div className="shrink-0 w-11 h-11 rounded-lg bg-base-800 grid place-items-center text-lg">
          {icon}
        </div>
      )}
      <div className="min-w-0">
        <p className="label mb-0.5">{label}</p>
        <p className={`text-2xl font-semibold leading-tight ${accent}`}>{value}</p>
        {hint && <p className="text-xs text-slate-500 mt-0.5 truncate">{hint}</p>}
      </div>
    </div>
  );
}
