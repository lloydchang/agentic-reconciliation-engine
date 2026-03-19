#!/usr/bin/env node

/**
 * Test script to run MCP servers in standalone mode
 * This demonstrates how to run MCP servers outside of Claude Desktop
 */

const { spawn } = require('child_process');
const path = require('path');

// Configuration
const MCP_SERVERS_DIR = path.join(__dirname, '.claude', 'mcp-servers');
const ENV_FILE = path.join(__dirname, '.env');

// Load environment variables
require('dotenv').config({ path: ENV_FILE });

async function testMCPServer(serverName) {
    console.log(`\n=== Testing ${serverName} MCP Server ===`);
    
    const serverPath = path.join(MCP_SERVERS_DIR, serverName, 'index.js');
    
    // Create a test request
    const testRequest = {
        jsonrpc: '2.0',
        id: 1,
        method: 'tools/list',
        params: {}
    };
    
    return new Promise((resolve, reject) => {
        // Spawn the MCP server process
        const serverProcess = spawn('node', [serverPath], {
            stdio: ['pipe', 'pipe', 'pipe'],
            env: { ...process.env }
        });
        
        let response = '';
        let errorOutput = '';
        
        serverProcess.stdout.on('data', (data) => {
            response += data.toString();
        });
        
        serverProcess.stderr.on('data', (data) => {
            errorOutput += data.toString();
        });
        
        serverProcess.on('close', (code) => {
            if (code === 0) {
                console.log(`✅ ${serverName} server started successfully`);
                console.log('Available tools:');
                
                try {
                    const responses = response.split('\n').filter(line => line.trim());
                    responses.forEach(resp => {
                        if (resp.trim()) {
                            const parsed = JSON.parse(resp);
                            if (parsed.result && parsed.result.tools) {
                                parsed.result.tools.forEach(tool => {
                                    console.log(`  - ${tool.name}: ${tool.description}`);
                                });
                            }
                        }
                    });
                } catch (e) {
                    console.log('Raw response:', response);
                }
            } else {
                console.error(`❌ ${serverName} server exited with code ${code}`);
                if (errorOutput) {
                    console.error('Error output:', errorOutput);
                }
            }
            resolve({ serverName, success: code === 0, response, error: errorOutput });
        });
        
        // Send test request
        serverProcess.stdin.write(JSON.stringify(testRequest) + '\n');
        
        // Close stdin after a short delay to trigger server response
        setTimeout(() => {
            serverProcess.stdin.end();
        }, 1000);
    });
}

async function main() {
    console.log('MCP Server Standalone Test');
    console.log('============================\n');
    
    const servers = ['cloud-compliance', 'incident-triage', 'iac-validator', 'knowledge-base', 'engagement-sync'];
    
    for (const server of servers) {
        await testMCPServer(server);
        
        // Wait a bit between servers
        await new Promise(resolve => setTimeout(resolve, 500));
    }
    
    console.log('\n=== Test Complete ===');
    console.log('To run servers manually:');
    console.log('1. Set environment variables in .env file');
    console.log('2. Run: node .claude/mcp-servers/[server-name]/index.js');
    console.log('3. Send JSON-RPC requests via stdin');
}

// Check if dotenv is available, install if not
try {
    require('dotenv');
} catch (e) {
    console.log('Installing dotenv package...');
    const { execSync } = require('child_process');
    execSync('npm install dotenv', { stdio: 'inherit' });
}

main().catch(console.error);
