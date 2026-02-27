import { useEffect, useState } from 'react';
import { useRouter } from 'next/router';
import io from 'socket.io-client';

let socket;

export default function Clips() {
  const router = useRouter();
  const [clips, setClips] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const fetchClips = async () => {
    try {
      setLoading(true);
      setError(null);
      const headers = {};
      const token = window.localStorage.getItem('token');
      if (token) headers['Authorization'] = `Bearer ${token}`;
      const res = await fetch('/api/clips', { headers });
      if (!res.ok) {
        if (res.status === 401) {
          // not authenticated, send to login
          router.push('/login');
          return;
        }
        throw new Error(`fetch failed: ${res.status}`);
      }
      const data = await res.json();
      setClips(data);
    } catch (err) {
      console.error(err);
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchClips();

    if (!socket) {
      socket = io();
    }

    socket.on('new_clip', (clip) => {
      setClips((prev) => [clip, ...prev]);
    });

    return () => {
      socket.off('new_clip');
    };
  }, []);

  const deleteClip = async (id) => {
    if (!window.confirm('Are you sure you want to delete this clip?')) {
      return;
    }
    try {
      const headers = {};
      const token = window.localStorage.getItem('token');
      if (token) headers['Authorization'] = `Bearer ${token}`;
      const base = process.env.NEXT_PUBLIC_API_URL || '';
      const res = await fetch(`${base}/api/clips/${id}`, { method: 'DELETE', headers });
      if (!res.ok) {
        if (res.status === 401) {
          router.push('/login');
          return;
        }
        throw new Error('delete failed');
      }
      setClips((prev) => prev.filter((c) => c._id !== id));
    } catch (err) {
      console.error(err);
      alert('Failed to delete clip');
    }
  };

  return (
    <div className="min-h-screen bg-black text-green-400 font-mono p-4">
      <h1 className="text-3xl mb-4">Clips</h1>
      {loading && <p>Loading...</p>}
      {error && <p className="text-red-500">Error: {error}</p>}

      <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-4">
        {clips.map((clip) => (
          <div key={clip._id} className="bg-gray-900 rounded overflow-hidden shadow-lg flex flex-col">
            <video
              src={clip.url}
              className="w-full h-40 object-cover bg-black"
              controls
              muted
            />
            <div className="p-2 flex-1 flex flex-col justify-between">
              <div>
                <p className="text-sm">Score: {clip.hypeScore}</p>
                <p className="text-sm">Trigger: {clip.triggerType}</p>
                <p className="text-xs text-gray-400">
                  {new Date(clip.createdAt).toLocaleString()}
                </p>
              </div>
              <div className="mt-2 flex space-x-2">
                <button
                  onClick={() => deleteClip(clip._id)}
                  className="px-2 py-1 bg-red-600 rounded hover:bg-red-700 text-xs"
                >
                  Delete
                </button>
                <a
                  href={clip.url}
                  download={clip.fileName}
                  className="px-2 py-1 bg-cyber-cyan rounded hover:bg-cyber-pink text-xs"
                >
                  Download
                </a>
              </div>
            </div>
          </div>
        ))}
        {clips.length === 0 && !loading && (
          <p className="text-gray-500">No clips yet.</p>
        )}
      </div>
    </div>
  );
}
