import React, { useState, useEffect } from 'react';
import {
  Box,
  Card,
  CardContent,
  Typography,
  Button,
  Grid,
  Chip,
  Alert,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  TextField,
  FormControlLabel,
  Switch,
  Accordion,
  AccordionSummary,
  AccordionDetails,
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableRow,
  TableContainer,
  Paper,
} from '@mui/material';
import {
  CheckCircle,
  Cancel,
  Schedule,
  ExpandMore,
  Security,
  Gavel,
  Savings,
  Assessment,
  Person,
} from '@mui/icons-material';

interface PendingApproval {
  id: string;
  workflowId: string;
  type: 'security' | 'compliance' | 'cost-optimization' | 'aggregation';
  title: string;
  description: string;
  findings: string[];
  riskLevel: 'Low' | 'Medium' | 'High' | 'Critical';
  requestedAt: string;
  dueBy?: string;
  requester: string;
  priority: 'Low' | 'Medium' | 'High' | 'Critical';
  agentResults: AgentResult[];
  aggregatedScore: number;
}

interface AgentResult {
  agentId: string;
  agentType: string;
  score: number;
  findings: string[];
  recommendations: string[];
}

interface ApprovalDecision {
  approved: boolean;
  comments: string;
  reviewerId: string;
  reviewedAt: string;
}

const HumanInTheLoopApprovals: React.FC = () => {
  const [pendingApprovals, setPendingApprovals] = useState<PendingApproval[]>([]);
  const [selectedApproval, setSelectedApproval] = useState<PendingApproval | null>(null);
  const [decision, setDecision] = useState<ApprovalDecision>({
    approved: false,
    comments: '',
    reviewerId: 'user@company.com',
    reviewedAt: new Date().toISOString(),
  });
  const [showDecisionDialog, setShowDecisionDialog] = useState(false);
  const [autoApprovalEnabled, setAutoApprovalEnabled] = useState(false);

  useEffect(() => {
    fetchPendingApprovals();
    const interval = setInterval(fetchPendingApprovals, 30000); // Refresh every 30 seconds
    return () => clearInterval(interval);
  }, [autoApprovalEnabled]); // Re-fetch when auto-approval setting changes

  const fetchPendingApprovals = async () => {
    try {
      const response = await fetch('http://localhost:8081/approvals/pending');
      if (response.ok) {
        const data = await response.json();
        let filteredData = data;
        
        // Auto-approve high confidence findings if enabled
        if (autoApprovalEnabled) {
          const autoApprovable = data.filter((approval: PendingApproval) => 
            approval.aggregatedScore >= 95.0 && 
            approval.riskLevel === 'Low' && 
            approval.priority === 'Low'
          );
          
          // Auto-approve in background
          autoApprovable.forEach((approval: PendingApproval) => {
            submitAutoApproval(approval);
          });
          
          // Filter out auto-approved items
          filteredData = data.filter((approval: PendingApproval) => 
            !autoApprovable.some((auto: PendingApproval) => auto.id === approval.id)
          );
        }
        
        setPendingApprovals(filteredData);
      }
    } catch (error) {
      console.error('Error fetching pending approvals:', error);
    }
  };

  const submitAutoApproval = async (approval: PendingApproval) => {
    try {
      const autoDecision: ApprovalDecision = {
        approved: true,
        comments: 'Auto-approved: High confidence score (>95) with low risk and priority',
        reviewerId: 'system-auto-approval',
        reviewedAt: new Date().toISOString(),
      };

      await fetch(`http://localhost:8081/approvals/${approval.id}/decide`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(autoDecision),
      });
    } catch (error) {
      console.error('Error in auto-approval:', error);
    }
  };

  const handleApprovalDecision = (approval: PendingApproval, approved: boolean) => {
    setSelectedApproval(approval);
    setDecision({
      ...decision,
      approved,
      reviewedAt: new Date().toISOString(),
    });
    setShowDecisionDialog(true);
  };

  const submitDecision = async () => {
    if (!selectedApproval) return;

    try {
      const response = await fetch(`http://localhost:8081/approvals/${selectedApproval.id}/decide`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(decision),
      });

      if (response.ok) {
        setPendingApprovals(pendingApprovals.filter(a => a.id !== selectedApproval.id));
        setShowDecisionDialog(false);
        setSelectedApproval(null);
      }
    } catch (error) {
      console.error('Error submitting decision:', error);
    }
  };

  const getRiskColor = (risk: string): 'success' | 'warning' | 'error' | 'default' => {
    switch (risk) {
      case 'Low': return 'success';
      case 'Medium': return 'warning';
      case 'High': return 'error';
      case 'Critical': return 'error';
      default: return 'default';
    }
  };

  const getPriorityColor = (priority: string): 'success' | 'warning' | 'error' | 'default' => {
    switch (priority) {
      case 'Low': return 'success';
      case 'Medium': return 'warning';
      case 'High': return 'error';
      case 'Critical': return 'error';
      default: return 'default';
    }
  };

  const getAgentIcon = (agentType: string) => {
    switch (agentType) {
      case 'Security': return <Security />;
      case 'Compliance': return <Gavel />;
      case 'CostOptimization': return <Savings />;
      default: return <Assessment />;
    }
  };

  const isOverdue = (dueBy?: string): boolean => {
    if (!dueBy) return false;
    return new Date(dueBy) < new Date();
  };

  return (
    <Box sx={{ p: 3 }}>
      <Box display="flex" justifyContent="space-between" alignItems="center" mb={3}>
        <Typography variant="h4">
          Human-in-the-Loop Approvals
        </Typography>
        <FormControlLabel
          control={
            <Switch
              checked={autoApprovalEnabled}
              onChange={(e) => setAutoApprovalEnabled(e.target.checked)}
              color="primary"
            />
          }
          label="Enable Auto-Approval (High Confidence Only)"
        />
      </Box>

      <Alert severity="info" sx={{ mb: 3 }}>
        Review and approve AI agent findings for compliance workflows. {pendingApprovals.length} pending approval{pendingApprovals.length !== 1 ? 's' : ''}.
      </Alert>

      {pendingApprovals.length === 0 ? (
        <Card>
          <CardContent>
            <Box textAlign="center" py={4}>
              <CheckCircle sx={{ fontSize: 48, color: 'success.main', mb: 2 }} />
              <Typography variant="h6" color="text.secondary">
                No Pending Approvals
              </Typography>
              <Typography variant="body2" color="text.secondary">
                All AI agent findings have been processed or auto-approved.
              </Typography>
            </Box>
          </CardContent>
        </Card>
      ) : (
        <Grid container spacing={3}>
          {pendingApprovals.map((approval) => (
            <Grid item xs={12} key={approval.id}>
              <Card sx={{
                border: isOverdue(approval.dueBy) ? '2px solid #f44336' : '1px solid #e0e0e0',
                backgroundColor: isOverdue(approval.dueBy) ? '#fff5f5' : 'white'
              }}>
                <CardContent>
                  <Box display="flex" justifyContent="space-between" alignItems="flex-start" mb={2}>
                    <Box>
                      <Typography variant="h6" gutterBottom>
                        {approval.title}
                      </Typography>
                      <Typography variant="body2" color="text.secondary" gutterBottom>
                        Workflow: {approval.workflowId} • Requested by: {approval.requester}
                      </Typography>
                      <Typography variant="body2" color="text.secondary">
                        Requested: {new Date(approval.requestedAt).toLocaleString()}
                        {approval.dueBy && ` • Due: ${new Date(approval.dueBy).toLocaleString()}`}
                      </Typography>
                    </Box>
                    <Box display="flex" gap={1}>
                      <Chip
                        label={`Risk: ${approval.riskLevel}`}
                        color={getRiskColor(approval.riskLevel)}
                        size="small"
                      />
                      <Chip
                        label={`Priority: ${approval.priority}`}
                        color={getPriorityColor(approval.priority)}
                        size="small"
                      />
                      {isOverdue(approval.dueBy) && (
                        <Chip label="OVERDUE" color="error" size="small" />
                      )}
                    </Box>
                  </Box>

                  <Typography variant="body1" gutterBottom>
                    {approval.description}
                  </Typography>

                  <Box sx={{ mb: 2 }}>
                    <Typography variant="subtitle2" gutterBottom>
                      Overall Score: {approval.aggregatedScore.toFixed(1)}/100
                    </Typography>
                  </Box>

                  {/* Agent Results Summary */}
                  <Accordion sx={{ mb: 2 }}>
                    <AccordionSummary expandIcon={<ExpandMore />}>
                      <Typography variant="subtitle2">
                        Agent Analysis Results ({approval.agentResults.length} agents)
                      </Typography>
                    </AccordionSummary>
                    <AccordionDetails>
                      <TableContainer component={Paper} variant="outlined">
                        <Table size="small">
                          <TableHead>
                            <TableRow>
                              <TableCell>Agent Type</TableCell>
                              <TableCell>Score</TableCell>
                              <TableCell>Key Findings</TableCell>
                              <TableCell>Recommendations</TableCell>
                            </TableRow>
                          </TableHead>
                          <TableBody>
                            {approval.agentResults.map((agent) => (
                              <TableRow key={agent.agentId}>
                                <TableCell>
                                  <Box display="flex" alignItems="center">
                                    {getAgentIcon(agent.agentType)}
                                    <Typography variant="body2" sx={{ ml: 1 }}>
                                      {agent.agentType}
                                    </Typography>
                                  </Box>
                                </TableCell>
                                <TableCell>
                                  <Typography variant="body2">
                                    {agent.score.toFixed(1)}/100
                                  </Typography>
                                </TableCell>
                                <TableCell>
                                  <ul style={{ margin: 0, paddingLeft: '20px' }}>
                                    {agent.findings.slice(0, 2).map((finding, idx) => (
                                      <li key={idx}>
                                        <Typography variant="body2">{finding}</Typography>
                                      </li>
                                    ))}
                                    {agent.findings.length > 2 && (
                                      <li>
                                        <Typography variant="body2" color="text.secondary">
                                          ...and {agent.findings.length - 2} more
                                        </Typography>
                                      </li>
                                    )}
                                  </ul>
                                </TableCell>
                                <TableCell>
                                  <ul style={{ margin: 0, paddingLeft: '20px' }}>
                                    {agent.recommendations.slice(0, 2).map((rec, idx) => (
                                      <li key={idx}>
                                        <Typography variant="body2">{rec}</Typography>
                                      </li>
                                    ))}
                                    {agent.recommendations.length > 2 && (
                                      <li>
                                        <Typography variant="body2" color="text.secondary">
                                          ...and {agent.recommendations.length - 2} more
                                        </Typography>
                                      </li>
                                    )}
                                  </ul>
                                </TableCell>
                              </TableRow>
                            ))}
                          </TableBody>
                        </Table>
                      </TableContainer>
                    </AccordionDetails>
                  </Accordion>

                  {/* Action Buttons */}
                  <Box display="flex" gap={2} justifyContent="flex-end">
                    <Button
                      variant="outlined"
                      color="error"
                      startIcon={<Cancel />}
                      onClick={() => handleApprovalDecision(approval, false)}
                    >
                      Reject
                    </Button>
                    <Button
                      variant="contained"
                      color="success"
                      startIcon={<CheckCircle />}
                      onClick={() => handleApprovalDecision(approval, true)}
                    >
                      Approve
                    </Button>
                  </Box>
                </CardContent>
              </Card>
            </Grid>
          ))}
        </Grid>
      )}

      {/* Decision Dialog */}
      <Dialog open={showDecisionDialog} onClose={() => setShowDecisionDialog(false)} maxWidth="md" fullWidth>
        <DialogTitle>
          {decision.approved ? 'Approve' : 'Reject'} Decision
        </DialogTitle>
        <DialogContent>
          <Typography variant="body1" gutterBottom>
            Please provide comments for your decision:
          </Typography>
          <TextField
            fullWidth
            multiline
            rows={4}
            label="Comments"
            value={decision.comments}
            onChange={(e) => setDecision({ ...decision, comments: e.target.value })}
            placeholder={decision.approved ?
              "Explain your approval reasoning..." :
              "Explain why this was rejected and what needs to be addressed..."
            }
            sx={{ mt: 2 }}
          />
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setShowDecisionDialog(false)}>
            Cancel
          </Button>
          <Button
            onClick={submitDecision}
            variant="contained"
            color={decision.approved ? "success" : "error"}
          >
            {decision.approved ? 'Approve' : 'Reject'}
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
};

export default HumanInTheLoopApprovals;
