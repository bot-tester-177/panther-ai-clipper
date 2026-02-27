const mongoose = require('mongoose');

const clipSchema = new mongoose.Schema({
  fileName: {
    type: String,
    required: true
  },
  url: {
    type: String,
    required: true
  },
  hypeScore: {
    type: Number,
    required: true
  },
  triggerType: {
    type: String,
    required: true,
    enum: ['audio_spike', 'chat_spam', 'keyword', 'scene_change', 'manual_trigger']
  },
  createdAt: {
    type: Date,
    default: Date.now
  }
});

module.exports = mongoose.model('Clip', clipSchema);
