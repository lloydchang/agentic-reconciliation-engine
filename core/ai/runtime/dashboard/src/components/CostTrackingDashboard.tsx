import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Progress } from '@/components/ui/progress';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, BarChart, Bar, PieChart, Pie, Cell } from 'recharts';

interface CostSummary {
  totalCost: number;
  totalTokens: number;
  skillCosts: Record<string, number>;
  modelCosts: Record<string, number>;
  dailyCost: number;
  monthlyCost: number;
  costSavings: number;
  executionCount: number;
  successRate: number;
}

interface UsageRecord {
  skillName: string;
  modelUsed: string;
  inputTokens: number;
  outputTokens: number;
  executionTime: string;
  cost: number;
  userId: string;
  sessionId: string;
  success: boolean;
  errorMessage?: string;
}

const CostTrackingDashboard: React.FC = () => {
  const [summary, setSummary] = useState<CostSummary | null>(null);
  const [usage, setUsage] = useState<UsageRecord[]>([]);
  const [loading, setLoading] = useState(true);
  const [selectedSkill, setSelectedSkill] = useState<string>('');
  const [timeRange, setTimeRange] = useState<number>(7);

  useEffect(() => {
    fetchCostData();
    const interval = setInterval(fetchCostData, 30000); // Refresh every 30 seconds
    return () => clearInterval(interval);
  }, [selectedSkill, timeRange]);

  const fetchCostData = async () => {
    try {
      setLoading(true);
      const [summaryResponse, usageResponse] = await Promise.all([
        fetch(`/api/cost/summary?skill=${selectedSkill}&days=${timeRange}`),
        fetch(`/api/cost/usage?skill=${selectedSkill}&days=${timeRange}`)
      ]);

      const summaryData = await summaryResponse.json();
      const usageData = await usageResponse.json();

      setSummary(summaryData);
      setUsage(usageData);
    } catch (error) {
      console.error('Failed to fetch cost data:', error);
    } finally {
      setLoading(false);
    }
  };

  const formatCurrency = (amount: number) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      minimumFractionDigits: 4,
      maximumFractionDigits: 4
    }).format(amount);
  };

  const formatTokens = (tokens: number) => {
    if (tokens >= 1000000) {
      return `${(tokens / 1000000).toFixed(1)}M`;
    } else if (tokens >= 1000) {
      return `${(tokens / 1000).toFixed(1)}K`;
    }
    return tokens.toString();
  };

  const getCostLevel = (cost: number) => {
    if (cost > 1.0) return { level: 'high', color: 'bg-red-500' };
    if (cost > 0.5) return { level: 'medium', color: 'bg-yellow-500' };
    return { level: 'low', color: 'bg-green-500' };
  };

  const skillCostData = Object.entries(summary?.skillCosts || {}).map(([skill, cost]) => ({
    skill,
    cost,
    percentage: summary ? (cost / summary.totalCost) * 100 : 0
  }));

  const modelCostData = Object.entries(summary?.modelCosts || {}).map(([model, cost]) => ({
    model: model.includes('local') ? 'Local' : 'External',
    cost,
    percentage: summary ? (cost / summary.totalCost) * 100 : 0
  }));

  const dailyTrendData = usage.reduce((acc: any[], record) => {
    const date = new Date(record.executionTime).toLocaleDateString();
    const existing = acc.find(item => item.date === date);
    if (existing) {
      existing.cost += record.cost;
      existing.tokens += record.inputTokens + record.outputTokens;
    } else {
      acc.push({
        date,
        cost: record.cost,
        tokens: record.inputTokens + record.outputTokens
      });
    }
    return acc;
  }, []);

  const COLORS = ['#0088FE', '#00C49F', '#FFBB28', '#FF8042', '#8884D8'];

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  if (!summary) {
    return (
      <Alert>
        <AlertDescription>
          No cost data available. Start executing AI skills to see cost tracking information.
        </AlertDescription>
      </Alert>
    );
  }

  const costLevel = getCostLevel(summary.dailyCost);

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex justify-between items-center">
        <h1 className="text-3xl font-bold">AI Cost Tracking</h1>
        <div className="flex space-x-2">
          <select
            value={timeRange}
            onChange={(e) => setTimeRange(Number(e.target.value))}
            className="px-3 py-2 border rounded-md"
          >
            <option value={1}>Last 24 hours</option>
            <option value={7}>Last 7 days</option>
            <option value={30}>Last 30 days</option>
            <option value={90}>Last 90 days</option>
          </select>
          <select
            value={selectedSkill}
            onChange={(e) => setSelectedSkill(e.target.value)}
            className="px-3 py-2 border rounded-md"
          >
            <option value="">All Skills</option>
            {Object.keys(summary.skillCosts).map(skill => (
              <option key={skill} value={skill}>{skill}</option>
            ))}
          </select>
        </div>
      </div>

      {/* Cost Alerts */}
      {summary.dailyCost > 0.5 && (
        <Alert className={costLevel.level === 'high' ? 'border-red-500' : 'border-yellow-500'}>
          <AlertDescription>
            Daily cost {costLevel.level === 'high' ? 'exceeds recommended limit' : 'approaching limit'}: {formatCurrency(summary.dailyCost)}
          </AlertDescription>
        </Alert>
      )}

      {/* Summary Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Total Cost</CardTitle>
            <div className={`h-2 w-2 rounded-full ${costLevel.color}`}></div>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{formatCurrency(summary.totalCost)}</div>
            <p className="text-xs text-muted-foreground">
              Last {timeRange} days
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Total Tokens</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{formatTokens(summary.totalTokens)}</div>
            <p className="text-xs text-muted-foreground">
              Input + Output
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Executions</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{summary.executionCount}</div>
            <p className="text-xs text-muted-foreground">
              Success rate: {(summary.successRate * 100).toFixed(1)}%
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Cost Savings</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-green-600">{formatCurrency(summary.costSavings)}</div>
            <p className="text-xs text-muted-foreground">
              Using local models
            </p>
          </CardContent>
        </Card>
      </div>

      {/* Charts */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Daily Cost Trend */}
        <Card>
          <CardHeader>
            <CardTitle>Daily Cost Trend</CardTitle>
          </CardHeader>
          <CardContent>
            <ResponsiveContainer width="100%" height={300}>
              <LineChart data={dailyTrendData}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="date" />
                <YAxis />
                <Tooltip formatter={(value) => [formatCurrency(Number(value)), 'Cost']} />
                <Line type="monotone" dataKey="cost" stroke="#8884d8" strokeWidth={2} />
              </LineChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>

        {/* Skill Cost Distribution */}
        <Card>
          <CardHeader>
            <CardTitle>Cost by Skill</CardTitle>
          </CardHeader>
          <CardContent>
            <ResponsiveContainer width="100%" height={300}>
              <PieChart>
                <Pie
                  data={skillCostData}
                  cx="50%"
                  cy="50%"
                  labelLine={false}
                  label={({ skill, percentage }) => `${skill}: ${percentage.toFixed(1)}%`}
                  outerRadius={80}
                  fill="#8884d8"
                  dataKey="cost"
                >
                  {skillCostData.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                  ))}
                </Pie>
                <Tooltip formatter={(value) => [formatCurrency(Number(value)), 'Cost']} />
              </PieChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>

        {/* Model Cost Comparison */}
        <Card>
          <CardHeader>
            <CardTitle>Local vs External Models</CardTitle>
          </CardHeader>
          <CardContent>
            <ResponsiveContainer width="100%" height={300}>
              <BarChart data={modelCostData}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="model" />
                <YAxis />
                <Tooltip formatter={(value) => [formatCurrency(Number(value)), 'Cost']} />
                <Bar dataKey="cost" fill="#82ca9d" />
              </BarChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>

        {/* Cost Progress */}
        <Card>
          <CardHeader>
            <CardTitle>Monthly Budget Progress</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div>
              <div className="flex justify-between text-sm">
                <span>Current Usage</span>
                <span>{formatCurrency(summary.monthlyCost)}</span>
              </div>
              <Progress value={Math.min((summary.monthlyCost / 10) * 100, 100)} className="mt-2" />
              <p className="text-xs text-muted-foreground mt-1">
                Budget: $10.00
              </p>
            </div>
            
            <div>
              <div className="flex justify-between text-sm">
                <span>Daily Average</span>
                <span>{formatCurrency(summary.monthlyCost / 30)}</span>
              </div>
            </div>

            <div>
              <div className="flex justify-between text-sm">
                <span>Projected Monthly</span>
                <span>{formatCurrency(summary.dailyCost * 30)}</span>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Recent Usage Table */}
      <Card>
        <CardHeader>
          <CardTitle>Recent Executions</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b">
                  <th className="text-left p-2">Skill</th>
                  <th className="text-left p-2">Model</th>
                  <th className="text-left p-2">Tokens</th>
                  <th className="text-left p-2">Cost</th>
                  <th className="text-left p-2">Time</th>
                  <th className="text-left p-2">Status</th>
                </tr>
              </thead>
              <tbody>
                {usage.slice(0, 10).map((record, index) => (
                  <tr key={index} className="border-b">
                    <td className="p-2">{record.skillName}</td>
                    <td className="p-2">
                      <Badge variant={record.modelUsed.includes('local') ? 'default' : 'secondary'}>
                        {record.modelUsed.includes('local') ? 'Local' : 'External'}
                      </Badge>
                    </td>
                    <td className="p-2">{formatTokens(record.inputTokens + record.outputTokens)}</td>
                    <td className="p-2">{formatCurrency(record.cost)}</td>
                    <td className="p-2">{new Date(record.executionTime).toLocaleString()}</td>
                    <td className="p-2">
                      <Badge variant={record.success ? 'default' : 'destructive'}>
                        {record.success ? 'Success' : 'Failed'}
                      </Badge>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </CardContent>
      </Card>
    </div>
  );
};

export default CostTrackingDashboard;
