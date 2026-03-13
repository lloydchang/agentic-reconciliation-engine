import React, { useState, useEffect } from 'react';
import {
  Box,
  Card,
  CardContent,
  Typography,
  Grid,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Paper,
  Chip,
  Button,
  Alert,
  CircularProgress,
  LinearProgress,
  Tabs,
  Tab,
  Accordion,
  AccordionSummary,
  AccordionDetails,
} from '@mui/material';
import {
  Refresh,
  CheckCircle,
  Error,
  Schedule,
  PlayArrow,
  ExpandMore,
  Security,
  Gavel,
  Savings,
  People,
  Assessment,
} from '@mui/icons-material';

interface WorkflowExecution {
  id: string;
  type: string;
  status: 'Running' | 'Completed' | 'Failed' | 'Canceled';
  startTime: string;
  endTime?: string;
  duration?: string;
  progress?: number;
  currentStep?: string;
  agentResults?: AgentResult[];
}

interface AgentResult {
  agentId: string;
  agentType: string;
  status: string;
  score: number;
  findings: string[];
  executedAt: string;
}

interface InfrastructureResource {
  id: string;
  type: string;
  name: string;
  region: string;
  status: string;
  metrics: {
    cpuUtilization: number;
    memoryUtilization: number;
    diskUtilization: number;
  };
}

interface TabPanelProps {
  children?: React.ReactNode;
  index: number;
  value: number;
}

const TabPanel: React.FC<TabPanelProps> = ({ children, value, index }) => (
  <div hidden={value !== index}>
    {value === index && <Box sx={{ p: 3 }}>{children}</Box>}
  </div>
);

const MonitoringDashboard: React.FC = () => {
  const [tabValue, setTabValue] = useState(0);
  const [workflows, setWorkflows] = useState<WorkflowExecution[]>([]);
  const [resources, setResources] = useState<InfrastructureResource[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetchData();
    const interval = setInterval(fetchData, 10000); // Refresh every 10 seconds
    return () => clearInterval(interval);
  }, []);

  const fetchData = async () => {
    setLoading(true);
    setError(null);

    try {
      // Fetch infrastructure resources
      const resourcesResponse = await fetch('http://localhost:8081/emulator/resources');
      if (resourcesResponse.ok) {
        const resourcesData = await resourcesResponse.json();
        setResources(resourcesData);
      }
    } catch (err) {
      console.error('Error fetching data:', err);
      setError('Failed to fetch monitoring data');
    } finally {
      setLoading(false);
    }
  };

  const handleTabChange = (event: React.SyntheticEvent, newValue: number) => {
    setTabValue(newValue);
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'Completed':
        return <CheckCircle color="success" />;
      case 'Failed':
        return <Error color="error" />;
      case 'Running':
        return <PlayArrow color="primary" />;
      default:
        return <Schedule color="action" />;
    }
  };

  const getStatusColor = (status: string): 'success' | 'error' | 'warning' | 'default' => {
    switch (status) {
      case 'Completed':
        return 'success';
      case 'Failed':
        return 'error';
      case 'Running':
        return 'warning';
      default:
        return 'default';
    }
  };

  const getAgentIcon = (agentType: string) => {
    switch (agentType) {
      case 'Security':
        return <Security />;
      case 'Compliance':
        return <Gavel />;
      case 'CostOptimization':
        return <Savings />;
      default:
        return <Assessment />;
    }
  };

  const getHealthScore = (resource: InfrastructureResource): number => {
    const { cpu, memory, disk } = resource.metrics;
    return ((100 - cpu) + (100 - memory) + (100 - disk)) / 3;
  };

  const formatDuration = (startTime: string, endTime?: string): string => {
    const start = new Date(startTime);
    const end = endTime ? new Date(endTime) : new Date();
    const duration = end.getTime() - start.getTime();
    
    const minutes = Math.floor(duration / 60000);
    const seconds = Math.floor((duration % 60000) / 1000);
    
    return `${minutes}m ${seconds}s`;
  };

  return (
    <Box sx={{ width: '100%' }}>
      <Typography variant="h4" gutterBottom>
        AI Agent Monitoring Dashboard
      </Typography>

      {error && (
        <Alert severity="error" sx={{ mb: 2 }}>
          {error}
        </Alert>
      )}

      <Box sx={{ borderBottom: 1, borderColor: 'divider', mb: 3 }}>
        <Tabs value={tabValue} onChange={handleTabChange}>
          <Tab label="Workflow Executions" />
          <Tab label="Infrastructure Resources" />
          <Tab label="Agent Performance" />
        </Tabs>
      </Box>

      {/* Workflow Executions Tab */}
      <TabPanel value={tabValue} index={0}>
        <Box display="flex" justifyContent="space-between" alignItems="center" mb={2}>
          <Typography variant="h6">Active Workflow Executions</Typography>
          <Button
            variant="outlined"
            startIcon={<Refresh />}
            onClick={fetchData}
            disabled={loading}
          >
            Refresh
          </Button>
        </Box>

        {loading ? (
          <Box display="flex" justifyContent="center" p={4}>
            <CircularProgress />
          </Box>
        ) : (
          <TableContainer component={Paper}>
            <Table>
              <TableHead>
                <TableRow>
                  <TableCell>Workflow ID</TableCell>
                  <TableCell>Type</TableCell>
                  <TableCell>Status</TableCell>
                  <TableCell>Progress</TableCell>
                  <TableCell>Duration</TableCell>
                  <TableCell>Actions</TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {workflows.map((workflow) => (
                  <TableRow key={workflow.id}>
                    <TableCell>{workflow.id}</TableCell>
                    <TableCell>{workflow.type}</TableCell>
                    <TableCell>
                      <Box display="flex" alignItems="center">
                        {getStatusIcon(workflow.status)}
                        <Chip
                          label={workflow.status}
                          color={getStatusColor(workflow.status)}
                          size="small"
                          sx={{ ml: 1 }}
                        />
                      </Box>
                    </TableCell>
                    <TableCell>
                      {workflow.progress !== undefined && (
                        <Box sx={{ display: 'flex', alignItems: 'center' }}>
                          <LinearProgress
                            variant="determinate"
                            value={workflow.progress}
                            sx={{ width: '100px', mr: 1 }}
                          />
                          <Typography variant="body2">
                            {workflow.progress}%
                          </Typography>
                        </Box>
                      )}
                    </TableCell>
                    <TableCell>{workflow.duration}</TableCell>
                    <TableCell>
                      <Button size="small" variant="outlined">
                        View Details
                      </Button>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </TableContainer>
        )}
      </TabPanel>

      {/* Infrastructure Resources Tab */}
      <TabPanel value={tabValue} index={1}>
        <Box display="flex" justifyContent="space-between" alignItems="center" mb={2}>
          <Typography variant="h6">Infrastructure Resources</Typography>
          <Button
            variant="outlined"
            startIcon={<Refresh />}
            onClick={fetchData}
            disabled={loading}
          >
            Refresh
          </Button>
        </Box>

        <Grid container spacing={3}>
          {resources.map((resource) => (
            <Grid item xs={12} md={6} lg={4} key={resource.id}>
              <Card>
                <CardContent>
                  <Typography variant="h6" gutterBottom>
                    {resource.name}
                  </Typography>
                  <Chip
                    label={resource.type}
                    color="primary"
                    size="small"
                    sx={{ mb: 1 }}
                  />
                  <Chip
                    label={resource.status}
                    color={resource.status === 'Running' ? 'success' : 'default'}
                    size="small"
                    sx={{ mb: 2 }}
                  />
                  
                  <Typography variant="body2" color="text.secondary" gutterBottom>
                    Region: {resource.region}
                  </Typography>
                  
                  <Typography variant="subtitle2" gutterBottom>
                    Resource Metrics
                  </Typography>
                  <Box sx={{ mb: 1 }}>
                    <Typography variant="body2">
                      CPU: {resource.metrics.cpuUtilization.toFixed(1)}%
                    </Typography>
                    <LinearProgress
                      variant="determinate"
                      value={resource.metrics.cpuUtilization}
                      sx={{ mb: 1 }}
                    />
                  </Box>
                  <Box sx={{ mb: 1 }}>
                    <Typography variant="body2">
                      Memory: {resource.metrics.memoryUtilization.toFixed(1)}%
                    </Typography>
                    <LinearProgress
                      variant="determinate"
                      value={resource.metrics.memoryUtilization}
                      sx={{ mb: 1 }}
                    />
                  </Box>
                  <Box sx={{ mb: 2 }}>
                    <Typography variant="body2">
                      Disk: {resource.metrics.diskUtilization.toFixed(1)}%
                    </Typography>
                    <LinearProgress
                      variant="determinate"
                      value={resource.metrics.diskUtilization}
                    />
                  </Box>
                  
                  <Typography variant="body2" color="primary">
                    Health Score: {getHealthScore(resource).toFixed(1)}%
                  </Typography>
                </CardContent>
              </Card>
            </Grid>
          ))}
        </Grid>
      </TabPanel>

      {/* Agent Performance Tab */}
      <TabPanel value={tabValue} index={2}>
        <Typography variant="h6" gutterBottom>
          Agent Performance Metrics
        </Typography>

        {workflows
          .filter(w => w.agentResults && w.agentResults.length > 0)
          .map((workflow) => (
            <Accordion key={workflow.id} sx={{ mb: 2 }}>
              <AccordionSummary expandIcon={<ExpandMore />}>
                <Box sx={{ display: 'flex', alignItems: 'center', width: '100%' }}>
                  <Typography variant="subtitle1" sx={{ flexGrow: 1 }}>
                    {workflow.id}
                  </Typography>
                  <Chip
                    label={workflow.status}
                    color={getStatusColor(workflow.status)}
                    size="small"
                  />
                </Box>
              </AccordionSummary>
              <AccordionDetails>
                <Grid container spacing={2}>
                  {workflow.agentResults?.map((agent) => (
                    <Grid item xs={12} md={6} key={agent.agentId}>
                      <Card variant="outlined">
                        <CardContent>
                          <Box display="flex" alignItems="center" mb={1}>
                            {getAgentIcon(agent.agentType)}
                            <Typography variant="subtitle2" sx={{ ml: 1 }}>
                              {agent.agentType} Agent
                            </Typography>
                          </Box>
                          
                          <Typography variant="body2" color="text.secondary" gutterBottom>
                            {agent.agentId}
                          </Typography>
                          
                          <Box sx={{ mb: 2 }}>
                            <Typography variant="body2">
                              Score: {agent.score.toFixed(1)}/100
                            </Typography>
                            <LinearProgress
                              variant="determinate"
                              value={agent.score}
                              color={agent.score >= 80 ? 'success' : agent.score >= 60 ? 'warning' : 'error'}
                            />
                          </Box>
                          
                          <Typography variant="subtitle2" gutterBottom>
                            Findings:
                          </Typography>
                          {agent.findings.map((finding, index) => (
                            <Typography key={index} variant="body2" sx={{ ml: 2 }}>
                              • {finding}
                            </Typography>
                          ))}
                        </CardContent>
                      </Card>
                    </Grid>
                  ))}
                </Grid>
              </AccordionDetails>
            </Accordion>
          ))}
      </TabPanel>
    </Box>
  );
};

export default MonitoringDashboard;
