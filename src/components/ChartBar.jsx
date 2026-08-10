export default function ChartBar({ label, value, max, color }) {
  const pct = Math.round((value / max) * 100);
  return (
    <div className="space-y-1.5">
      <div className="flex justify-between text-sm font-semibold">
        <span className="text-morocco-dark">{label}</span>
        <span className="text-morocco-light">{value}</span>
      </div>
      <div className="h-3 bg-gray-100 rounded-full overflow-hidden">
        <div
          className="h-full rounded-full transition-all duration-1000 ease-out"
          style={{ width: `${pct}%`, backgroundColor: color }}
        />
      </div>
    </div>
  );
}