const express = require('express');
const http = require('http');
const { Server } = require('socket.io');

// services
const { HypeEngine } = require('./services');

const app = express();
const port = process.env.PORT || 3001;

// create http server so socket.io can attach
const server = http.createServer(app);

// initialize websocket server
const io = new Server(server, {
  cors: {
    origin: '*',
    methods: ['GET', 'POST']
  }
});

// create a single hype engine instance; threshold may be overridden via
// environment variable or other configuration mechanism.
const hype = new HypeEngine({
  threshold: Number(process.env.HYPE_THRESHOLD) || 10
});

// forward trigger events to all connected clients
hype.on('trigger_clip', ({ score }) => {
  console.log('hype threshold crossed, emitting trigger_clip (score=', score, ')');
  io.emit('trigger_clip', { score });
});

// WebSocket connection handler
io.on('connection', (socket) => {
  console.log('client connected:', socket.id);

  // basic text message example
  socket.on('message', (msg) => {
    console.log('received message:', msg);
    socket.emit('message', msg);
  });

  // allow clients to notify the server about various hype events
  socket.on('hype_event', (payload) => {
    // payload may be a string or an object with {type, value}
    let type;
    if (typeof payload === 'object' && payload !== null) {
      type = payload.type;
      // value is currently unused but might be useful for future weighting
      console.log('received hype_event', payload);
    } else {
      type = payload;
    }

    const { score, triggered } = hype.addEvent(type);
    if (triggered) {
      socket.emit('hype_ack', { triggered: true, score });
    }
  });

  socket.on('disconnect', () => {
    console.log('client disconnected:', socket.id);
  });
});

// HTTP routes
// Future route imports
// const routes = require('./routes');
// app.use('/api', routes(app));

// health check (prefixed with /api for consistency)
app.get('/api/health', (req, res) => res.json({ status: 'ok' }));
// keep legacy route if needed
app.get('/health', (req, res) => res.redirect('/api/health'));

// start both HTTP and WebSocket server
server.listen(port, () => {
  console.log(`Server listening on http://localhost:${port}`);
});
