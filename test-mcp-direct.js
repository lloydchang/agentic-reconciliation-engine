#!/usr/bin/env node

/**
 * Direct MCP Server Test - Shows how to communicate with MCP servers via stdin/stdout
 */

const { spawn } = require('child_process');
const path = require('path');

// Load environment variables
require('dotenv').config({ path: path.join(__dirname, '.env') });

async function testMCPServer() {
    const serverName = 'cloud-compliance';
    const serverPath = path.join(__dirname, '.claude', 'mcp-servers', serverName, 'index.js');

    console.log(`Testing ${serverName} MCP server directly...\n`);

    // Spawn the MCP server
    const serverProcess = spawn('node', [serverPath], {
        stdio: ['pipe', 'pipe', 'inherit'], // pipe stdin/stdout, inherit stderr
        env: { ...process.env }
    });

    let responseBuffer = '';
    let initialized = false;

    return new Promise((resolve) => {
        serverProcess.stdout.on('data', (data) => {
            const output = data.toString();
            console.log(`[SERVER OUTPUT]: ${output.trim()}`);

            if (output.includes('running on stdio')) {
                initialized = true;
                console.log('\n✅ Server initialized! Sending tools/list request...\n');

                // Send tools/list request
                const request = {
                    jsonrpc: '2.0',
                    id: 1,
                    method: 'tools/list',
                    params: {}
                };

                serverProcess.stdin.write(JSON.stringify(request) + '\n');
            }

            responseBuffer += output;

            // Try to parse JSON responses
            const lines = responseBuffer.split('\n');
            lines.forEach((line, index) => {
                if (line.trim() && line.includes('jsonrpc')) {
                    try {
                        const response = JSON.parse(line.trim());
                        console.log('\n📋 PARSED RESPONSE:');
                        console.log(JSON.stringify(response, null, 2));

                        if (response.result && response.result.tools) {
                            console.log('\n🔧 Available Tools:');
                            response.result.tools.forEach(tool => {
                                console.log(`  • ${tool.name}: ${tool.description}`);
                            });
                        }
                    } catch (e) {
                        console.log('Failed to parse response line:', line);
                    }
                }
            });
        });

        serverProcess.on('close', (code) => {
            console.log(`\n🔚 Server process exited with code ${code}`);
            resolve();
        });

        // Timeout after 10 seconds
        setTimeout(() => {
            console.log('\n⏰ Timeout reached, terminating server...');
            serverProcess.kill();
        }, 10000);
    });
}

async function main() {
    console.log('🔬 MCP Server Direct Communication Test');
    console.log('=====================================\n');

    console.log('This demonstrates how MCP servers work:');
    console.log('1. They start and wait for JSON-RPC requests on stdin');
    console.log('2. They send JSON-RPC responses to stdout');
    console.log('3. Claude Desktop manages this communication\n');

    await testMCPServer();

    console.log('\n📚 Summary:');
    console.log('• MCP servers can run standalone');
    console.log('• They communicate via JSON-RPC over stdin/stdout');
    console.log('• Claude Desktop acts as the MCP client');
    console.log('• You can build your own MCP clients (like the HTTP wrapper)');
    console.log('\nTo run manually: echo \'{"jsonrpc":"2.0","id":1,"method":"tools/list","params":{}}\' | node .claude/mcp-servers/cloud-compliance/index.js');
}

main().catch(console.error);
