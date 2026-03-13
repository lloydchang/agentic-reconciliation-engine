import React, { useState, useEffect } from 'react';
import {
  Card,
  CardContent,
  CardActions,
  Button,
  TextField,
  Typography,
  Box,
  Chip,
  Alert,
  CircularProgress,
  Paper,
  Divider,
  Grid,
} from '@mui/material';
import {
  Send as SendIcon,
  SmartToy as BotIcon,
  Person as PersonIcon,
  Search as SearchIcon,
  Lightbulb as InsightIcon,
} from '@mui/icons-material';
import { useApi } from '@backstage/core-plugin-api';

interface Message {
  id: string;
  content: string;
  sender: 'user' | 'assistant';
  timestamp: Date;
  sources?: string[];
}

interface ToolCall {
  toolName: string;
  parameters: Record<string, any>;
  result?: Record<string, any>;
  error?: string;
  duration: number;
}

interface RagAIResponse {
  message: string;
  sources: string[];
  toolCalls: ToolCall[];
  confidence: number;
  processingTime: number;
}

export const RagAIPage = () => {
  const [messages, setMessages] = useState<Message[]>([]);
  const [inputValue, setInputValue] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [availableTools, setAvailableTools] = useState<string[]>([]);
  const [categories, setCategories] = useState<string[]>([]);
  const [selectedCategory, setSelectedCategory] = useState<string>('all');
  const api = useApi();

  useEffect(() => {
    // Load available tools and categories
    loadToolsAndCategories();
  }, []);

  const loadToolsAndCategories = async () => {
    try {
      // Load tools
      const toolsResponse = await fetch('/api/mcp/tools');
      const toolsData = await toolsResponse.json();
      setAvailableTools(toolsData.tools.map((tool: any) => tool.name));

      // Load categories
      const categoriesResponse = await fetch('/api/mcp/categories');
      const categoriesData = await categoriesResponse.json();
      setCategories(categoriesData.categories);
    } catch (err) {
      console.error('Failed to load tools and categories:', err);
    }
  };

  const handleSendMessage = async () => {
    if (!inputValue.trim()) return;

    const userMessage: Message = {
      id: Date.now().toString(),
      content: inputValue,
      sender: 'user',
      timestamp: new Date(),
    };

    setMessages(prev => [...prev, userMessage]);
    setInputValue('');
    setIsLoading(true);
    setError(null);

    try {
      // Call RAG AI API
      const response = await fetch('/api/rag-ai/chat', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          message: inputValue,
          category: selectedCategory !== 'all' ? selectedCategory : undefined,
          includeSources: true,
          maxTokens: 1000,
        }),
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data: RagAIResponse = await response.json();

      const assistantMessage: Message = {
        id: (Date.now() + 1).toString(),
        content: data.message,
        sender: 'assistant',
        timestamp: new Date(),
        sources: data.sources,
      };

      setMessages(prev => [...prev, assistantMessage]);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to send message');
      console.error('Error sending message:', err);
    } finally {
      setIsLoading(false);
    }
  };

  const handleKeyPress = (event: React.KeyboardEvent) => {
    if (event.key === 'Enter' && !event.shiftKey) {
      event.preventDefault();
      handleSendMessage();
    }
  };

  const clearConversation = () => {
    setMessages([]);
    setError(null);
  };

  const renderMessage = (message: Message) => (
    <Box
      key={message.id}
      sx={{
        display: 'flex',
        justifyContent: message.sender === 'user' ? 'flex-end' : 'flex-start',
        mb: 2,
      }}
    >
      <Box
        sx={{
          maxWidth: '70%',
          display: 'flex',
          alignItems: 'flex-start',
          gap: 1,
        }}
      >
        {message.sender === 'assistant' && (
          <BotIcon color="primary" sx={{ mt: 1 }} />
        )}
        <Paper
          elevation={2}
          sx={{
            p: 2,
            backgroundColor: message.sender === 'user' ? 'primary.main' : 'grey.100',
            color: message.sender === 'user' ? 'white' : 'text.primary',
            borderRadius: 2,
          }}
        >
          <Typography variant="body1">{message.content}</Typography>
          {message.sources && message.sources.length > 0 && (
            <Box sx={{ mt: 1 }}>
              <Typography variant="caption" sx={{ fontWeight: 'bold' }}>
                Sources:
              </Typography>
              {message.sources.map((source, index) => (
                <Chip
                  key={index}
                  label={source}
                  size="small"
                  variant="outlined"
                  sx={{ mr: 0.5, mt: 0.5 }}
                />
              ))}
            </Box>
          )}
          <Typography variant="caption" sx={{ mt: 1, display: 'block', opacity: 0.7 }}>
            {message.timestamp.toLocaleTimeString()}
          </Typography>
        </Paper>
        {message.sender === 'user' && (
          <PersonIcon sx={{ mt: 1, color: 'text.secondary' }} />
        )}
      </Box>
    </Box>
  );

  return (
    <Box sx={{ height: '100vh', display: 'flex', flexDirection: 'column', p: 2 }}>
      <Typography variant="h4" gutterBottom>
        RAG AI Assistant
      </Typography>
      <Typography variant="body1" color="text.secondary" gutterBottom>
        Ask questions about your catalog, documentation, and more. The AI will provide answers based on your organization's data.
      </Typography>

      <Grid container spacing={2} sx={{ mb: 2 }}>
        <Grid item xs={12} md={8}>
          <Card>
            <CardContent sx={{ height: '60vh', overflowY: 'auto', pb: 1 }}>
              {messages.length === 0 ? (
                <Box
                  sx={{
                    display: 'flex',
                    flexDirection: 'column',
                    alignItems: 'center',
                    justifyContent: 'center',
                    height: '100%',
                    color: 'text.secondary',
                  }}
                >
                  <BotIcon sx={{ fontSize: 64, mb: 2 }} />
                  <Typography variant="h6">Ask me anything!</Typography>
                  <Typography variant="body2">
                    I can help you with information from your catalog, documentation, and other sources.
                  </Typography>
                </Box>
              ) : (
                messages.map(renderMessage)
              )}
              {isLoading && (
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, mt: 2 }}>
                  <CircularProgress size={20} />
                  <Typography variant="body2">Thinking...</Typography>
                </Box>
              )}
            </CardContent>
            <Divider />
            <CardActions sx={{ p: 2 }}>
              <TextField
                fullWidth
                multiline
                maxRows={3}
                placeholder="Ask a question..."
                value={inputValue}
                onChange={(e) => setInputValue(e.target.value)}
                onKeyPress={handleKeyPress}
                disabled={isLoading}
                variant="outlined"
                size="small"
              />
              <Button
                variant="contained"
                onClick={handleSendMessage}
                disabled={!inputValue.trim() || isLoading}
                startIcon={<SendIcon />}
              >
                Send
              </Button>
              <Button
                variant="outlined"
                onClick={clearConversation}
                disabled={messages.length === 0}
              >
                Clear
              </Button>
            </CardActions>
          </Card>
        </Grid>

        <Grid item xs={12} md={4}>
          <Card sx={{ mb: 2 }}>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                <SearchIcon sx={{ mr: 1, verticalAlign: 'middle' }} />
                Available Tools
              </Typography>
              <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 0.5 }}>
                {availableTools.map((tool) => (
                  <Chip
                    key={tool}
                    label={tool}
                    size="small"
                    variant="outlined"
                    color="primary"
                  />
                ))}
              </Box>
            </CardContent>
          </Card>

          <Card sx={{ mb: 2 }}>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                <InsightIcon sx={{ mr: 1, verticalAlign: 'middle' }} />
                Categories
              </Typography>
              <Box sx={{ display: 'flex', flexDirection: 'column', gap: 0.5 }}>
                <Chip
                  label="All"
                  onClick={() => setSelectedCategory('all')}
                  color={selectedCategory === 'all' ? 'primary' : 'default'}
                  variant={selectedCategory === 'all' ? 'filled' : 'outlined'}
                  clickable
                />
                {categories.map((category) => (
                  <Chip
                    key={category}
                    label={category}
                    onClick={() => setSelectedCategory(category)}
                    color={selectedCategory === category ? 'primary' : 'default'}
                    variant={selectedCategory === category ? 'filled' : 'outlined'}
                    clickable
                  />
                ))}
              </Box>
            </CardContent>
          </Card>

          {error && (
            <Alert severity="error" onClose={() => setError(null)}>
              {error}
            </Alert>
          )}
        </Grid>
      </Grid>
    </Box>
  );
};
