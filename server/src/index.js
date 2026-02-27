require('dotenv').config();
const express = require('express');
const cors = require('cors');
const http = require('http');
const { Server } = require('socket.io');
const mongoose = require('mongoose');

// simple shared logger
const { log, warn, error } = require('./utils');

// services
const { HypeEngine } = require('./services');

// routes
const clipRoutes = require('./routes/clipRoutes');
const authRoutes = require('./routes/authRoutes');
const { authenticateToken } = require('./middleware/authMiddleware');

const app = express();
const port = process.env.PORT || 3001;

// middleware
app.use(express.json());
app.use(express.urlencoded({ extended: true }));

// enable CORS for frontend; in production you may want to restrict
// the origin (e.g. process.env.CORS_ORIGIN)
app.use(
  cors({
    origin: process.env.CORS_ORIGIN || '*',
    methods: ['GET', 'POST', 'PUT', 'DELETE', 'OPTIONS']
  })
);

// create http server so socket.io can attach
const server = http.createServer(app);

// MongoDB connection with graceful fallback; production deployments
// should supply a full connection string via MONGODB_URI.
let dbConnected = false;
const mongoUri = process.env.MONGODB_URI || 'mongodb://localhost:27017/panther-clips';
mongoose.connect(mongoUri, { serverSelectionTimeoutMS: 3000 })
  .then(() => {
    log('Connected to MongoDB');
    dbConnected = true;
  })
  .catch(err => {
    warn('MongoDB connection failed, using in-memory storage:', err.message);
    dbConnected = false;
  });

// Middleware to update MongoDB connection status
app.use((req, res, next) => {
  req.app.locals.dbConnected = dbConnected;
  next();
});

// initialize websocket server
const io = new Server(server, {
  cors: {
    origin: process.env.CORS_ORIGIN || '*',
    methods: ['GET', 'POST', 'PUT', 'DELETE', 'OPTIONS']
  }
});

// make io accessible to controllers via app (used for emitting new clip events)
app.set('io', io);

// create a single hype engine instance; threshold may be overridden via
// environment variable or other configuration mechanism.
const hype = new HypeEngine({
  threshold: Number(process.env.HYPE_THRESHOLD) || 10
});

// forward trigger events to all connected clients
hype.on('trigger_clip', ({ score }) => {
  log('hype threshold crossed, emitting trigger_clip (score=', score, ')');
  io.emit('trigger_clip', { score });
});

// WebSocket connection handler
io.on('connection', (socket) => {
  log('client connected:', socket.id);

  // send current hype/threshold to new client
  socket.emit('hypeUpdate', hype.score || 0);
  socket.emit('thresholdUpdate', hype.threshold);

  // basic text message example (mostly used during development)
  socket.on('message', (msg) => {
    log('received message:', msg);
    socket.emit('message', msg);
  });

  // allow clients to notify the server about various hype events
  socket.on('hype_event', (payload) => {
    // payload may be a string or an object with {type, value}
    let type;
    if (typeof payload === 'object' && payload !== null) {
      type = payload.type;
      // value is currently unused but might be useful for future weighting
      log('received hype_event', payload);
    } else {
      type = payload;
    }

    // broadcast event to everyone (for the feed)
    const evt = { type, timestamp: Date.now(), detail: payload.detail || '' };
    io.emit('event', evt);

    const { score, triggered } = hype.addEvent(type);
    if (triggered) {
      io.emit('hypeUpdate', score); // notify all of new score
      socket.emit('hype_ack', { triggered: true, score });
    } else {
      // update metrics for everyone anyway
      io.emit('hypeUpdate', score);
    }
  });

  socket.on('thresholdChange', (newThreshold) => {
    log('threshold change requested by', socket.id, newThreshold);
    hype.threshold = Number(newThreshold) || hype.threshold;
    io.emit('thresholdUpdate', hype.threshold);
  });

  socket.on('disconnect', () => {
    log('client disconnected:', socket.id);
  });
});

// HTTP routes
app.use('/api/auth', authRoutes);
// protect clip endpoints - require a valid JWT
app.use('/api/clips', authenticateToken, clipRoutes);

// health check (prefixed with /api for consistency)
app.get('/api/health', (req, res) => res.json({ status: 'ok' }));
// keep legacy route if needed
app.get('/health', (req, res) => res.redirect('/api/health'));

// start both HTTP and WebSocket server
server.listen(port, () => {
  // always log startup so process managers know we're alive
  console.log(`Server listening on port ${port}`);
});
