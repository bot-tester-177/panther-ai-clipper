export default function SettingsPanel({ threshold, onThresholdChange }) {
  return (
    <div className="bg-gray-900 p-4 rounded">
      <h2 className="text-xl mb-2">Settings</h2>
      <div className="flex flex-col">
        <label className="mb-1" htmlFor="threshold">
          Threshold ({threshold}%)
        </label>
        <input
          id="threshold"
          type="range"
          min="0"
          max="100"
          value={threshold}
          onChange={(e) => onThresholdChange(Number(e.target.value))}
          className="w-full"
        />
      </div>
    </div>
  );
}
