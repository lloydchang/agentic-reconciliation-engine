#!/usr/bin/env node

/**
 * HTTP Server Wrapper for MCP Servers
 * Allows running MCP servers via HTTP API instead of stdio
 */

const express = require('express');
const { spawn } = require('child_process');
const path = require('path');
const cors = require('cors');

// Configuration
const MCP_SERVERS_DIR = path.join(__dirname, '.claude', 'mcp-servers');
const ENV_FILE = path.join(__dirname, '.env');

// Load environment variables
require('dotenv').config({ path: ENV_FILE });

class MCPHTTPServer {
    constructor(serverName, port = 3000) {
        this.serverName = serverName;
        this.port = port;
        this.serverProcess = null;
        this.app = express();
        
        this.setupMiddleware();
        this.setupRoutes();
    }
    
    setupMiddleware() {
        this.app.use(cors());
        this.app.use(express.json());
        this.app.use((req, res, next) => {
            console.log(`${new Date().toISOString()} - ${req.method} ${req.path}`);
            next();
        });
    }
    
    setupRoutes() {
        // Health check
        this.app.get('/health', (req, res) => {
            res.json({
                status: 'ok',
                server: this.serverName,
                timestamp: new Date().toISOString()
            });
        });
        
        // List tools
        this.app.get('/tools', async (req, res) => {
            try {
                const tools = await this.sendRequest('tools/list', {});
                res.json(tools);
            } catch (error) {
                res.status(500).json({ error: error.message });
            }
        });
        
        // Call tool
        this.app.post('/tools/:toolName', async (req, res) => {
            try {
                const { toolName } = req.params;
                const { arguments: args = {} } = req.body;
                
                const result = await this.sendRequest('tools/call', {
                    name: toolName,
                    arguments: args
                });
                res.json(result);
            } catch (error) {
                res.status(500).json({ error: error.message });
            }
        });
        
        // Generic MCP endpoint
        this.app.post('/mcp', async (req, res) => {
            try {
                const { method, params = {} } = req.body;
                const result = await this.sendRequest(method, params);
                res.json(result);
            } catch (error) {
                res.status(500).json({ error: error.message });
            }
        });
    }
    
    async startServer() {
        const serverPath = path.join(MCP_SERVERS_DIR, this.serverName, 'index.js');
        
        console.log(`Starting ${this.serverName} MCP server...`);
        
        // Spawn the MCP server process
        this.serverProcess = spawn('node', [serverPath], {
            stdio: ['pipe', 'pipe', 'pipe'],
            env: { ...process.env }
        });
        
        let responseBuffer = '';
        let isInitialized = false;
        
        this.serverProcess.stdout.on('data', (data) => {
            const output = data.toString();
            console.log(`[${this.serverName}] Raw output:`, output);
            
            responseBuffer += output;
            
            // Check for initialization message
            if (output.includes('running on stdio') && !isInitialized) {
                console.log(`[${this.serverName}] Server initialized successfully`);
                isInitialized = true;
                return;
            }
            
            // Try to parse complete JSON responses
            const lines = responseBuffer.split('\n');
            for (let i = 0; i < lines.length - 1; i++) {
                const line = lines[i].trim();
                if (line && line.startsWith('{')) {
                    try {
                        const response = JSON.parse(line);
                        this.handleResponse(response);
                    } catch (e) {
                        console.log(`[${this.serverName}] Failed to parse line: ${line}`);
                    }
                }
            }
            responseBuffer = lines[lines.length - 1];
        });
        
        this.serverProcess.stderr.on('data', (data) => {
            const error = data.toString();
            console.error(`[${this.serverName}] Error:`, error);
        });
        
        this.serverProcess.on('close', (code) => {
            console.log(`[${this.serverName}] Process exited with code ${code}`);
        });
        
        // Wait for server to initialize
        await new Promise((resolve) => {
            const checkInterval = setInterval(() => {
                if (isInitialized) {
                    clearInterval(checkInterval);
                    resolve();
                }
            }, 100);
        });
        
        // Start HTTP server
        this.app.listen(this.port, () => {
            console.log(`\n🚀 ${this.serverName} MCP HTTP Server running on port ${this.port}`);
            console.log(`📖 API Documentation:`);
            console.log(`   GET  http://localhost:${this.port}/health - Health check`);
            console.log(`   GET  http://localhost:${this.port}/tools - List available tools`);
            console.log(`   POST http://localhost:${this.port}/tools/:toolName - Call specific tool`);
            console.log(`   POST http://localhost:${this.port}/mcp - Generic MCP endpoint`);
            console.log(`\n💡 Example usage:`);
            console.log(`   curl http://localhost:${this.port}/tools`);
            console.log(`   curl -X POST http://localhost:${this.port}/tools/aws_security_hub_analysis \\`);
            console.log(`                -H "Content-Type: application/json" \\`);
            console.log(`                -d '{"region": "us-east-1", "severity": "HIGH"}'`);
        });
    }
    
    async sendRequest(method, params) {
        return new Promise((resolve, reject) => {
            const requestId = Date.now();
            const request = {
                jsonrpc: '2.0',
                id: requestId,
                method,
                params
            };
            
            // Store the promise for this request
            this.pendingRequests = this.pendingRequests || {};
            this.pendingRequests[requestId] = { resolve, reject };
            
            console.log(`[${this.serverName}] Sending request:`, JSON.stringify(request, null, 2));
            
            // Send request to MCP server
            this.serverProcess.stdin.write(JSON.stringify(request) + '\n');
            
            // Timeout after 30 seconds
            setTimeout(() => {
                if (this.pendingRequests[requestId]) {
                    delete this.pendingRequests[requestId];
                    reject(new Error('Request timeout'));
                }
            }, 30000);
        });
    }
    
    handleResponse(response) {
        console.log(`[${this.serverName}] Received response:`, JSON.stringify(response, null, 2));
        
        if (response.id && this.pendingRequests && this.pendingRequests[response.id]) {
            const { resolve, reject } = this.pendingRequests[response.id];
            delete this.pendingRequests[response.id];
            
            if (response.error) {
                reject(new Error(response.error.message || 'Unknown error'));
            } else {
                resolve(response.result);
            }
        }
    }
}

// Command line interface
async function main() {
    const args = process.argv.slice(2);
    
    if (args.length === 0) {
        console.log('Usage: node run-mcp-http.js <server-name> [port]');
        console.log('');
        console.log('Available servers:');
        console.log('  cloud-compliance');
        console.log('  incident-triage');
        console.log('  iac-validator');
        console.log('  knowledge-base');
        console.log('  engagement-sync');
        console.log('');
        console.log('Example:');
        console.log('  node run-mcp-http.js cloud-compliance 3001');
        process.exit(1);
    }
    
    const serverName = args[0];
    const port = parseInt(args[1]) || 3000;
    
    // Check required packages
    try {
        require('express');
        require('cors');
    } catch (e) {
        console.log('Installing required packages...');
        const { execSync } = require('child_process');
        execSync('npm install express cors', { stdio: 'inherit' });
    }
    
    // Start the HTTP wrapper
    const httpServer = new MCPHTTPServer(serverName, port);
    await httpServer.startServer();
}

if (require.main === module) {
    main().catch(console.error);
}

module.exports = MCPHTTPServer;
