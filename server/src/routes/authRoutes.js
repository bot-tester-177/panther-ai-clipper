const express = require('express');
const router = express.Router();
const authController = require('../controllers/authController');

// register new account
router.post('/register', authController.register);
// login and receive jwt
router.post('/login', authController.login);

module.exports = router;
