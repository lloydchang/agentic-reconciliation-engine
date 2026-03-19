const http = require('http');
const fs = require('fs');
const path = require('path');

const port = 8080;

const server = http.createServer((req, res) => {
    if (req.url === '/') {
        // Serve the redirect HTML
        try {
            const html = fs.readFileSync(path.join(__dirname, 'redirect.html'), 'utf8');
            res.writeHead(200, { 'Content-Type': 'text/html' });
            res.end(html);
        } catch (error) {
            res.writeHead(500, { 'Content-Type': 'text/plain' });
            res.end('Error loading redirect page');
        }
    } else {
        // Redirect all other requests to the real dashboard
        res.writeHead(302, { 'Location': 'http://localhost:8085' + req.url });
        res.end();
    }
});

server.listen(port, () => {
    console.log(`🔄 Redirect server running on http://localhost:${port}`);
    console.log(`📡 Redirecting to real dashboard at http://localhost:8085`);
});
