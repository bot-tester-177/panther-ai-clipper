export default function HypeMeter({ value, threshold }) {
  const percent = Math.min(100, Math.max(0, value));
  const isOver = percent >= threshold;
  return (
    <div className="mb-6">
      <div className="flex justify-between mb-1">
        <span className="text-sm">Hype</span>
        <span className="text-sm">{percent}%</span>
      </div>
      <div className="w-full bg-gray-800 rounded-full h-6 overflow-hidden">
        <div
          className={`h-full transition-all duration-300 ${
            isOver ? 'bg-pink-500' : 'bg-green-500'
          }`}
          style={{ width: `${percent}%` }}
        />
      </div>
      {isOver && <p className="mt-2 text-pink-400">Threshold reached!</p>}
    </div>
  );
}
