import React, { useState } from 'react';
import { Button, Table, TableBody, TableCell, TableHead, TableRow, Typography, Box, Tabs, Tab } from '@mui/material';
import AIAgentWorkflowBuilder from './AIAgentWorkflowBuilder';
import MonitoringDashboard from './MonitoringDashboard';
import HumanInTheLoopApprovals from './HumanInTheLoopApprovals';

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

const TemporalPage = () => {
  const [tabValue, setTabValue] = useState(0);
  const [workflows, setWorkflows] = useState<{id: string, status: string}[]>([]);
  const [complianceWorkflows, setComplianceWorkflows] = useState<{id: string, status: string}[]>([]);

  const handleTabChange = (event: React.SyntheticEvent, newValue: number) => {
    setTabValue(newValue);
  };

  const startWorkflow = async () => {
    try {
      const response = await fetch('http://localhost:8081/workflow/start', { method: 'POST' });
      const id = await response.text();
      setWorkflows([...workflows, { id, status: 'Running' }]);
    } catch (error) {
      console.error('Error starting workflow:', error);
    }
  };

  const checkStatus = async (id: string) => {
    try {
      const response = await fetch(`http://localhost:8081/workflow/status?id=${id}`);
      const status = await response.text();
      setWorkflows(workflows.map(w => w.id === id ? { ...w, status } : w));
    } catch (error) {
      console.error('Error checking status:', error);
    }
  };

  const startComplianceWorkflow = async () => {
    try {
      const response = await fetch('http://localhost:8081/workflow/start-compliance', { method: 'POST' });
      const id = await response.text();
      setComplianceWorkflows([...complianceWorkflows, { id, status: 'Running' }]);
    } catch (error) {
      console.error('Error starting compliance workflow:', error);
    }
  };

  const checkComplianceStatus = async (id: string) => {
    try {
      const response = await fetch(`http://localhost:8081/workflow/status?id=${id}`);
      const status = await response.text();
      setComplianceWorkflows(complianceWorkflows.map(w => w.id === id ? { ...w, status } : w));
    } catch (error) {
      console.error('Error checking compliance status:', error);
    }
  };

  const sendApproval = async (id: string, approval: string) => {
    try {
      await fetch(`http://localhost:8081/workflow/signal/${id}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ signal: 'human-approval', value: approval }),
      });
      // Optionally update status or remove from list
      setComplianceWorkflows(complianceWorkflows.map(w => w.id === id ? { ...w, status: 'Completed' } : w));
    } catch (error) {
      console.error('Error sending approval:', error);
    }
  };

  return (
    <div>
      <Typography variant="h4">Temporal AI Agent Integration</Typography>
      
      <Box sx={{ borderBottom: 1, borderColor: 'divider', mt: 3 }}>
        <Tabs value={tabValue} onChange={handleTabChange}>
          <Tab label="Basic Workflows" />
          <Tab label="AI Agent Builder" />
          <Tab label="Monitoring Dashboard" />
          <Tab label="Compliance Workflows" />
          <Tab label="Human Approvals" />
        </Tabs>
      </Box>

      <TabPanel value={tabValue} index={0}>
        <Typography variant="h6" gutterBottom>
          Basic Workflow Management
        </Typography>
        <Button variant="contained" color="primary" onClick={startWorkflow}>Start Basic Workflow</Button>
        <Table sx={{ mt: 2 }}>
          <TableHead>
            <TableRow>
              <TableCell>ID</TableCell>
              <TableCell>Status</TableCell>
              <TableCell>Actions</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {workflows.map(w => (
              <TableRow key={w.id}>
                <TableCell>{w.id}</TableCell>
                <TableCell>{w.status}</TableCell>
                <TableCell>
                  <Button onClick={() => checkStatus(w.id)}>Check Status</Button>
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </TabPanel>

      <TabPanel value={tabValue} index={1}>
        <AIAgentWorkflowBuilder />
      </TabPanel>

      <TabPanel value={tabValue} index={2}>
        <MonitoringDashboard />
      </TabPanel>

      <TabPanel value={tabValue} index={3}>
        <Typography variant="h6" gutterBottom>
          Compliance Workflow Management
        </Typography>
        <Button variant="contained" color="primary" onClick={startComplianceWorkflow}>Start Compliance Check</Button>
        <Table sx={{ mt: 2 }}>
          <TableHead>
            <TableRow>
              <TableCell>ID</TableCell>
              <TableCell>Status</TableCell>
              <TableCell>Actions</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {complianceWorkflows.map(w => (
              <TableRow key={w.id}>
                <TableCell>{w.id}</TableCell>
                <TableCell>{w.status}</TableCell>
                <TableCell>
                  <Button onClick={() => checkComplianceStatus(w.id)}>Check Status</Button>
                  {w.status === 'Running' && (
                    <>
                      <Button onClick={() => sendApproval(w.id, 'Approved')}>Approve</Button>
                      <Button onClick={() => sendApproval(w.id, 'Rejected')}>Reject</Button>
                    </>
                  )}
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </TabPanel>

      <TabPanel value={tabValue} index={4}>
        <HumanInTheLoopApprovals />
      </TabPanel>
    </div>
  );
};

export { TemporalPage };
