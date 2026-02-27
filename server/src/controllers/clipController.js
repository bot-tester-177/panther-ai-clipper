const Clip = require('../models/Clip');

// Create a new clip
exports.createClip = async (req, res) => {
  try {
    const { fileName, url, hypeScore, triggerType } = req.body;

    // Validate required fields
    if (!fileName || !url || hypeScore === undefined || !triggerType) {
      return res.status(400).json({
        error: 'Missing required fields: fileName, url, hypeScore, triggerType'
      });
    }

    const clip = new Clip({
      fileName,
      url,
      hypeScore,
      triggerType
    });

    const savedClip = await clip.save();
    res.status(201).json(savedClip);
  } catch (error) {
    console.error('Error creating clip:', error);
    res.status(500).json({
      error: 'Failed to create clip',
      details: error.message
    });
  }
};

// Get all clips
exports.getClips = async (req, res) => {
  try {
    const clips = await Clip.find().sort({ createdAt: -1 });
    res.json(clips);
  } catch (error) {
    console.error('Error fetching clips:', error);
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

    const clip = await Clip.findById(id);
    if (!clip) {
      return res.status(404).json({ error: 'Clip not found' });
    }

    res.json(clip);
  } catch (error) {
    console.error('Error fetching clip:', error);
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

    const clip = await Clip.findByIdAndDelete(id);
    if (!clip) {
      return res.status(404).json({ error: 'Clip not found' });
    }

    res.json({
      message: 'Clip deleted successfully',
      deletedClip: clip
    });
  } catch (error) {
    console.error('Error deleting clip:', error);
    res.status(500).json({
      error: 'Failed to delete clip',
      details: error.message
    });
  }
};
