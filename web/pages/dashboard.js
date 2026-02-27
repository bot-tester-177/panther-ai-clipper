import { useEffect, useState } from 'react';
import io from 'socket.io-client';
import HypeMeter from '../components/HypeMeter';
import EventFeed from '../components/EventFeed';
import SettingsPanel from '../components/SettingsPanel';

let socket;

export default function Dashboard() {
  const [hype, setHype] = useState(0);
  const [events, setEvents] = useState([]);
  const [threshold, setThreshold] = useState(50);

  useEffect(() => {
    // only create socket once
    if (!socket) {
      socket = io(); // connects to same origin by default
    }

    socket.on('hypeUpdate', (value) => {
      setHype(value);
    });

    socket.on('thresholdUpdate', (newThresh) => {
      setThreshold(newThresh);
    });

    socket.on('event', (evt) => {
      setEvents((prev) => [evt, ...prev].slice(0, 50));
    });

    return () => {
      socket.off('hypeUpdate');
      socket.off('event');
    };
  }, []);

  const handleThresholdChange = (newThreshold) => {
    setThreshold(newThreshold);
    socket?.emit('thresholdChange', newThreshold);
  };

  return (
    <div className="min-h-screen bg-black text-green-400 font-mono p-4">
      <h1 className="text-3xl mb-4">Live Hype Dashboard</h1>
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <div className="md:col-span-2">
          <HypeMeter value={hype} threshold={threshold} />
          <EventFeed events={events} />
          <div className="mt-4">
            <h2 className="text-xl mb-2">Debug / emit test events</h2>
            <div className="space-x-2">
              {['audio_spike','chat_spam','keyword','scene_change','manual_trigger'].map((type) => (
                <button
                  key={type}
                  className="px-3 py-1 bg-cyber-cyan rounded hover:bg-cyber-pink"
                  onClick={() => socket.emit('hype_event', { type })}
                >
                  {type}
                </button>
              ))}
            </div>
          </div>
        </div>
        <SettingsPanel threshold={threshold} onThresholdChange={handleThresholdChange} />
      </div>
    </div>
  );
}
