const express = require('express');
const cors = require('cors');
const bodyParser = require('body-parser');
const path = require('path');
const apiRoutes = require('./routes/api');

// Initialize express app
const app = express();
// In backend/server.js
const PORT = process.env.PORT || 3001; // Change from 5000 to 3001

// Middleware
app.use(cors({
  origin: 'http://localhost:3000', // Assuming frontend runs on port 3000
  methods: ['GET', 'POST'],
  allowedHeaders: ['Content-Type', 'Authorization']
}));

app.use(bodyParser.json());
app.use(bodyParser.urlencoded({ extended: true }));

// Serve static files if needed
app.use(express.static(path.join(__dirname, 'public')));

// API Routes
app.use('/api', apiRoutes);

// Basic route for testing
app.get('/', (req, res) => {
  res.send('Egyptian History RAG API is running');
});

// Error handling middleware
app.use((err, req, res, next) => {
  console.error(err.stack);
  res.status(500).send('Something broke!');
});

// Start server
app.listen(PORT, () => {
  console.log(`Server running on port ${PORT}`);
});

module.exports = app;