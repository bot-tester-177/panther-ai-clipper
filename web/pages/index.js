export default function Home() {
  return (
    <div className="min-h-screen bg-cyber-bg text-cyber-green font-mono p-8">
      <h1 className="text-4xl mb-4">Panther AI Clipper — Web</h1>
      <p className="mb-4">Placeholder Next.js app.</p>
      <div className="space-x-4">
        <a href="/dashboard" className="text-cyber-cyan underline">
          Go to Dashboard
        </a>
        <a href="/clips" className="text-cyber-cyan underline">
          View Clips
        </a>
      </div>
    </div>
  );
}
