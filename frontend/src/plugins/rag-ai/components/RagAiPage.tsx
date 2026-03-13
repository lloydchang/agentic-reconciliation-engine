import React, { useState } from 'react';
import {
  Page,
  Header,
  Content,
  ContentHeader,
  SupportButton,
} from '@backstage/core-components';
import {
  Grid,
  Card,
  CardContent,
  Typography,
  TextField,
  Button,
  Box,
  Chip,
  List,
  ListItem,
  ListItemText,
  Divider,
} from '@mui/material';
// import { useApi } from '@backstage/core-plugin-api';
// import { ragAiApiRef } from '@roadiehq/rag-ai';

export const RagAiPage = () => {

  const handleSearch = async () => {
    if (!query.trim()) return;

    setIsLoading(true);
    try {
      // Mock implementation - would use actual RAG AI API
      const mockResults = [
        {
          id: '1',
          title: 'Temporal Workflow Documentation',
          content: 'Learn about durable workflows and activities...',
          score: 0.95,
          source: 'techdocs',
        },
        {
          id: '2',
          title: 'AI Agent Integration Guide',
          content: 'How to integrate AI agents with Temporal...',
          score: 0.89,
          source: 'catalog',
        },
      ];

      setResults(mockResults);
    } catch (error) {
      console.error('Search failed:', error);
    } finally {
      setIsLoading(false);
    }
  };

  const getSourceColor = (source: string) => {
    switch (source) {
      case 'techdocs': return 'primary';
      case 'catalog': return 'secondary';
      default: return 'default';
    }
  };

  return (
    <Page themeId="tool">
      <Header
        title="RAG AI Assistant"
        subtitle="Retrieval-Augmented Generation powered AI assistant"
      >
        <SupportButton>
          RAG AI provides intelligent search and assistance powered by your documentation and catalog data.
        </SupportButton>
      </Header>

      <Content>
        <ContentHeader title="Ask the AI Assistant">
          <Typography variant="body2">
            Search through your technical documentation, catalog entities, and organizational knowledge.
          </Typography>
        </ContentHeader>

        <Grid container spacing={3}>
          <Grid item xs={12}>
            <Card>
              <CardContent>
                <Box display="flex" gap={2} mb={2}>
                  <TextField
                    fullWidth
                    label="Ask a question or search for information"
                    variant="outlined"
                    value={query}
                    onChange={(e) => setQuery(e.target.value)}
                    onKeyPress={(e) => {
                      if (e.key === 'Enter') {
                        handleSearch();
                      }
                    }}
                    placeholder="How do I create a Temporal workflow?"
                  />
                  <Button
                    variant="contained"
                    onClick={handleSearch}
                    disabled={isLoading || !query.trim()}
                    sx={{ minWidth: 120 }}
                  >
                    {isLoading ? 'Searching...' : 'Search'}
                  </Button>
                </Box>

                {results.length > 0 && (
                  <Box>
                    <Typography variant="h6" gutterBottom>
                      Results ({results.length})
                    </Typography>
                    <List>
                      {results.map((result, index) => (
                        <React.Fragment key={result.id}>
                          <ListItem alignItems="flex-start">
                            <ListItemText
                              primary={
                                <Box display="flex" alignItems="center" gap={1}>
                                  <Typography variant="subtitle1">
                                    {result.title}
                                  </Typography>
                                  <Chip
                                    label={result.source}
                                    size="small"
                                    color={getSourceColor(result.source)}
                                    variant="outlined"
                                  />
                                  <Chip
                                    label={`Score: ${(result.score * 100).toFixed(0)}%`}
                                    size="small"
                                    variant="filled"
                                  />
                                </Box>
                              }
                              secondary={
                                <Typography variant="body2" color="text.secondary">
                                  {result.content}
                                </Typography>
                              }
                            />
                          </ListItem>
                          {index < results.length - 1 && <Divider component="li" />}
                        </React.Fragment>
                      ))}
                    </List>
                  </Box>
                )}
              </CardContent>
            </Card>
          </Grid>

          <Grid item xs={12} md={6}>
            <Card>
              <CardContent>
                <Typography variant="h6" gutterBottom>
                  Content Sources
                </Typography>
                <Box display="flex" flexWrap="wrap" gap={1}>
                  <Chip label="TechDocs" color="primary" />
                  <Chip label="Catalog" color="secondary" />
                  <Chip label="Custom Sources" variant="outlined" />
                </Box>
                <Typography variant="body2" sx={{ mt: 2 }}>
                  The RAG AI assistant searches through your technical documentation,
                  service catalog, and other configured knowledge sources to provide
                  accurate and contextual answers.
                </Typography>
              </CardContent>
            </Card>
          </Grid>

          <Grid item xs={12} md={6}>
            <Card>
              <CardContent>
                <Typography variant="h6" gutterBottom>
                  Configuration
                </Typography>
                <Typography variant="body2" paragraph>
                  RAG AI is configured with:
                </Typography>
                <Box component="ul" sx={{ pl: 2 }}>
                  <li>OpenAI embeddings for semantic search</li>
                  <li>AWS Bedrock embeddings as alternative</li>
                  <li>PostgreSQL with pgvector for vector storage</li>
                  <li>Hybrid retrieval with re-ranking</li>
                </Box>
                <Typography variant="body2" sx={{ mt: 2 }}>
                  Embeddings are automatically generated and updated as your
                  documentation and catalog change.
                </Typography>
              </CardContent>
            </Card>
          </Grid>
        </Grid>
      </Content>
    </Page>
  );
};
