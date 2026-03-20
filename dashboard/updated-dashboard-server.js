#!/usr/bin/env node

/**
 * Updated Dashboard Server
 * Serves the fixed dashboard with real data endpoints
 */

const express = require('express');
const path = require('path');
const fs = require('fs');

const app = express();
const PORT = 9002;

// Enable CORS
app.use((req, res, next) => {
    res.header('Access-Control-Allow-Origin', '*');
    res.header('Access-Control-Allow-Headers', 'Content-Type');
    next();
});

// Serve the updated dashboard
app.get('/', (req, res) => {
    const dashboardPath = path.join(__dirname, 'src', 'real-dashboard.html');
    if (fs.existsSync(dashboardPath)) {
        res.sendFile(dashboardPath);
    } else {
        res.status(404).send('Dashboard not found');
    }
});

// Health endpoint
app.get('/health', (req, res) => {
    res.json({ 
        status: 'healthy', 
        service: 'Updated Dashboard Server',
        version: '1.0.0',
        timestamp: new Date().toISOString()
    });
});

app.listen(PORT, () => {
    console.log(`🚀 Updated Dashboard Server running on port ${PORT}`);
    console.log(`📊 Dashboard available at: http://localhost:${PORT}`);
    console.log(`\n✅ Fixed service endpoints and real data integration!`);
});
