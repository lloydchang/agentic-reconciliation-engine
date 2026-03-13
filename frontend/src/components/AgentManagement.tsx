import React, { useState, useEffect, useCallback } from 'react';
import {
  Button,
  Grid,
  Chip,
  Typography,
  Box,
  LinearProgress,
  Alert,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  TextField,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Accordion,
  AccordionSummary,
  AccordionDetails,
  List,
  ListItem,
  ListItemText,
  ListItemSecondaryAction,
  IconButton,
  Tooltip,
  Card,
  CardContent,
  CardHeader,
} from '@mui/material';
import {
  PlayArrow,
  Stop,
  Refresh,
  Assessment,
  Security,
  AttachMoney,
  ExpandMore,
  Info,
  CheckCircle,
  Error,
  Schedule,
} from '@mui/icons-material';
import { useApi } from '@backstage/core-plugin-api';
import { configApiRef } from '@backstage/core-plugin-api';

interface AgentManagementProps {
  onWorkflowStart?: (workflowId: string) => void;
}

interface Workflow {
  id: string;
  type: string;
  status: 'running' | 'completed' | 'failed' | 'pending';
  targetResource: string;
  startedAt: string;
  completedAt?: string;
  result?: any;
  error?: string;
}

interface AgentStats {
  totalAgents: number;
  activeAgents: number;
  completedTasks: number;
  failedTasks: number;
  averageExecutionTime: number;
}

interface ComplianceResult {
  score: number;
  issues: number;
  recommendations: string[];
  approved: boolean;
}

const AgentManagement: React.FC<AgentManagementProps> = ({ onWorkflowStart }) => {
  const [workflows, setWorkflows] = useState<Workflow[]>([]);
  const [stats, setStats] = useState<AgentStats | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [startDialogOpen, setStartDialogOpen] = useState(false);
  const [selectedWorkflowType, setSelectedWorkflowType] = useState('');
  const [targetResource, setTargetResource] = useState('');
  const [priority, setPriority] = useState('normal');
  const [expandedWorkflow, setExpandedWorkflow] = useState<string | null>(null);

  const config = useApi(configApiRef);
  const backendUrl = config.getOptionalString('temporal.backendUrl') || 'http://localhost:8081';

  const fetchWorkflows = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);

      // In a real implementation, you'd call the backend API
      // For now, simulate some sample data
      const mockWorkflows: Workflow[] = [
        {
          id: 'wf-compliance-001',
          type: 'compliance',
          status: 'completed',
          targetResource: 'vm-web-server-001',
          startedAt: new Date(Date.now() - 2 * 60 * 60 * 1000).toISOString(),
          completedAt: new Date(Date.now() - 1 * 60 * 60 * 1000).toISOString(),
          result: {
            score: 92.5,
            issues: 3,
            recommendations: [
              'Update SSL certificates',
              'Enable encryption at rest',
              'Review access permissions'
            ],
            approved: true
          }
        },
        {
          id: 'wf-security-002',
          type: 'security',
          status: 'running',
          targetResource: 'db-main-001',
          startedAt: new Date(Date.now() - 30 * 60 * 1000).toISOString(),
        },
        {
          id: 'wf-cost-003',
          type: 'cost-analysis',
          status: 'failed',
          targetResource: 'storage-backups-001',
          startedAt: new Date(Date.now() - 4 * 60 * 60 * 1000).toISOString(),
          completedAt: new Date(Date.now() - 3 * 60 * 60 * 1000).toISOString(),
          error: 'Analysis timeout - resource unavailable'
        }
      ];

      setWorkflows(mockWorkflows);

      const mockStats: AgentStats = {
        totalAgents: 3,
        activeAgents: 1,
        completedTasks: 45,
        failedTasks: 2,
        averageExecutionTime: 285
      };

      setStats(mockStats);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Failed to fetch workflows');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchWorkflows();
    // Set up periodic refresh
    const interval = setInterval(fetchWorkflows, 30000);
    return () => clearInterval(interval);
  }, [fetchWorkflows]);

  const handleStartWorkflow = async () => {
    if (!selectedWorkflowType || !targetResource) {
      setError('Please fill in all required fields');
      return;
    }

    try {
      setLoading(true);
      setError(null);

      // In a real implementation, make API call to backend
      const response = await fetch(`${backendUrl}/workflow/start-${selectedWorkflowType}`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          targetResource,
          priority,
          parameters: {}
        }),
      });

      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      }

      const result = await response.text();
      const workflowId = result.trim();

      // Add new workflow to the list
      const newWorkflow: Workflow = {
        id: workflowId,
        type: selectedWorkflowType,
        status: 'running',
        targetResource,
        startedAt: new Date().toISOString(),
      };

      setWorkflows(prev => [newWorkflow, ...prev]);

      // Notify parent component
      if (onWorkflowStart) {
        onWorkflowStart(workflowId);
      }

      // Close dialog
      setStartDialogOpen(false);
      setSelectedWorkflowType('');
      setTargetResource('');
      setPriority('normal');

    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Failed to start workflow');
    } finally {
      setLoading(false);
    }
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'completed':
        return <CheckCircle color="success" />;
      case 'failed':
        return <Error color="error" />;
      case 'running':
        return <Schedule color="primary" />;
      default:
        return <Info color="disabled" />;
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'completed':
        return 'success';
      case 'failed':
        return 'error';
      case 'running':
        return 'primary';
      default:
        return 'default';
    }
  };

  const getWorkflowTypeIcon = (type: string) => {
    switch (type) {
      case 'compliance':
        return <Assessment />;
      case 'security':
        return <Security />;
      case 'cost-analysis':
        return <AttachMoney />;
      default:
        return <Info />;
    }
  };

  const formatDuration = (startTime: string, endTime?: string) => {
    const start = new Date(startTime);
    const end = endTime ? new Date(endTime) : new Date();
    const duration = end.getTime() - start.getTime();

    const minutes = Math.floor(duration / (1000 * 60));
    const seconds = Math.floor((duration % (1000 * 60)) / 1000);

    if (minutes > 0) {
      return `${minutes}m ${seconds}s`;
    }
    return `${seconds}s`;
  };

  return (
    <Box sx={{ p: 3 }}>
      <Typography variant="h4" gutterBottom>
        AI Agent Management
      </Typography>

      {error && (
        <Alert severity="error" sx={{ mb: 2 }}>
          {error}
        </Alert>
      )}

      {/* Stats Overview */}
      {stats && (
        <Grid container spacing={3} sx={{ mb: 3 }}>
          <Grid item xs={12} md={3}>
            <Card>
              <CardContent>
                <Typography variant="h6" color="primary">
                  {stats.totalAgents}
                </Typography>
                <Typography variant="body2" color="textSecondary">
                  Total Agents
                </Typography>
              </CardContent>
            </Card>
          </Grid>
          <Grid item xs={12} md={3}>
            <Card>
              <CardContent>
                <Typography variant="h6" color="primary">
                  {stats.activeAgents}
                </Typography>
                <Typography variant="body2" color="textSecondary">
                  Active Agents
                </Typography>
              </CardContent>
            </Card>
          </Grid>
          <Grid item xs={12} md={3}>
            <Card>
              <CardContent>
                <Typography variant="h6" color="success.main">
                  {stats.completedTasks}
                </Typography>
                <Typography variant="body2" color="textSecondary">
                  Completed Tasks
                </Typography>
              </CardContent>
            </Card>
          </Grid>
          <Grid item xs={12} md={3}>
            <Card>
              <CardContent>
                <Typography variant="h6">
                  {stats.averageExecutionTime}s
                </Typography>
                <Typography variant="body2" color="textSecondary">
                  Avg Execution Time
                </Typography>
              </CardContent>
            </Card>
          </Grid>
        </Grid>
      )}

      {/* Controls */}
      <Box sx={{ mb: 3, display: 'flex', gap: 2, alignItems: 'center' }}>
        <Button
          variant="contained"
          startIcon={<PlayArrow />}
          onClick={() => setStartDialogOpen(true)}
          disabled={loading}
        >
          Start New Workflow
        </Button>
        <Button
          variant="outlined"
          startIcon={<Refresh />}
          onClick={fetchWorkflows}
          disabled={loading}
        >
          Refresh
        </Button>
      </Box>

      {/* Workflows List */}
      <Card>
        <CardHeader
          title="Recent Workflows"
          subheader="Monitor and manage AI agent workflows"
        />
        <CardContent>
          {loading && <LinearProgress sx={{ mb: 2 }} />}

          <List>
            {workflows.map((workflow) => (
              <Accordion
                key={workflow.id}
                expanded={expandedWorkflow === workflow.id}
                onChange={() => setExpandedWorkflow(
                  expandedWorkflow === workflow.id ? null : workflow.id
                )}
              >
                <AccordionSummary expandIcon={<ExpandMore />}>
                  <Box sx={{ display: 'flex', alignItems: 'center', width: '100%' }}>
                    {getWorkflowTypeIcon(workflow.type)}
                    <Typography sx={{ ml: 2, flex: 1 }}>
                      {workflow.type} - {workflow.targetResource}
                    </Typography>
                    <Chip
                      label={workflow.status}
                      color={getStatusColor(workflow.status) as any}
                      size="small"
                      sx={{ mr: 2 }}
                    />
                    <Typography variant="body2" color="textSecondary">
                      {formatDuration(workflow.startedAt, workflow.completedAt)}
                    </Typography>
                  </Box>
                </AccordionSummary>
                <AccordionDetails>
                  <Box sx={{ mb: 2 }}>
                    <Typography variant="body2" color="textSecondary">
                      <strong>ID:</strong> {workflow.id}
                    </Typography>
                    <Typography variant="body2" color="textSecondary">
                      <strong>Started:</strong> {new Date(workflow.startedAt).toLocaleString()}
                    </Typography>
                    {workflow.completedAt && (
                      <Typography variant="body2" color="textSecondary">
                        <strong>Completed:</strong> {new Date(workflow.completedAt).toLocaleString()}
                      </Typography>
                    )}
                  </Box>

                  {workflow.result && (
                    <Box sx={{ mb: 2 }}>
                      <Typography variant="subtitle2" gutterBottom>
                        Results:
                      </Typography>
                      {workflow.type === 'compliance' && workflow.result.score && (
                        <Box>
                          <Typography variant="body2">
                            Compliance Score: {workflow.result.score}%
                          </Typography>
                          <Typography variant="body2">
                            Issues Found: {workflow.result.issues}
                          </Typography>
                          <Typography variant="body2">
                            Approved: {workflow.result.approved ? 'Yes' : 'No'}
                          </Typography>
                          {workflow.result.recommendations && (
                            <Box sx={{ mt: 1 }}>
                              <Typography variant="body2" sx={{ mb: 1 }}>
                                Recommendations:
                              </Typography>
                              <List dense>
                                {workflow.result.recommendations.map((rec: string, index: number) => (
                                  <ListItem key={index}>
                                    <ListItemText primary={rec} />
                                  </ListItem>
                                ))}
                              </List>
                            </Box>
                          )}
                        </Box>
                      )}
                    </Box>
                  )}

                  {workflow.error && (
                    <Alert severity="error" sx={{ mt: 2 }}>
                      {workflow.error}
                    </Alert>
                  )}
                </AccordionDetails>
              </Accordion>
            ))}
          </List>

          {workflows.length === 0 && !loading && (
            <Typography variant="body2" color="textSecondary" sx={{ textAlign: 'center', py: 4 }}>
              No workflows found. Start your first workflow to see results here.
            </Typography>
          )}
        </CardContent>
      </Card>

      {/* Start Workflow Dialog */}
      <Dialog open={startDialogOpen} onClose={() => setStartDialogOpen(false)} maxWidth="sm" fullWidth>
        <DialogTitle>Start New Workflow</DialogTitle>
        <DialogContent>
          <Box sx={{ pt: 1, display: 'flex', flexDirection: 'column', gap: 2 }}>
            <FormControl fullWidth>
              <InputLabel>Workflow Type</InputLabel>
              <Select
                value={selectedWorkflowType}
                onChange={(e) => setSelectedWorkflowType(e.target.value)}
                label="Workflow Type"
              >
                <MenuItem value="compliance">Compliance Check</MenuItem>
                <MenuItem value="security">Security Scan</MenuItem>
                <MenuItem value="cost-analysis">Cost Analysis</MenuItem>
              </Select>
            </FormControl>

            <TextField
              label="Target Resource"
              value={targetResource}
              onChange={(e) => setTargetResource(e.target.value)}
              placeholder="e.g., vm-web-server-001"
              fullWidth
              required
            />

            <FormControl fullWidth>
              <InputLabel>Priority</InputLabel>
              <Select
                value={priority}
                onChange={(e) => setPriority(e.target.value)}
                label="Priority"
              >
                <MenuItem value="low">Low</MenuItem>
                <MenuItem value="normal">Normal</MenuItem>
                <MenuItem value="high">High</MenuItem>
                <MenuItem value="critical">Critical</MenuItem>
              </Select>
            </FormControl>
          </Box>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setStartDialogOpen(false)}>Cancel</Button>
          <Button
            onClick={handleStartWorkflow}
            variant="contained"
            disabled={!selectedWorkflowType || !targetResource || loading}
          >
            {loading ? 'Starting...' : 'Start Workflow'}
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
};

export default AgentManagement;
