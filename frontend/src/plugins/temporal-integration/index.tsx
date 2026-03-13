import React, { useState } from 'react';
import {
  Content,
  Header,
  Page,
  Progress,
  ResponseErrorPanel,
} from '@backstage/core-components';
import { Button, Grid, Paper, Typography, Table, TableBody, TableCell, TableContainer, TableHead, TableRow, Box } from '@mui/material';
import { useApi } from '@backstage/core-plugin-api';
import { configApiRef } from '@backstage/core-plugin-api';

interface WorkflowStatus {
  id: string;
  status: string;
  createdAt: string;
}

export const TemporalIntegrationPage = () => {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<Error>();
  const [workflows, setWorkflows] = useState<WorkflowStatus[]>([]);
  const [isSplitScreen, setIsSplitScreen] = useState(false);
  const config = useApi(configApiRef);
  const backendUrl = config.getOptionalString('temporal.backendUrl') || 'http://localhost:8081';

  const startWorkflow = async () => {
    setLoading(true);
    setError(undefined);
    
    try {
      const response = await fetch(`${backendUrl}/workflow/start`, {
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
      };
      
      setWorkflows(prev => [newWorkflow, ...prev]);
    } catch (err) {
      setError(err as Error);
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
        prev.map(w => 
          w.id === workflowId ? { ...w, status } : w
        )
      );
    } catch (err) {
      setError(err as Error);
    }
  };

  if (error) {
    return <ResponseErrorPanel error={error} />;
  }

  return (
    <Page themeId="tool">
      <Header 
        title="Temporal Integration" 
        children={
          <Button
            variant="outlined"
            onClick={() => setIsSplitScreen(!isSplitScreen)}
          >
            {isSplitScreen ? 'Exit Split Screen' : 'Split Screen View'}
          </Button>
        }
      />
      <Content>
        {isSplitScreen ? (
          <Box sx={{ display: 'flex', height: 'calc(100vh - 120px)', overflow: 'hidden' }}>
            <Box 
              sx={{ 
                flex: 1, 
                resize: 'horizontal', 
                overflow: 'auto', 
                minWidth: '300px', 
                maxWidth: '80%', 
                borderRight: '1px solid #ccc' 
              }}
            >
              <Grid container spacing={3} direction="column">
                <Grid item>
                  <Paper style={{ padding: 16 }}>
                    <Typography variant="h6" gutterBottom>
                      Workflow Management
                    </Typography>
                    <Button
                      variant="contained"
                      color="primary"
                      onClick={startWorkflow}
                      disabled={loading}
                      style={{ marginRight: 16 }}
                    >
                      {loading ? <Progress /> : 'Start HelloBackstage Workflow'}
                    </Button>
                    <Button
                      variant="outlined"
                      onClick={() => workflows.forEach(w => checkWorkflowStatus(w.id))}
                    >
                      Refresh All Status
                    </Button>
                  </Paper>
                </Grid>
                
                <Grid item>
                  <Paper style={{ padding: 16 }}>
                    <Typography variant="h6" gutterBottom>
                      Workflow Status
                    </Typography>
                    <TableContainer>
                      <Table>
                        <TableHead>
                          <TableRow>
                            <TableCell>Workflow ID</TableCell>
                            <TableCell>Status</TableCell>
                            <TableCell>Created At</TableCell>
                            <TableCell>Actions</TableCell>
                          </TableRow>
                        </TableHead>
                        <TableBody>
                          {workflows.map((workflow) => (
                            <TableRow key={workflow.id}>
                              <TableCell>{workflow.id}</TableCell>
                              <TableCell>{workflow.status}</TableCell>
                              <TableCell>{new Date(workflow.createdAt).toLocaleString()}</TableCell>
                              <TableCell>
                                <Button
                                  size="small"
                                  onClick={() => checkWorkflowStatus(workflow.id)}
                                >
                                  Check Status
                                </Button>
                              </TableCell>
                            </TableRow>
                          ))}
                          {workflows.length === 0 && (
                            <TableRow>
                              <TableCell colSpan={4} align="center">
                                No workflows started yet. Click "Start HelloBackstage Workflow" to begin.
                              </TableCell>
                            </TableRow>
                          )}
                        </TableBody>
                      </Table>
                    </TableContainer>
                  </Paper>
                </Grid>
              </Grid>
            </Box>
            <Box sx={{ flex: 1, overflow: 'hidden' }}>
              <iframe
                src="http://localhost:8080"
                style={{ width: '100%', height: '100%', border: 'none' }}
                title="Temporal UI"
              />
            </Box>
          </Box>
        ) : (
          <Grid container spacing={3} direction="column">
            <Grid item>
              <Paper style={{ padding: 16 }}>
                <Typography variant="h6" gutterBottom>
                  Workflow Management
                </Typography>
                <Button
                  variant="contained"
                  color="primary"
                  onClick={startWorkflow}
                  disabled={loading}
                  style={{ marginRight: 16 }}
                >
                  {loading ? <Progress /> : 'Start HelloBackstage Workflow'}
                </Button>
                <Button
                  variant="outlined"
                  onClick={() => workflows.forEach(w => checkWorkflowStatus(w.id))}
                >
                  Refresh All Status
                </Button>
              </Paper>
            </Grid>
            
            <Grid item>
              <Paper style={{ padding: 16 }}>
                <Typography variant="h6" gutterBottom>
                  Workflow Status
                </Typography>
                <TableContainer>
                  <Table>
                    <TableHead>
                      <TableRow>
                        <TableCell>Workflow ID</TableCell>
                        <TableCell>Status</TableCell>
                        <TableCell>Created At</TableCell>
                        <TableCell>Actions</TableCell>
                      </TableRow>
                    </TableHead>
                    <TableBody>
                      {workflows.map((workflow) => (
                        <TableRow key={workflow.id}>
                          <TableCell>{workflow.id}</TableCell>
                          <TableCell>{workflow.status}</TableCell>
                          <TableCell>{new Date(workflow.createdAt).toLocaleString()}</TableCell>
                          <TableCell>
                            <Button
                              size="small"
                              onClick={() => checkWorkflowStatus(workflow.id)}
                            >
                              Check Status
                            </Button>
                          </TableCell>
                        </TableRow>
                      ))}
                      {workflows.length === 0 && (
                        <TableRow>
                          <TableCell colSpan={4} align="center">
                            No workflows started yet. Click "Start HelloBackstage Workflow" to begin.
                          </TableCell>
                        </TableRow>
                      )}
                    </TableBody>
                  </Table>
                </TableContainer>
              </Paper>
            </Grid>
          </Grid>
        )}
      </Content>
    </Page>
  );
};
