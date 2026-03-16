import React, { useState, useEffect } from 'react';
import {
  Container, Paper, Typography, Grid, Card, CardContent,
  Box, Chip, LinearProgress, Alert, Button, IconButton,
  Dialog, DialogTitle, DialogContent, DialogActions, Tabs, Tab
} from '@mui/material';
import {
  Refresh as RefreshIcon,
  Memory as MemoryIcon,
  Timeline as TimelineIcon,
  BugReport as BugReportIcon,
  TrendingUp as TrendingUpIcon,
  Error as ErrorIcon,
  CheckCircle as CheckCircleIcon
} from '@mui/icons-material';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, BarChart, Bar } from 'recharts';
import axios from 'axios';

interface Agent {
  name: string;
  status: 'active' | 'idle' | 'error';
  language: string;
  skills: string[];
  currentActivity: string;
  cpu: number;
  memory: number;
  uptime: string;
}

interface Metrics {
  agent_count: number;
  skills_executed: number;
  errors_last_24h: number;
  avg_response_time: number;
  temporal_workflows_active: number;
  memory_usage_mb: number;
}

interface TabPanelProps {
  children?: React.ReactNode;
  index: number;
  value: number;
}

function TabPanel(props: TabPanelProps) {
  const { children, value, index, ...other } = props;

  return (
    <div
      role="tabpanel"
      hidden={value !== index}
      id={`dashboard-tabpanel-${index}`}
      aria-labelledby={`dashboard-tab-${index}`}
      {...other}
    >
      {value === index && <Box sx={{ p: 3 }}>{children}</Box>}
    </div>
  );
}

function Dashboard() {
  const [agents, setAgents] = useState<Agent[]>([]);
  const [metrics, setMetrics] = useState<Metrics | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [tabValue, setTabValue] = useState(0);
  const [debugDialog, setDebugDialog] = useState(false);

  const fetchData = async () => {
    try {
      setLoading(true);
      const [agentsResponse, metricsResponse] = await Promise.all([
        axios.get('/api/agents/detailed'),
        axios.get('/api/metrics/real-time')
      ]);

      setAgents(agentsResponse.data);
      setMetrics(metricsResponse.data);
      setError(null);
    } catch (err) {
      setError('Failed to fetch dashboard data');
      console.error('Dashboard fetch error:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
    const interval = setInterval(fetchData, 30000); // Update every 30 seconds
    return () => clearInterval(interval);
  }, []);

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'active': return 'success';
      case 'idle': return 'info';
      case 'error': return 'error';
      default: return 'default';
    }
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'active': return <CheckCircleIcon />;
      case 'error': return <ErrorIcon />;
      default: return <MemoryIcon />;
    }
  };

  const handleTabChange = (event: React.SyntheticEvent, newValue: number) => {
    setTabValue(newValue);
  };

  if (loading && !metrics) {
    return (
      <Container maxWidth="lg" sx={{ mt: 4, mb: 4 }}>
        <Box display="flex" justifyContent="center" alignItems="center" minHeight="400px">
          <LinearProgress sx={{ width: '50%' }} />
        </Box>
      </Container>
    );
  }

  return (
    <Container maxWidth="xl" sx={{ mt: 4, mb: 4 }}>
      {/* Header */}
      <Paper sx={{ p: 3, mb: 3 }}>
        <Box display="flex" justifyContent="space-between" alignItems="center">
          <Typography variant="h4" component="h1" gutterBottom>
            🚀 Cloud AI Agents Dashboard
          </Typography>
          <Box>
            <IconButton onClick={() => setDebugDialog(true)} color="primary">
              <BugReportIcon />
            </IconButton>
            <Button
              variant="contained"
              startIcon={<RefreshIcon />}
              onClick={fetchData}
              disabled={loading}
            >
              Refresh
            </Button>
          </Box>
        </Box>
        {error && <Alert severity="error" sx={{ mt: 2 }}>{error}</Alert>}
      </Paper>

      {/* Key Metrics */}
      <Grid container spacing={3} sx={{ mb: 3 }}>
        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Typography color="textSecondary" gutterBottom>
                Active Agents
              </Typography>
              <Typography variant="h4" component="div">
                {metrics?.agent_count || 0}
              </Typography>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Typography color="textSecondary" gutterBottom>
                Skills Executed (24h)
              </Typography>
              <Typography variant="h4" component="div">
                {metrics?.skills_executed || 0}
              </Typography>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Typography color="textSecondary" gutterBottom>
                Avg Response Time
              </Typography>
              <Typography variant="h4" component="div">
                {metrics?.avg_response_time || 0}ms
              </Typography>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Typography color="textSecondary" gutterBottom>
                Active Workflows
              </Typography>
              <Typography variant="h4" component="div">
                {metrics?.temporal_workflows_active || 0}
              </Typography>
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      {/* Tabs */}
      <Paper sx={{ width: '100%' }}>
        <Box sx={{ borderBottom: 1, borderColor: 'divider' }}>
          <Tabs value={tabValue} onChange={handleTabChange} aria-label="dashboard tabs">
            <Tab label="Agent Overview" />
            <Tab label="Performance Metrics" />
            <Tab label="System Health" />
          </Tabs>
        </Box>

        {/* Agent Overview Tab */}
        <TabPanel value={tabValue} index={0}>
          <Grid container spacing={3}>
            {agents.map((agent, index) => (
              <Grid item xs={12} md={6} lg={4} key={index}>
                <Card>
                  <CardContent>
                    <Box display="flex" justifyContent="space-between" alignItems="center" mb={2}>
                      <Typography variant="h6" component="div">
                        {agent.name}
                      </Typography>
                      <Chip
                        icon={getStatusIcon(agent.status)}
                        label={agent.status}
                        color={getStatusColor(agent.status) as any}
                        size="small"
                      />
                    </Box>

                    <Typography color="textSecondary" gutterBottom>
                      Language: {agent.language}
                    </Typography>

                    <Typography variant="body2" sx={{ mb: 2 }}>
                      Current Activity: {agent.currentActivity}
                    </Typography>

                    <Box sx={{ mb: 2 }}>
                      <Typography variant="body2" color="textSecondary" gutterBottom>
                        Skills ({agent.skills.length}):
                      </Typography>
                      <Box display="flex" flexWrap="wrap" gap={0.5}>
                        {agent.skills.slice(0, 3).map((skill, skillIndex) => (
                          <Chip key={skillIndex} label={skill} size="small" variant="outlined" />
                        ))}
                        {agent.skills.length > 3 && (
                          <Chip label={`+${agent.skills.length - 3} more`} size="small" variant="outlined" />
                        )}
                      </Box>
                    </Box>

                    <Box sx={{ mb: 1 }}>
                      <Typography variant="body2" color="textSecondary">
                        CPU: {agent.cpu}% | Memory: {agent.memory}MB
                      </Typography>
                      <Typography variant="body2" color="textSecondary">
                        Uptime: {agent.uptime}
                      </Typography>
                    </Box>
                  </CardContent>
                </Card>
              </Grid>
            ))}
          </Grid>
        </TabPanel>

        {/* Performance Metrics Tab */}
        <TabPanel value={tabValue} index={1}>
          <Grid container spacing={3}>
            <Grid item xs={12} md={6}>
              <Card>
                <CardContent>
                  <Typography variant="h6" gutterBottom>
                    CPU Usage Trend
                  </Typography>
                  <ResponsiveContainer width="100%" height={300}>
                    <LineChart data={[]}>
                      <CartesianGrid strokeDasharray="3 3" />
                      <XAxis dataKey="time" />
                      <YAxis />
                      <Tooltip />
                      <Line type="monotone" dataKey="cpu" stroke="#8884d8" strokeWidth={2} />
                    </LineChart>
                  </ResponsiveContainer>
                </CardContent>
              </Card>
            </Grid>
            <Grid item xs={12} md={6}>
              <Card>
                <CardContent>
                  <Typography variant="h6" gutterBottom>
                    Skill Execution Frequency
                  </Typography>
                  <ResponsiveContainer width="100%" height={300}>
                    <BarChart data={[]}>
                      <CartesianGrid strokeDasharray="3 3" />
                      <XAxis dataKey="skill" />
                      <YAxis />
                      <Tooltip />
                      <Bar dataKey="count" fill="#82ca9d" />
                    </BarChart>
                  </ResponsiveContainer>
                </CardContent>
              </Card>
            </Grid>
          </Grid>
        </TabPanel>

        {/* System Health Tab */}
        <TabPanel value={tabValue} index={2}>
          <Grid container spacing={3}>
            <Grid item xs={12} md={6}>
              <Card>
                <CardContent>
                  <Typography variant="h6" gutterBottom>
                    System Components
                  </Typography>
                  <Box sx={{ mb: 2 }}>
                    <Typography variant="body2">
                      Temporal Orchestration: <Chip label="Healthy" color="success" size="small" />
                    </Typography>
                  </Box>
                  <Box sx={{ mb: 2 }}>
                    <Typography variant="body2">
                      Memory Persistence: <Chip label="Active" color="success" size="small" />
                    </Typography>
                  </Box>
                  <Box sx={{ mb: 2 }}>
                    <Typography variant="body2">
                      AI Inference Gateway: <Chip label="Ready" color="info" size="small" />
                    </Typography>
                  </Box>
                </CardContent>
              </Card>
            </Grid>
            <Grid item xs={12} md={6}>
              <Card>
                <CardContent>
                  <Typography variant="h6" gutterBottom>
                    Error Summary (Last 24h)
                  </Typography>
                  <Typography variant="h4" color="error">
                    {metrics?.errors_last_24h || 0}
                  </Typography>
                  <Typography variant="body2" color="textSecondary">
                    Errors requiring attention
                  </Typography>
                </CardContent>
              </Card>
            </Grid>
          </Grid>
        </TabPanel>
      </Paper>

      {/* Debug Dialog */}
      <Dialog open={debugDialog} onClose={() => setDebugDialog(false)} maxWidth="md" fullWidth>
        <DialogTitle>Debug Tools</DialogTitle>
        <DialogContent>
          <Typography variant="body1" gutterBottom>
            Quick debugging commands for AI agents ecosystem:
          </Typography>
          <Box component="pre" sx={{ bgcolor: 'grey.100', p: 2, borderRadius: 1, fontSize: '0.875rem' }}>
{`# Fast agent debugging
./quick_debug.sh agents errors true

# Full system analysis  
python main.py debug --target-component all --issue-type performance --time-range 2h --auto-fix

# Infrastructure health check
kubectl get pods -n temporal -l app=temporal-worker
kubectl logs -n temporal deployment/temporal-worker --since=1h | grep ERROR`}
          </Box>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setDebugDialog(false)}>Close</Button>
        </DialogActions>
      </Dialog>
    </Container>
  );
}

export default Dashboard;
