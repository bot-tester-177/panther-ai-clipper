export default function EventFeed({ events }) {
  return (
    <div className="mb-6">
      <h2 className="text-xl mb-2">Event Feed</h2>
      <ul className="space-y-1 max-h-64 overflow-y-auto bg-gray-900 p-2 rounded">
        {events.map((evt, idx) => (
          <li key={idx} className="text-sm">
            <span className="text-cyan-400">[{new Date(evt.timestamp).toLocaleTimeString()}]</span>{' '}
            {evt.type}: {evt.detail}
          </li>
        ))}
        {events.length === 0 && <li className="text-gray-500">No events yet.</li>}
      </ul>
    </div>
  );
}
