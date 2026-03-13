import React, { useState, useEffect, useRef, useCallback } from 'react';
import {
  Content,
  Header,
  Page,
} from '@backstage/core-components';
import {
  Button,
  Grid,
  Paper,
  Typography,
  Box,
  Tabs,
  Tab,
  TextField,
  Chip,
  Card,
  CardContent,
  CardActions,
  List,
  ListItem,
  ListItemText,
  Accordion,
  AccordionSummary,
  AccordionDetails,
  LinearProgress,
  MenuItem,
} from '@mui/material';
import {
  PlayArrow,
  Stop,
  Settings,
  Storage,
  Timeline,
  ErrorOutline,
  ExpandMore,
  CheckCircle,
  Error,
  Schedule,
  Assessment,
  Security,
  AttachMoney,
  Info,
} from '@mui/icons-material';

  const [activeTab, setActiveTab] = useState(0);

  const handleTabChange = (_event: React.SyntheticEvent, newValue: number) => {
    setActiveTab(newValue);
  };

interface MCPTool {
  name: string;
  description: string;
  inputSchema: any;
}

interface MCPResource {
  name: string;
  description: string;
  uri: string;
  mimeType: string;
}

interface MCPMessage {
  type: string;
  sessionId?: string;
  requestId?: string;
  method?: string;
  params?: any;
  result?: any;
  error?: {
    code: number;
    message: string;
    data?: any;
  };
}

const WebMCPClient: React.FC<WebMCPClientProps> = ({ serverUrl = 'ws://localhost:8082/webmcp' }) => {
  const [isConnected, setIsConnected] = useState(false);
  const [clientId, setClientId] = useState<string>('');
  const [sessionId, setSessionId] = useState<string>('');
  const [tools, setTools] = useState<MCPTool[]>([]);
  const [resources, setResources] = useState<MCPResource[]>([]);
  const [logs, setLogs] = useState<string[]>([]);
  const [selectedTool, setSelectedTool] = useState<MCPTool | null>(null);
  const [toolParams, setToolParams] = useState<Record<string, any>>({});
  const [toolResult, setToolResult] = useState<any>(null);
  const [isLoading, setIsLoading] = useState(false);

  const wsRef = useRef<WebSocket | null>(null);
  const requestIdRef = useRef(1);

  const addLog = useCallback((message: string) => {
    setLogs(prev => [...prev.slice(-99), `${new Date().toISOString()}: ${message}`]);
  }, []);

  const connectWebSocket = useCallback(() => {
    if (wsRef.current) {
      wsRef.current.close();
    }

    addLog(`Connecting to ${serverUrl}...`);
    const ws = new WebSocket(serverUrl);
    wsRef.current = ws;

    ws.onopen = () => {
      setIsConnected(true);
      addLog('Connected to WebMCP server');

      // Send initialize message
      const initMessage: MCPMessage = {
        type: 'initialize',
        requestId: requestIdRef.current.toString(),
        params: {
          protocolVersion: '2024-11-05',
          capabilities: {},
          clientInfo: {
            name: 'Temporal AI Agents Web Client',
            version: '1.0.0'
          }
        }
      };
      requestIdRef.current++;
      ws.send(JSON.stringify(initMessage));
    };

    ws.onmessage = (event) => {
      try {
        const message: MCPMessage = JSON.parse(event.data);
        addLog(`Received: ${message.type}`);

        switch (message.type) {
          case 'welcome':
            if (message.result) {
              setClientId(message.result.clientId);
              setSessionId(message.result.sessionId || '');
              addLog(`Welcome! Client ID: ${message.result.clientId}`);
            }
            break;

          case 'response':
            if (message.result) {
              if (message.result.tools) {
                setTools(message.result.tools);
                addLog(`Loaded ${message.result.tools.length} tools`);
              } else if (message.result.resources) {
                setResources(message.result.resources);
                addLog(`Loaded ${message.result.resources.length} resources`);
              } else if (message.result.contents) {
                // Resource read result
                setToolResult(message.result);
              } else {
                // Tool execution result
                setToolResult(message.result);
              }
            }
            if (message.error) {
              addLog(`Error: ${message.error.message}`);
            }
            setIsLoading(false);
            break;
        }
      } catch (error) {
        addLog(`Failed to parse message: ${error}`);
      }
    };

    ws.onclose = () => {
      setIsConnected(false);
      setClientId('');
      setSessionId('');
      addLog('Disconnected from WebMCP server');
    };

    ws.onerror = (error) => {
      addLog(`WebSocket error: ${error}`);
    };
  }, [serverUrl, addLog]);

  const disconnectWebSocket = useCallback(() => {
    if (wsRef.current) {
      wsRef.current.close();
      wsRef.current = null;
    }
  }, []);

  const sendMessage = useCallback((message: MCPMessage) => {
    if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
      message.requestId = requestIdRef.current.toString();
      requestIdRef.current++;
      wsRef.current.send(JSON.stringify(message));
      addLog(`Sent: ${message.type}`);
    } else {
      addLog('WebSocket not connected');
    }
  }, [addLog]);

  const loadTools = useCallback(() => {
    sendMessage({ type: 'tools/list' });
  }, [sendMessage]);

  const loadResources = useCallback(() => {
    sendMessage({ type: 'resources/list' });
  }, [sendMessage]);

  const executeTool = useCallback(() => {
    if (!selectedTool) return;

    setIsLoading(true);
    setToolResult(null);

    sendMessage({
      type: 'tools/call',
      params: {
        name: selectedTool.name,
        arguments: toolParams
      }
    });
  }, [selectedTool, toolParams, sendMessage]);

  const readResource = useCallback((uri: string) => {
    setIsLoading(true);
    setToolResult(null);

    sendMessage({
      type: 'resources/read',
      params: { uri }
    });
  }, [sendMessage]);

  useEffect(() => {
    return () => {
      if (wsRef.current) {
        wsRef.current.close();
      }
    };
  }, []);

  const renderToolForm = () => {
    if (!selectedTool) return null;

    const schema = selectedTool.inputSchema;
    if (!schema?.properties) return null;

    return (
      <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
        <Typography variant="h6">{selectedTool.name}</Typography>
        <Typography variant="body2" color="textSecondary">{selectedTool.description}</Typography>

        {Object.entries(schema.properties).map(([key, prop]: [string, any]) => (
          <Box key={key} sx={{ display: 'flex', flexDirection: 'column', gap: 1 }}>
            <Typography variant="body2" sx={{ fontWeight: 'medium' }}>
              {key} {schema.required?.includes(key) && <span style={{ color: 'red' }}>*</span>}
            </Typography>
            {prop.type === 'string' && prop.enum ? (
              <TextField
                select
                fullWidth
                value={toolParams[key] || ''}
                onChange={(e) => setToolParams(prev => ({ ...prev, [key]: e.target.value }))}
              >
                <MenuItem value="">Select {key}</MenuItem>
                {prop.enum.map((option: string) => (
                  <MenuItem key={option} value={option}>{option}</MenuItem>
                ))}
              </TextField>
            ) : (
              <TextField
                fullWidth
                type={prop.type === 'number' ? 'number' : 'text'}
                placeholder={prop.description}
                value={toolParams[key] || ''}
                onChange={(e) => setToolParams(prev => ({ ...prev, [key]: e.target.value }))}
              />
            )}
            {prop.description && (
              <Typography variant="caption" color="textSecondary">{prop.description}</Typography>
            )}
          </Box>
        ))}

        <Button onClick={executeTool} disabled={isLoading} variant="contained" fullWidth>
          {isLoading ? 'Executing...' : 'Execute Tool'}
        </Button>
      </Box>
    );
  };

  return (
    <Page themeId="tool">
      <Header title="WebMCP Client - Temporal AI Agents" />
      <Content>
        <Box sx={{ maxWidth: '6xl', mx: 'auto', p: 6, spaceY: 6 }}>
          <Card>
            <CardContent>
              <Typography variant="h5" gutterBottom sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
                <Settings />
                WebMCP Client - Temporal AI Agents
              </Typography>
              <Typography variant="body2" color="textSecondary">
                Browser-based interface for Model Context Protocol (MCP) interactions with AI agents
              </Typography>
            </CardContent>
            <CardActions>
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, mb: 4 }}>
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                  <Box
                    sx={{
                      width: 12,
                      height: 12,
                      borderRadius: '50%',
                      bgcolor: isConnected ? 'success.main' : 'error.main'
                    }}
                  />
                  <Typography variant="body2">
                    {isConnected ? 'Connected' : 'Disconnected'}
                    {clientId && ` (ID: ${clientId})`}
                  </Typography>
                </Box>

                {!isConnected ? (
                  <Button onClick={connectWebSocket} startIcon={<PlayArrow />}>
                    Connect
                  </Button>
                ) : (
                  <Button variant="outlined" onClick={disconnectWebSocket}>
                    Disconnect
                  </Button>
                )}
              </Box>

              {isConnected && (
                <Box sx={{ display: 'flex', gap: 1 }}>
                  <Button variant="outlined" size="small" onClick={loadTools}>
                    Load Tools
                  </Button>
                  <Button variant="outlined" size="small" onClick={loadResources}>
                    Load Resources
                  </Button>
                </Box>
              )}
            </CardActions>
          </Card>

          <Box sx={{ borderBottom: 1, borderColor: 'divider' }}>
            <Tabs value={activeTab} onChange={handleTabChange} sx={{ mb: 2 }}>
              <Tab icon={<Settings />} iconPosition="start" label={`Tools (${tools.length})`} />
              <Tab icon={<Database />} iconPosition="start" label={`Resources (${resources.length})`} />
              <Tab icon={<Activity />} iconPosition="start" label="Execution" />
              <Tab icon={<AlertCircle />} iconPosition="start" label="Logs" />
            </Tabs>
          </Box>

          {/* Tools Tab */}
          {activeTab === 0 && (
            <Box sx={{ p: 3 }}>
              <Card>
                <CardContent>
                  <Typography variant="h6">Available Tools</Typography>
                  <Typography variant="body2" color="textSecondary">
                    AI agent tools that can be executed via MCP
                  </Typography>
                </CardContent>
                <CardContent>
                  <Grid container spacing={2}>
                    {tools.map((tool) => (
                      <Grid item xs={12} md={6} key={tool.name}>
                        <Card
                          sx={{
                            cursor: 'pointer',
                            border: selectedTool?.name === tool.name ? 2 : 1,
                            borderColor: selectedTool?.name === tool.name ? 'primary.main' : 'divider'
                          }}
                          onClick={() => setSelectedTool(tool)}
                        >
                          <CardContent>
                            <Typography variant="subtitle1">{tool.name}</Typography>
                            <Typography variant="body2" color="textSecondary">{tool.description}</Typography>
                          </CardContent>
                        </Card>
                      </Grid>
                    ))}
                  </Grid>
                </CardContent>
              </Card>
            </Box>
          )}

          {/* Resources Tab */}
          {activeTab === 1 && (
            <Box sx={{ p: 3 }}>
              <Card>
                <CardContent>
                  <Typography variant="h6">Available Resources</Typography>
                  <Typography variant="body2" color="textSecondary">
                    Data sources accessible via MCP
                  </Typography>
                </CardContent>
                <CardContent>
                  <Grid container spacing={2}>
                    {resources.map((resource) => (
                      <Grid item xs={12} md={6} key={resource.uri}>
                        <Card>
                          <CardContent>
                            <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
                              <Box>
                                <Typography variant="subtitle1">{resource.name}</Typography>
                                <Typography variant="body2" color="textSecondary">{resource.description}</Typography>
                              </Box>
                              <Button
                                size="small"
                                variant="outlined"
                                onClick={() => readResource(resource.uri)}
                                disabled={isLoading}
                              >
                                Read
                              </Button>
                            </Box>
                          </CardContent>
                          <CardActions>
                            <Chip label={resource.mimeType} size="small" />
                            <Typography variant="caption" color="textSecondary">{resource.uri}</Typography>
                          </CardActions>
                        </Card>
                      </Grid>
                    ))}
                  </Grid>
                </CardContent>
              </Card>
            </Box>
          )}

          {/* Execution Tab */}
          {activeTab === 2 && (
            <Box sx={{ p: 3 }}>
              <Card>
                <CardContent>
                  <Typography variant="h6">Tool Execution</Typography>
                  <Typography variant="body2" color="textSecondary">
                    Execute selected tools with custom parameters
                  </Typography>
                </CardContent>
                <CardContent>
                  {selectedTool ? (
                    <Box sx={{ display: 'flex', flexDirection: 'column', gap: 3 }}>
                      {renderToolForm()}

                      {toolResult && (
                        <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
                          <Typography variant="subtitle1">Result:</Typography>
                          <TextField
                            multiline
                            fullWidth
                            minRows={4}
                            value={JSON.stringify(toolResult, null, 2)}
                            InputProps={{ readOnly: true }}
                            sx={{ fontFamily: 'monospace', fontSize: '0.875rem' }}
                          />
                        </Box>
                      )}
                    </Box>
                  ) : (
                    <Typography variant="body2" color="textSecondary">
                      Select a tool from the Tools tab to execute it.
                    </Typography>
                  )}
                </CardContent>
              </Card>
            </Box>
          )}

          {/* Logs Tab */}
          {activeTab === 3 && (
            <Box sx={{ p: 3 }}>
              <Card>
                <CardContent>
                  <Typography variant="h6">Activity Logs</Typography>
                  <Typography variant="body2" color="textSecondary">
                    Real-time logging of MCP interactions
                  </Typography>
                </CardContent>
                <CardContent>
                  <Box sx={{ height: 400, overflow: 'auto', fontFamily: 'monospace', fontSize: '0.875rem' }}>
                    {logs.map((log, index) => (
                      <Box key={index} sx={{ color: 'text.secondary', mb: 1 }}>
                        {log}
                      </Box>
                    ))}
                  </Box>
                </CardContent>
              </Card>
            </Box>
          )}
        </Box>
      </Content>
    </Page>
  );
};

export default WebMCPClient;
