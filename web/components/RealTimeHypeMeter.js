import { useEffect, useState } from 'react';
import { getSocket } from '../lib/socket';

export default function RealTimeHypeMeter({ threshold: propThreshold }) {
  const [hype, setHype] = useState(0);
  const [threshold, setThreshold] = useState(propThreshold ?? 50);

  useEffect(() => {
    const socket = getSocket();
    socket.on('hypeUpdate', setHype);
    socket.on('thresholdUpdate', setThreshold);

    return () => {
      socket.off('hypeUpdate', setHype);
      socket.off('thresholdUpdate', setThreshold);
    };
  }, []);

  // if parent passes a different threshold keep them in sync
  useEffect(() => {
    if (propThreshold !== undefined && propThreshold !== threshold) {
      setThreshold(propThreshold);
    }
  }, [propThreshold, threshold]);

  const percent = Math.min(100, Math.max(0, hype));
  const isOver = percent >= threshold;
  const glowClass = isOver ? 'ring-4 ring-cyber-pink animate-pulse' : '';

  return (
    <div className="w-full max-w-xl mx-auto p-4 bg-cyber-bg rounded-lg shadow-xl">
      <div className="flex justify-between mb-2 text-cyber-green">
        <span className="text-lg font-semibold">Hype</span>
        <span className="text-lg font-semibold">{percent}%</span>
      </div>
      <div
        className={`relative w-full h-8 bg-gray-800 rounded-full overflow-hidden transition-shadow duration-300 ${glowClass}`}
      >
        <div
          className={`h-full transition-all duration-500 ease-out ${
            isOver ? 'bg-cyber-pink' : 'bg-cyber-cyan'
          }`}
          style={{ width: `${percent}%` }}
        />
      </div>
      {isOver && (
        <p className="mt-2 text-center text-cyber-pink font-bold">
          🔥 Threshold Reached!
        </p>
      )}
    </div>
  );
}
