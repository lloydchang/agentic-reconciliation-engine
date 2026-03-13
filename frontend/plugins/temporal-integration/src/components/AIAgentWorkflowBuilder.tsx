import React, { useState } from 'react';
import {
  Box,
  Card,
  CardContent,
  Typography,
  Button,
  Grid,
  Select,
  MenuItem,
  FormControl,
  InputLabel,
  TextField,
  Chip,
  Paper,
  Divider,
  Alert,
  CircularProgress,
} from '@mui/material';
import {
  PlayArrow,
  Security,
  Gavel,
  Savings,
  People,
  Cloud,
  Assessment,
} from '@mui/icons-material';

interface WorkflowStep {
  id: string;
  type: 'agent' | 'infrastructure' | 'human' | 'aggregation';
  name: string;
  description: string;
  icon: React.ReactNode;
  config: Record<string, any>;
  status?: 'pending' | 'running' | 'completed' | 'error';
}

interface WorkflowDefinition {
  name: string;
  description: string;
  steps: WorkflowStep[];
}

const AIAgentWorkflowBuilder: React.FC = () => {
  const [selectedWorkflow, setSelectedWorkflow] = useState<string>('ai-orchestration');
  const [workflowConfig, setWorkflowConfig] = useState<Record<string, any>>({});
  const [isRunning, setIsRunning] = useState(false);
  const [workflowResult, setWorkflowResult] = useState<any>(null);
  const [error, setError] = useState<string | null>(null);

  const workflowTemplates: Record<string, WorkflowDefinition> = {
    'ai-orchestration': {
      name: 'AI Agent Orchestration',
      description: 'Coordinate multiple AI agents for comprehensive compliance checking',
      steps: [
        {
          id: 'discover',
          type: 'infrastructure',
          name: 'Infrastructure Discovery',
          description: 'Discover and emulate target infrastructure resources',
          icon: <Cloud />,
          config: { targetResource: 'vm-web-server-001' },
        },
        {
          id: 'security-agent',
          type: 'agent',
          name: 'Security Agent',
          description: 'Analyze security posture and identify vulnerabilities',
          icon: <Security />,
          config: { agentType: 'security', scanType: 'comprehensive' },
        },
        {
          id: 'compliance-agent',
          type: 'agent',
          name: 'Compliance Agent',
          description: 'Check compliance against regulatory standards',
          icon: <Gavel />,
          config: { agentType: 'compliance', standards: ['SOC2', 'GDPR', 'HIPAA'] },
        },
        {
          id: 'cost-agent',
          type: 'agent',
          name: 'Cost Optimization Agent',
          description: 'Analyze cost optimization opportunities',
          icon: <Savings />,
          config: { agentType: 'cost-optimization', analysisDepth: 'deep' },
        },
        {
          id: 'aggregate',
          type: 'aggregation',
          name: 'Result Aggregation',
          description: 'Aggregate and analyze all agent results',
          icon: <Assessment />,
          config: { aggregationType: 'weighted-average' },
        },
        {
          id: 'human-review',
          type: 'human',
          name: 'Human Review',
          description: 'Human review and approval of findings',
          icon: <People />,
          config: { required: true, approvers: ['security-team'] },
        },
      ],
    },
    'multi-agent-collaboration': {
      name: 'Multi-Agent Collaboration',
      description: 'Enable agents to collaborate and reach consensus',
      steps: [
        {
          id: 'primary-analysis',
          type: 'agent',
          name: 'Primary Agent Analysis',
          description: 'Primary agent performs initial analysis',
          icon: <Security />,
          config: { agentType: 'security', isPrimary: true },
        },
        {
          id: 'validation-agents',
          type: 'agent',
          name: 'Validation Agents',
          description: 'Multiple agents validate primary findings',
          icon: <Gavel />,
          config: { agentTypes: ['compliance', 'cost-optimization'], consensusType: 'majority' },
        },
        {
          id: 'consensus-building',
          type: 'aggregation',
          name: 'Consensus Building',
          description: 'Build consensus from agent inputs',
          icon: <Assessment />,
          config: { consensusThreshold: 0.7 },
        },
      ],
    },
    'human-in-the-loop': {
      name: 'Human-in-the-Loop Workflow',
      description: 'Workflow with human decision points',
      steps: [
        {
          id: 'automated-check',
          type: 'agent',
          name: 'Automated Compliance Check',
          description: 'Initial automated compliance verification',
          icon: <Security />,
          config: { agentType: 'compliance', autoApproveThreshold: 0.9 },
        },
        {
          id: 'human-decision',
          type: 'human',
          name: 'Human Decision Point',
          description: 'Human review and decision required',
          icon: <People />,
          config: { decisionType: 'approve-reject', timeout: '24h' },
        },
        {
          id: 'final-approval',
          type: 'aggregation',
          name: 'Final Approval',
          description: 'Process human decision and complete workflow',
          icon: <Assessment />,
          config: { recordDecision: true, notifyStakeholders: true },
        },
      ],
    },
  };

  const currentWorkflow = workflowTemplates[selectedWorkflow];

  const handleConfigChange = (stepId: string, field: string, value: any) => {
    setWorkflowConfig(prev => ({
      ...prev,
      [stepId]: {
        ...prev[stepId],
        [field]: value,
      },
    }));
  };

  const startWorkflow = async () => {
    setIsRunning(true);
    setError(null);
    setWorkflowResult(null);

    try {
      const endpoint = getWorkflowEndpoint(selectedWorkflow);
      const response = await fetch(`http://localhost:8081${endpoint}`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(workflowConfig),
      });

      if (!response.ok) {
        throw new Error(`Workflow failed: ${response.statusText}`);
      }

      const workflowId = await response.text();
      setWorkflowResult({ workflowId, status: 'started' });

      // Poll for status updates
      pollWorkflowStatus(workflowId);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unknown error occurred');
    } finally {
      setIsRunning(false);
    }
  };

  const getWorkflowEndpoint = (workflowType: string): string => {
    const endpoints: Record<string, string> = {
      'ai-orchestration': '/workflow/start-ai-orchestration',
      'multi-agent-collaboration': '/workflow/start-multi-agent',
      'human-in-the-loop': '/workflow/start-human-in-loop',
    };
    return endpoints[workflowType] || '/workflow/start';
  };

  const pollWorkflowStatus = async (workflowId: string) => {
    const pollInterval = setInterval(async () => {
      try {
        const response = await fetch(`http://localhost:8081/workflow/status?id=${workflowId}`);
        if (response.ok) {
          const status = await response.text();
          setWorkflowResult(prev => ({ ...prev, status }));

          if (status === 'Completed' || status === 'Failed') {
            clearInterval(pollInterval);
          }
        }
      } catch (err) {
        console.error('Error polling workflow status:', err);
        clearInterval(pollInterval);
      }
    }, 2000);
  };

  const getStepColor = (stepType: string) => {
    const colors: Record<string, string> = {
      agent: 'primary',
      infrastructure: 'secondary',
      human: 'warning',
      aggregation: 'success',
    };
    return colors[stepType] || 'default';
  };

  return (
    <Box sx={{ p: 3 }}>
      <Typography variant="h4" gutterBottom>
        AI Agent Workflow Builder
      </Typography>

      {/* Workflow Selection */}
      <Card sx={{ mb: 3 }}>
        <CardContent>
          <Typography variant="h6" gutterBottom>
            Select Workflow Template
          </Typography>
          <FormControl fullWidth>
            <InputLabel>Workflow Type</InputLabel>
            <Select
              value={selectedWorkflow}
              label="Workflow Type"
              onChange={(e) => setSelectedWorkflow(e.target.value)}
            >
              {Object.entries(workflowTemplates).map(([key, workflow]) => (
                <MenuItem key={key} value={key}>
                  {workflow.name}
                </MenuItem>
              ))}
            </Select>
          </FormControl>
          <Typography variant="body2" color="text.secondary" sx={{ mt: 2 }}>
            {currentWorkflow.description}
          </Typography>
        </CardContent>
      </Card>

      {/* Workflow Steps */}
      <Paper sx={{ p: 2, mb: 3 }}>
        <Typography variant="h6" gutterBottom>
          Workflow Steps
        </Typography>
        <Grid container spacing={2}>
          {currentWorkflow.steps.map((step, index) => (
            <Grid item xs={12} md={6} lg={4} key={step.id}>
              <Card variant="outlined">
                <CardContent>
                  <Box display="flex" alignItems="center" mb={1}>
                    {step.icon}
                    <Typography variant="subtitle1" sx={{ ml: 1 }}>
                      {step.name}
                    </Typography>
                  </Box>
                  <Chip
                    label={step.type}
                    color={getStepColor(step.type) as any}
                    size="small"
                    sx={{ mb: 1 }}
                  />
                  <Typography variant="body2" color="text.secondary">
                    {step.description}
                  </Typography>
                  
                  {/* Step Configuration */}
                  {step.type === 'agent' && (
                    <Box sx={{ mt: 2 }}>
                      <TextField
                        fullWidth
                        label="Agent Configuration"
                        size="small"
                        value={JSON.stringify(workflowConfig[step.id] || step.config)}
                        onChange={(e) => {
                          try {
                            const config = JSON.parse(e.target.value);
                            handleConfigChange(step.id, 'config', config);
                          } catch (err) {
                            // Invalid JSON, ignore
                          }
                        }}
                        multiline
                        rows={2}
                      />
                    </Box>
                  )}
                </CardContent>
              </Card>
            </Grid>
          ))}
        </Grid>
      </Paper>

      {/* Workflow Execution */}
      <Card>
        <CardContent>
          <Typography variant="h6" gutterBottom>
            Execute Workflow
          </Typography>
          
          {error && (
            <Alert severity="error" sx={{ mb: 2 }}>
              {error}
            </Alert>
          )}

          {workflowResult && (
            <Alert severity="success" sx={{ mb: 2 }}>
              Workflow started successfully! ID: {workflowResult.workflowId}
              <br />
              Status: {workflowResult.status}
            </Alert>
          )}

          <Button
            variant="contained"
            startIcon={isRunning ? <CircularProgress size={20} /> : <PlayArrow />}
            onClick={startWorkflow}
            disabled={isRunning}
            size="large"
          >
            {isRunning ? 'Starting Workflow...' : 'Start Workflow'}
          </Button>
        </CardContent>
      </Card>
    </Box>
  );
};

export default AIAgentWorkflowBuilder;
