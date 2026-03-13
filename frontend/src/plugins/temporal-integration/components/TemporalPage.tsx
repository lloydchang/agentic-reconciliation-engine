import React, { useState } from 'react';
import { Button, Paper, Typography, Table, TableBody, TableCell, TableContainer, TableHead, TableRow, Tabs, Tab, Box, TextField, Dialog, DialogTitle, DialogContent, DialogActions } from '@mui/material';

interface WorkflowStatus {
  id: string;
  status: string;
  createdAt: string;
  type?: string;
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
      id={`simple-tabpanel-${index}`}
      aria-labelledby={`simple-tab-${index}`}
      {...other}
    >
      {value === index && <Box sx={{ p: 3 }}>{children}</Box>}
    </div>
  );
}

export const TemporalPage = () => {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string>();
  const [workflows, setWorkflows] = useState<WorkflowStatus[]>([]);
  const [tabValue, setTabValue] = useState(0);
  const [signalDialog, setSignalDialog] = useState<{open: boolean, workflowId: string}>({open: false, workflowId: ''});
  const [signalForm, setSignalForm] = useState({signal: '', value: ''});
  const backendUrl = 'http://localhost:8081';

  const startWorkflow = async (type: string = 'hello') => {
    setLoading(true);
    setError(undefined);
    
    try {
      let endpoint = '/workflow/start';
      if (type === 'ai-orchestration') {
        endpoint = '/workflow/start-ai-orchestration';
      } else if (type === 'human-in-loop') {
        endpoint = '/workflow/start-human-in-loop';
      } else if (type === 'multi-agent') {
        endpoint = '/workflow/start-multi-agent';
      } else if (type === 'compliance') {
        endpoint = '/workflow/start-compliance';
      }
      
      const response = await fetch(`${backendUrl}${endpoint}`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
      });
      
      if (!response.ok) {
        throw new Error(`Failed to start workflow: ${response.statusText}`);
      }
      
      const workflowId = await response.text();
      const newWorkflow: WorkflowStatus = {
        id: workflowId,
        status: 'RUNNING',
        createdAt: new Date().toISOString(),
        type: type,
      };
      
      setWorkflows(prev => [newWorkflow, ...prev]);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unknown error');
    } finally {
      setLoading(false);
    }
  };

  const checkWorkflowStatus = async (workflowId: string) => {
    try {
      const response = await fetch(`${backendUrl}/workflow/status?id=${workflowId}`);
      
      if (!response.ok) {
        throw new Error(`Failed to get workflow status: ${response.statusText}`);
      }
      
      const status = await response.text();
      
      setWorkflows(prev => 
        prev.map((w: WorkflowStatus) => 
          w.id === workflowId ? { ...w, status } : w
        )
      );
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unknown error');
    }
  };

  const sendSignal = async () => {
    try {
      const response = await fetch(`${backendUrl}/workflow/signal/${signalDialog.workflowId}`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(signalForm),
      });
      
      if (!response.ok) {
        throw new Error(`Failed to send signal: ${response.statusText}`);
      }
      
      setSignalDialog({open: false, workflowId: ''});
      setSignalForm({signal: '', value: ''});
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unknown error');
    }
  };

  const handleTabChange = (event: React.SyntheticEvent, newValue: number) => {
    setTabValue(newValue);
  };

  if (error) {
    return (
      <Paper style={{ padding: 24 }}>
        <Typography variant="h6" color="error">
          Error: {error}
        </Typography>
        <Button onClick={() => setError(undefined)} variant="contained">
          Clear Error
        </Button>
      </Paper>
    );
  }

  return (
    <div>
      <Paper style={{ padding: 24, marginBottom: 24 }}>
        <Typography variant="h6" gutterBottom>
          AI Agent Workflow Management
        </Typography>
        <Tabs value={tabValue} onChange={handleTabChange}>
          <Tab label="Basic Workflows" />
          <Tab label="AI Orchestration" />
          <Tab label="Multi-Agent" />
          <Tab label="Compliance" />
        </Tabs>
      </Paper>
      
      <TabPanel value={tabValue} index={0}>
        <Paper style={{ padding: 24, marginBottom: 24 }}>
          <Typography variant="h6" gutterBottom>
            Basic Workflows
          </Typography>
          <Button
            variant="contained"
            color="primary"
            onClick={() => startWorkflow('hello')}
            disabled={loading}
            style={{ marginRight: 16 }}
          >
            {loading ? 'Starting...' : 'Start HelloBackstage Workflow'}
          </Button>
          <Button
            variant="contained"
            color="secondary"
            onClick={() => startWorkflow('compliance')}
            disabled={loading}
            style={{ marginRight: 16 }}
          >
            {loading ? 'Starting...' : 'Start Compliance Workflow'}
          </Button>
        </Paper>
      </TabPanel>

      <TabPanel value={tabValue} index={1}>
        <Paper style={{ padding: 24, marginBottom: 24 }}>
          <Typography variant="h6" gutterBottom>
            AI Orchestration
          </Typography>
          <Button
            variant="contained"
            color="primary"
            onClick={() => startWorkflow('ai-orchestration')}
            disabled={loading}
            style={{ marginRight: 16 }}
          >
            {loading ? 'Starting...' : 'Start AI Orchestration'}
          </Button>
          <Button
            variant="contained"
            color="secondary"
            onClick={() => startWorkflow('human-in-loop')}
            disabled={loading}
          >
            {loading ? 'Starting...' : 'Start Human-in-Loop'}
          </Button>
        </Paper>
      </TabPanel>

      <TabPanel value={tabValue} index={2}>
        <Paper style={{ padding: 24, marginBottom: 24 }}>
          <Typography variant="h6" gutterBottom>
            Multi-Agent Collaboration
          </Typography>
          <Button
            variant="contained"
            color="primary"
            onClick={() => startWorkflow('multi-agent')}
            disabled={loading}
          >
            {loading ? 'Starting...' : 'Start Multi-Agent Workflow'}
          </Button>
        </Paper>
      </TabPanel>

      <TabPanel value={tabValue} index={3}>
        <Paper style={{ padding: 24, marginBottom: 24 }}>
          <Typography variant="h6" gutterBottom>
            Compliance Workflows
          </Typography>
          <Button
            variant="contained"
            color="primary"
            onClick={() => startWorkflow('compliance')}
            disabled={loading}
          >
            {loading ? 'Starting...' : 'Start Compliance Check'}
          </Button>
        </Paper>
      </TabPanel>
      
      <Paper style={{ padding: 24 }}>
        <Typography variant="h6" gutterBottom>
          Workflow Status
        </Typography>
        <Button
          variant="outlined"
          onClick={() => workflows.forEach((w: WorkflowStatus) => checkWorkflowStatus(w.id))}
          style={{ marginBottom: 16 }}
        >
          Refresh All Status
        </Button>
        <TableContainer>
          <Table>
            <TableHead>
              <TableRow>
                <TableCell>Workflow ID</TableCell>
                <TableCell>Type</TableCell>
                <TableCell>Status</TableCell>
                <TableCell>Created At</TableCell>
                <TableCell>Actions</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {workflows.map((workflow: WorkflowStatus) => (
                <TableRow key={workflow.id}>
                  <TableCell>{workflow.id}</TableCell>
                  <TableCell>{workflow.type || 'basic'}</TableCell>
                  <TableCell>{workflow.status}</TableCell>
                  <TableCell>{new Date(workflow.createdAt).toLocaleString()}</TableCell>
                  <TableCell>
                    <Button
                      size="small"
                      onClick={() => checkWorkflowStatus(workflow.id)}
                      style={{ marginRight: 8 }}
                    >
                      Check Status
                    </Button>
                    <Button
                      size="small"
                      variant="outlined"
                      onClick={() => setSignalDialog({open: true, workflowId: workflow.id})}
                    >
                      Send Signal
                    </Button>
                  </TableCell>
                </TableRow>
              ))}
              {workflows.length === 0 && (
                <TableRow>
                  <TableCell colSpan={5} align="center">
                    No workflows started yet. Select a tab and click a workflow button to begin.
                  </TableCell>
                </TableRow>
              )}
            </TableBody>
          </Table>
        </TableContainer>
      </Paper>

      <Dialog open={signalDialog.open} onClose={() => setSignalDialog({open: false, workflowId: ''})}>
        <DialogTitle>Send Signal to Workflow</DialogTitle>
        <DialogContent>
          <TextField
            autoFocus
            margin="dense"
            label="Signal Name"
            fullWidth
            variant="outlined"
            value={signalForm.signal}
            onChange={(e) => setSignalForm({...signalForm, signal: e.target.value})}
            style={{ marginBottom: 16 }}
          />
          <TextField
            margin="dense"
            label="Signal Value"
            fullWidth
            variant="outlined"
            value={signalForm.value}
            onChange={(e) => setSignalForm({...signalForm, value: e.target.value})}
          />
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setSignalDialog({open: false, workflowId: ''})}>Cancel</Button>
          <Button onClick={sendSignal} variant="contained">Send Signal</Button>
        </DialogActions>
      </Dialog>
    </div>
  );
};
