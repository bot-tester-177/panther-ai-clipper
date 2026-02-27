const Clip = require('../models/Clip');
const { InMemoryClip } = require('../models/InMemoryStore');
const { log, warn, error } = require('../utils');

// Helper to get appropriate storage (MongoDB or in-memory)
const getClipModel = (dbConnected) => dbConnected ? Clip : InMemoryClip;

// Create a new clip
exports.createClip = async (req, res) => {
  try {
    const { fileName, url, hypeScore, triggerType } = req.body;
    const dbConnected = req.app.locals.dbConnected;

    // Validate required fields
    if (!fileName || !url || hypeScore === undefined || !triggerType) {
      return res.status(400).json({
        error: 'Missing required fields: fileName, url, hypeScore, triggerType'
      });
    }

    const ClipModel = getClipModel(dbConnected);
    const clip = new ClipModel({
      fileName,
      url,
      hypeScore,
      triggerType
    });

    const savedClip = await clip.save();

    // notify any realtime clients about the new clip
    try {
      const io = req.app.get('io');
      if (io) {
        io.emit('new_clip', savedClip);
      }
    } catch (emitErr) {
      warn('Failed to emit new_clip event:', emitErr.message);
    }

    res.status(201).json(savedClip);
  } catch (error) {
    error('Error creating clip:', error);
    res.status(500).json({
      error: 'Failed to create clip',
      details: error.message
    });
  }
};

// Get all clips
exports.getClips = async (req, res) => {
  try {
    const dbConnected = req.app.locals.dbConnected;
    const ClipModel = getClipModel(dbConnected);

    const clips = await ClipModel.find();
    res.json(clips);
  } catch (error) {
    error('Error fetching clips:', error);
    res.status(500).json({
      error: 'Failed to fetch clips',
      details: error.message
    });
  }
};

// Get a single clip by ID
exports.getClipById = async (req, res) => {
  try {
    const { id } = req.params;
    const dbConnected = req.app.locals.dbConnected;
    const ClipModel = getClipModel(dbConnected);

    const clip = await ClipModel.findById(id);
    if (!clip) {
      return res.status(404).json({ error: 'Clip not found' });
    }

    res.json(clip);
  } catch (error) {
    error('Error fetching clip:', error);
    res.status(500).json({
      error: 'Failed to fetch clip',
      details: error.message
    });
  }
};

// Delete a clip by ID
exports.deleteClip = async (req, res) => {
  try {
    const { id } = req.params;
    const dbConnected = req.app.locals.dbConnected;
    const ClipModel = getClipModel(dbConnected);

    const clip = await ClipModel.findByIdAndDelete(id);
    if (!clip) {
      return res.status(404).json({ error: 'Clip not found' });
    }

    res.json({
      message: 'Clip deleted successfully',
      deletedClip: clip
    });
  } catch (error) {
    error('Error deleting clip:', error);
    res.status(500).json({
      error: 'Failed to delete clip',
      details: error.message
    });
  }
};
