const io = require('socket.io-client');
const socket = io('http://localhost:3002');

socket.on('connect', () => {
  console.log('connected');
  const payload = { type: 'audio_spike', value: 0.9 };
  // send multiple times
  for (let i = 0; i < 5; i++) {
    socket.emit('hype_event', payload);
  }
});

socket.on('trigger_clip', (msg) => {
  console.log('received trigger_clip', msg);
  socket.disconnect();
});

socket.on('hype_ack', (msg) => console.log('ack', msg));

socket.on('disconnect', () => console.log('disconnect'));
