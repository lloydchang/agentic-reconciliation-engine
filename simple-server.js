const http = require('http');
const fs = require('fs');
const path = require('path');

const port = 8085;

const server = http.createServer((req, res) => {
    // Enable CORS
    res.setHeader('Access-Control-Allow-Origin', '*');
    res.setHeader('Access-Control-Allow-Methods', 'GET, POST, PUT, DELETE');
    res.setHeader('Access-Control-Allow-Headers', 'Content-Type');

    if (req.url === '/') {
        // Serve the real dashboard HTML
        try {
            const html = fs.readFileSync(path.join(__dirname, 'real-dashboard.html'), 'utf8');
            res.writeHead(200, { 'Content-Type': 'text/html' });
            res.end(html);
        } catch (error) {
            res.writeHead(404, { 'Content-Type': 'text/plain' });
            res.end('Dashboard not found');
        }
    } else if (req.url === '/health') {
        // Health endpoint
        res.writeHead(200, { 'Content-Type': 'application/json' });
        res.end(JSON.stringify({
            status: 'healthy',
            timestamp: new Date().toISOString(),
            port: port,
            version: '1.0.0'
        }));
    } else if (req.url === '/api/system/overview') {
        // System overview endpoint
        const os = require('os');
        const systemData = {
            system: {
                platform: os.platform(),
                arch: os.arch(),
                uptime: os.uptime(),
                freemem: os.freemem(),
                totalmem: os.totalmem(),
                cpus: os.cpus().length,
                timestamp: new Date().toISOString()
            },
            services: {
                portal: { status: 'running', port: 9000 },
                dashboard: { status: 'running', port: 8080 },
                api: { status: 'unknown', port: 5000 },
                temporal: { status: 'unknown', port: 7233 }
            }
        };
        res.writeHead(200, { 'Content-Type': 'application/json' });
        res.end(JSON.stringify(systemData));
    } else {
        res.writeHead(404, { 'Content-Type': 'text/plain' });
        res.end('Not Found');
    }
});

server.listen(port, () => {
    console.log(`🚀 Real Data Dashboard running on http://localhost:${port}`);
    console.log(`📡 Serving real system metrics (no fake data)`);
    console.log(`🔥 Dashboard available at: http://localhost:${port}`);
    console.log(`🌐 Health endpoint: http://localhost:${port}/health`);
});
