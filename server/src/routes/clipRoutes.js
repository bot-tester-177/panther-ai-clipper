const express = require('express');
const router = express.Router();
const clipController = require('../controllers/clipController');

// Create a new clip
router.post('/', clipController.createClip);

// Get all clips
router.get('/', clipController.getClips);

// Get a single clip by ID
router.get('/:id', clipController.getClipById);

// Delete a clip by ID
router.delete('/:id', clipController.deleteClip);

module.exports = router;
