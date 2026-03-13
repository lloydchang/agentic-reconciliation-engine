import React, { useState, useEffect, useRef } from 'react';
import {
  Box,
  Typography,
  List,
  ListItem,
  ListItemText,
  Button,
  TextField,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Chip,
  Card,
  CardContent,
  CardActions,
  Grid,
  Alert,
  CircularProgress,
  LinearProgress,
  Divider,
  Paper,
} from '@mui/material';
import { 
  PlayArrow, 
  Info, 
  Refresh, 
  CheckCircle, 
  Error as ErrorIcon, 
  PlayCircleFilled,
  Description
} from '@mui/icons-material';
import { MarkdownContent } from '@backstage/core-components';

interface Skill {
  name: string;
  description: string;
  scope: string;
  argumentHint?: string;
  userInvocable: boolean;
  allowedTools?: string[];
  context?: string;
  model?: string;
}

interface StepResult {
  stepNumber: number;
  output: string;
  success: boolean;
}

interface SkillExecutionStatus {
  skillName: string;
  currentStep: number;
  totalSteps: number;
  status: string; // "Running", "Paused", "Completed", "Failed"
  stepResults: StepResult[];
}

const SkillsManagement: React.FC = () => {
  const [skills, setSkills] = useState<Skill[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [selectedSkill, setSelectedSkill] = useState<Skill | null>(null);
  const [executionDialog, setExecutionDialog] = useState(false);
  const [executionArgs, setExecutionArgs] = useState('');
  const [executing, setExecuting] = useState(false);
  const [workflowId, setWorkflowId] = useState<string | null>(null);
  const [executionStatus, setExecutionStatus] = useState<SkillExecutionStatus | null>(null);
  const [viewMarkdownSkill, setViewMarkdownSkill] = useState<Skill | null>(null);
  const pollIntervalRef = useRef<NodeJS.Timeout | null>(null);

  const API_BASE = 'http://localhost:8081';

  const fetchSkills = async () => {
    setLoading(true);
    setError(null);
    try {
      const response = await fetch(`${API_BASE}/api/skills`);
      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      }
      const data = await response.json();
      setSkills(data.skills || []);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to fetch skills');
    } finally {
      setLoading(false);
    }
  };

  const startSkillWorkflow = async (skillName: string, args: string[]) => {
    setExecuting(true);
    setError(null);
    setExecutionStatus(null);
    try {
      const response = await fetch(`${API_BASE}/workflow/start-skill`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ skillName, arguments: args }),
      });

      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      }

      const data = await response.json();
      setWorkflowId(data.workflowId);
      return data;
    } catch (err: any) {
      setError(err.message || 'Failed to start skill workflow');
      setExecuting(false);
      throw err;
    }
  };

  const pollStatus = async () => {
    if (!workflowId) return;

    try {
      const response = await fetch(`${API_BASE}/workflow/skill-status/${workflowId}`);
      if (!response.ok) return;

      const status: SkillExecutionStatus = await response.json();
      setExecutionStatus(status);

      if (status.status === 'Completed' || status.status === 'Failed') {
        stopPolling();
        setExecuting(false);
      }
    } catch (err) {
      console.error('Polling error:', err);
    }
  };

  const stopPolling = () => {
    if (pollIntervalRef.current) {
      clearInterval(pollIntervalRef.current);
      pollIntervalRef.current = null;
    }
  };

  const openExecutionDialog = (skill: Skill) => {
    setSelectedSkill(skill);
    setExecutionDialog(true);
  };

  const closeExecutionDialog = () => {
    setExecutionDialog(false);
    setSelectedSkill(null);
    setExecutionArgs('');
  };

  const handleExecuteSkill = async () => {
    if (!selectedSkill) return;

    const args = executionArgs.trim() ? executionArgs.split(' ') : [];
    try {
      await startSkillWorkflow(selectedSkill.name, args);
      closeExecutionDialog();
    } catch (err) {
      // Error handled in startSkillWorkflow
    }
  };

  const handleApprove = async () => {
    if (!workflowId) return;

    try {
      await fetch(`${API_BASE}/workflow/signal/${workflowId}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ signal: 'HumanApprovalSignal', value: 'Approved' }),
      });
    } catch (err) {
      setError('Failed to send approval signal');
    }
  };

  useEffect(() => {
    if (workflowId && executing) {
      pollIntervalRef.current = setInterval(pollStatus, 1000);
    }
    return () => stopPolling();
  }, [workflowId, executing]);

  useEffect(() => {
    fetchSkills();
  }, []);

  const getStatusColor = (status: string): "primary" | "warning" | "success" | "error" | "default" => {
    switch (status) {
      case 'Running': return 'primary';
      case 'Paused': return 'warning';
      case 'Completed': return 'success';
      case 'Failed': return 'error';
      default: return 'default';
    }
  };

  return (
    <Box sx={{ p: 3 }}>
      <Typography variant="h4" gutterBottom>
        AI Agent Skills
      </Typography>

      <Box sx={{ mb: 3, display: 'flex', gap: 2 }}>
        <Button
          variant="contained"
          startIcon={<Refresh />}
          onClick={fetchSkills}
          disabled={loading || executing}
        >
          {loading ? <CircularProgress size={20} /> : 'Refresh Skills'}
        </Button>
      </Box>

      {error && (
        <Alert severity="error" sx={{ mb: 3 }} onClose={() => setError(null)}>
          {error}
        </Alert>
      )}

      {executionStatus && (
        <Paper elevation={3} sx={{ p: 3, mb: 4, bgcolor: 'background.paper', borderRadius: 2 }}>
          <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
            <Typography variant="h5">
              Executing: {executionStatus.skillName}
            </Typography>
            <Chip 
              label={executionStatus.status} 
              color={getStatusColor(executionStatus.status)}
              sx={{ fontWeight: 'bold' }}
            />
          </Box>

          <Box sx={{ mb: 2 }}>
            <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 1 }}>
              <Typography variant="body2" color="text.secondary">
                Step {executionStatus.currentStep} of {executionStatus.totalSteps}
              </Typography>
              <Typography variant="body2" color="text.secondary">
                {Math.round((executionStatus.currentStep / executionStatus.totalSteps) * 100)}%
              </Typography>
            </Box>
            <LinearProgress 
              variant="determinate" 
              value={(executionStatus.currentStep / executionStatus.totalSteps) * 100} 
              sx={{ height: 10, borderRadius: 5 }}
            />
          </Box>

          {executionStatus.status === 'Paused' && (
            <Alert severity="info" sx={{ mb: 2 }} action={
              <Button color="inherit" size="small" onClick={handleApprove} startIcon={<PlayCircleFilled />}>
                CONFIRM & PROCEED
              </Button>
            }>
              <strong>Human Gate Triggered:</strong> This step requires manual confirmation of impact. Review the plan below and confirm to proceed.
            </Alert>
          )}

          <Typography variant="h6" gutterBottom sx={{ mt: 3 }}>
            Execution Log
          </Typography>
          <List sx={{ bgcolor: 'action.hover', borderRadius: 1 }}>
            {executionStatus.stepResults.map((result, idx) => (
              <React.Fragment key={idx}>
                {idx > 0 && <Divider />}
                <ListItem alignItems="flex-start">
                  <Box sx={{ mr: 2, mt: 0.5 }}>
                    {result.success ? 
                      <CheckCircle color="success" /> : 
                      <ErrorIcon color="error" />
                    }
                  </Box>
                  <ListItemText
                    primary={`Step ${result.stepNumber}`}
                    secondaryTypographyProps={{ component: 'div' }}
                    secondary={
                      <Box component="pre" sx={{ 
                        mt: 1, 
                        p: 1, 
                        bgcolor: 'common.black', 
                        color: 'common.white', 
                        borderRadius: 1,
                        fontSize: '0.8rem',
                        overflowX: 'auto',
                        whiteSpace: 'pre-wrap'
                      }}>
                        {result.output}
                      </Box>
                    }
                  />
                </ListItem>
              </React.Fragment>
            ))}
            {executing && executionStatus.status === 'Running' && (
              <ListItem>
                <Box sx={{ mr: 2 }}>
                  <CircularProgress size={24} />
                </Box>
                <ListItemText primary={`Step ${executionStatus.currentStep} in progress...`} />
              </ListItem>
            )}
          </List>
        </Paper>
      )}

      <Grid container spacing={3}>
        {skills.map((skill) => (
          <Grid item xs={12} md={6} lg={4} key={skill.name}>
            <Card sx={{ height: '100%', display: 'flex', flexDirection: 'column' }}>
              <CardContent sx={{ flexGrow: 1 }}>
                <Typography variant="h6" gutterBottom>
                  /{skill.name}
                </Typography>
                <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
                  {skill.description}
                </Typography>

                <Box sx={{ mb: 1 }}>
                  <Chip
                    label={skill.scope}
                    size="small"
                    color={skill.scope === 'repo' ? 'primary' : 'secondary'}
                  />
                  {skill.context && (
                    <Chip
                      label={`Context: ${skill.context}`}
                      size="small"
                      variant="outlined"
                      sx={{ ml: 1 }}
                    />
                  )}
                </Box>
              </CardContent>

              <CardActions>
                <Button
                  size="small"
                  startIcon={<Info />}
                  onClick={() => setSelectedSkill(skill)}
                  disabled={!skill.userInvocable}
                >
                  Info
                </Button>
                <Button
                  size="small"
                  startIcon={<Description />}
                  onClick={() => setViewMarkdownSkill(skill)}
                >
                  View MD
                </Button>
                <Button
                  size="small"
                  variant="contained"
                  startIcon={<PlayArrow />}
                  onClick={() => openExecutionDialog(skill)}
                  disabled={!skill.userInvocable || executing}
                >
                  Execute
                </Button>
              </CardActions>
            </Card>
          </Grid>
        ))}
      </Grid>

      {/* Skill Info Dialog */}
      <Dialog open={!!selectedSkill && !executionDialog} onClose={() => setSelectedSkill(null)} maxWidth="md" fullWidth>
        <DialogTitle>
          Skill: {selectedSkill?.name}
        </DialogTitle>
        <DialogContent>
          {selectedSkill && (
            <Box>
              <Typography variant="body1" sx={{ mb: 2 }}>
                {selectedSkill.description}
              </Typography>

              <Grid container spacing={2}>
                <Grid item xs={6}>
                  <Typography variant="subtitle2">Scope:</Typography>
                  <Chip label={selectedSkill.scope} size="small" />
                </Grid>
                <Grid item xs={6}>
                  <Typography variant="subtitle2">User Invocable:</Typography>
                  <Chip
                    label={selectedSkill.userInvocable ? 'Yes' : 'No'}
                    size="small"
                    color={selectedSkill.userInvocable ? 'success' : 'default'}
                  />
                </Grid>
                {selectedSkill.argumentHint && (
                  <Grid item xs={12}>
                    <Typography variant="subtitle2">Arguments:</Typography>
                    <Typography variant="body2">{selectedSkill.argumentHint}</Typography>
                  </Grid>
                )}
              </Grid>
            </Box>
          )}
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setSelectedSkill(null)}>Close</Button>
          {selectedSkill?.userInvocable && (
            <Button variant="contained" onClick={() => openExecutionDialog(selectedSkill)}>
              Execute Skill
            </Button>
          )}
        </DialogActions>
      </Dialog>

      {/* Skill Execution Dialog */}
      <Dialog open={executionDialog} onClose={closeExecutionDialog} maxWidth="sm" fullWidth>
        <DialogTitle>
          Execute Skill: {selectedSkill?.name}
        </DialogTitle>
        <DialogContent>
          <Typography variant="body2" sx={{ mb: 2 }}>
            {selectedSkill?.description}
          </Typography>

          <TextField
            fullWidth
            label="Arguments (space-separated)"
            value={executionArgs}
            onChange={(e) => setExecutionArgs(e.target.value)}
            placeholder={selectedSkill?.argumentHint || "Enter arguments..."}
            sx={{ mt: 1 }}
          />
        </DialogContent>
        <DialogActions>
          <Button onClick={closeExecutionDialog}>Cancel</Button>
          <Button
            variant="contained"
            onClick={handleExecuteSkill}
            disabled={executing}
            startIcon={executing ? <CircularProgress size={16} /> : <PlayArrow />}
          >
            {executing ? 'Executing...' : 'Execute'}
          </Button>
        </DialogActions>
      </Dialog>

      {/* Skill Markdown Viewer Dialog */}
      <Dialog 
        open={!!viewMarkdownSkill} 
        onClose={() => setViewMarkdownSkill(null)} 
        maxWidth="lg" 
        fullWidth
      >
        <DialogTitle>
          SKILL.md: {viewMarkdownSkill?.name}
        </DialogTitle>
        <DialogContent dividers>
          {viewMarkdownSkill && (
            <Box sx={{ p: 1 }}>
              <MarkdownContent content={viewMarkdownSkill.content} />
            </Box>
          )}
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setViewMarkdownSkill(null)}>Close</Button>
          {viewMarkdownSkill?.userInvocable && (
            <Button 
              variant="contained" 
              startIcon={<PlayArrow />}
              onClick={() => {
                const skill = viewMarkdownSkill;
                setViewMarkdownSkill(null);
                openExecutionDialog(skill);
              }}
            >
              Execute This Skill
            </Button>
          )}
        </DialogActions>
      </Dialog>
    </Box>
  );
};

export default SkillsManagement;
