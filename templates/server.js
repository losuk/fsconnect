// server.js
const express = require('express');
const cors = require('cors');
const crypto = require('crypto');
const path = require('path');
const app = express();

// Middleware
app.use(cors());
app.use(express.json());

// Serve static files from the "public" directory
app.use(express.static(path.join(__dirname, 'public')));

// In-memory store for API keys (Replace with a database in production)
let apiKeys = []; // Each key: { key: '...', createdAt: Date, status: 'Active' }

// Function to generate a new API key
function generateApiKey() {
    return crypto.randomBytes(16).toString('hex');
}

// Route to generate a new API key
app.post('/api/keys', (req, res) => {
    console.log('Received request to generate a new API key.');
    if (apiKeys.length >= 5) {
        console.log('Maximum number of API keys reached.');
        return res.status(400).json({ message: 'Maximum number of API keys reached.' });
    }
    const newKey = generateApiKey();
    const apiKey = {
        key: newKey,
        createdAt: new Date(),
        status: 'Active'
    };
    apiKeys.push(apiKey);
    console.log('Generated new API key:', newKey);
    res.json(apiKey);
});

// Route to get all API keys
app.get('/api/keys', (req, res) => {
    console.log('Received request to fetch all API keys.');
    res.json(apiKeys);
});

// Route to regenerate an API key
app.post('/api/keys/:key/regenerate', (req, res) => {
    const { key } = req.params;
    console.log(`Received request to regenerate API key: ${key}`);
    const index = apiKeys.findIndex(apiKey => apiKey.key === key);
    if (index === -1) {
        console.log('API key not found.');
        return res.status(404).json({ message: 'API key not found.' });
    }
    const newKey = generateApiKey();
    apiKeys[index] = {
        key: newKey,
        createdAt: new Date(),
        status: 'Active'
    };
    console.log(`API key regenerated: Old Key = ${key}, New Key = ${newKey}`);
    res.json(apiKeys[index]);
});

// Route to delete an API key
app.delete('/api/keys/:key', (req, res) => {
    const { key } = req.params;
    console.log(`Received request to delete API key: ${key}`);
    const index = apiKeys.findIndex(apiKey => apiKey.key === key);
    if (index === -1) {
        console.log('API key not found.');
        return res.status(404).json({ message: 'API key not found.' });
    }
    apiKeys.splice(index, 1);
    console.log('API key deleted successfully:', key);
    res.json({ message: 'API key deleted successfully.' });
});

// Catch-all route to serve api-keys.html for any non-API routes
app.get('*', (req, res) => {
    res.sendFile(path.join(__dirname, 'public', 'api-keys.html'));
});

// Start the server
const PORT = process.env.PORT || 5000;
app.listen(PORT, () => {
    console.log(`Server is running on port ${PORT}`);
});
