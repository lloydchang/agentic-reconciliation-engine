import React, { useState, useRef, useEffect } from 'react';
import {
  Content,
  Header,
  Page,
} from '@backstage/core-components';
import {
  Button,
  Grid,
  Paper,
  Typography,
  IconButton,
  Box,
  Toolbar,
  AppBar,
  useTheme,
  useMediaQuery,
} from '@mui/material';
import {
  ViewColumn,
  OpenInNew,
} from '@mui/icons-material';
import { useApi } from '@backstage/core-plugin-api';
import { configApiRef } from '@backstage/core-plugin-api';

interface SplitScreenPageProps {
  temporalUrl?: string;
}

export const SplitScreenPage: React.FC<SplitScreenPageProps> = ({ 
  temporalUrl = 'http://localhost:8080' 
}) => {
  const [isSplitScreen, setIsSplitScreen] = useState(true);
  const [showTemporalOnly, setShowTemporalOnly] = useState(false);
  const [showBackstageOnly, setShowBackstageOnly] = useState(false);
  const [temporalFrameKey, setTemporalFrameKey] = useState(Date.now());
  const iframeRef = useRef<HTMLIFrameElement>(null);
  const theme = useTheme();
  const isMobile = useMediaQuery(theme.breakpoints.down('md'));

  // Use the backend proxy to bypass X-Frame-Options: sameorigin
  // Use absolute URL to the Go backend proxy to bypass dev server 404s
  const actualTemporalUrl = 'http://localhost:8081/api/temporal-proxy/';

  useEffect(() => {
    // Reset iframe when toggling views to prevent caching issues
    setTemporalFrameKey(Date.now());
  }, [isSplitScreen, showTemporalOnly, showBackstageOnly]);

  const handleToggleSplitScreen = () => {
    setIsSplitScreen(!isSplitScreen);
    setShowTemporalOnly(false);
    setShowBackstageOnly(false);
  };

  const handleShowTemporalOnly = () => {
    setShowTemporalOnly(true);
    setShowBackstageOnly(false);
    setIsSplitScreen(false);
  };

  const handleShowBackstageOnly = () => {
    setShowBackstageOnly(true);
    setShowTemporalOnly(false);
    setIsSplitScreen(false);
  };

  const handleOpenTemporalNewTab = () => {
    window.open(actualTemporalUrl, '_blank');
  };

  const renderToolbar = () => (
    <AppBar position="static" color="default" elevation={1}>
      <Toolbar variant="dense">
        <Typography variant="h6" sx={{ flexGrow: 1 }}>
          Backstage + Temporal Integration
        </Typography>
        
        <Box sx={{ display: 'flex', gap: 1, alignItems: 'center' }}>
          <Button
            size="small"
            variant={isSplitScreen ? "contained" : "outlined"}
            startIcon={<ViewColumn />}
            onClick={handleToggleSplitScreen}
            disabled={isMobile}
          >
            Split View
          </Button>
          
          <Button
            size="small"
            variant={showBackstageOnly ? "contained" : "outlined"}
            onClick={handleShowBackstageOnly}
          >
            Backstage
          </Button>
          
          <Button
            size="small"
            variant={showTemporalOnly ? "contained" : "outlined"}
            onClick={handleShowTemporalOnly}
            endIcon={<OpenInNew />}
          >
            Temporal
          </Button>
          
          <IconButton
            size="small"
            onClick={handleOpenTemporalNewTab}
            title="Open Temporal in new tab"
          >
            <OpenInNew fontSize="small" />
          </IconButton>
        </Box>
      </Toolbar>
    </AppBar>
  );

  const renderBackstagePanel = () => (
    <Paper
      sx={{
        height: 'calc(100vh - 120px)',
        display: 'flex',
        flexDirection: 'column',
        overflow: 'hidden',
      }}
    >
      <Box sx={{ p: 2, borderBottom: 1, borderColor: 'divider' }}>
        <Typography variant="h6">Backstage Catalog</Typography>
        <Typography variant="body2" color="textSecondary">
          Software catalog and component management
        </Typography>
      </Box>
      
      <Box sx={{ flex: 1, overflow: 'auto', p: 2 }}>
        <iframe
          src="/catalog"
          style={{
            width: '100%',
            height: '100%',
            border: 'none',
            borderRadius: theme.shape.borderRadius,
          }}
          title="Backstage Catalog"
        />
      </Box>
    </Paper>
  );

  const renderTemporalPanel = () => (
    <Paper
      sx={{
        height: 'calc(100vh - 120px)',
        display: 'flex',
        flexDirection: 'column',
        overflow: 'hidden',
      }}
    >
      <Box sx={{ p: 2, borderBottom: 1, borderColor: 'divider' }}>
        <Typography variant="h6">Temporal Workflows</Typography>
        <Typography variant="body2" color="textSecondary">
          Workflow execution and monitoring
        </Typography>
      </Box>
      
      <Box sx={{ flex: 1, overflow: 'hidden' }}>
        <iframe
          ref={iframeRef}
          key={temporalFrameKey}
          src={actualTemporalUrl}
          style={{
            width: '100%',
            height: '100%',
            border: 'none',
            borderRadius: theme.shape.borderRadius,
          }}
          title="Temporal Web UI"
          sandbox="allow-scripts allow-same-origin allow-forms allow-popups"
        />
      </Box>
    </Paper>
  );

  const renderContent = () => {
    // Mobile: always show single view with toggle
    if (isMobile) {
      return (
        <Box sx={{ mt: 2 }}>
          <Paper sx={{ p: 2, mb: 2 }}>
            <Typography variant="body1" gutterBottom>
              Mobile View: Select which interface to view
            </Typography>
            <Box sx={{ display: 'flex', gap: 1, mt: 2 }}>
              <Button
                variant={showBackstageOnly ? "contained" : "outlined"}
                onClick={handleShowBackstageOnly}
                fullWidth
              >
                Backstage
              </Button>
              <Button
                variant={showTemporalOnly ? "contained" : "outlined"}
                onClick={handleShowTemporalOnly}
                fullWidth
              >
                Temporal
              </Button>
            </Box>
          </Paper>
          
          {(showBackstageOnly || (!showTemporalOnly && !showBackstageOnly)) && renderBackstagePanel()}
          {showTemporalOnly && renderTemporalPanel()}
        </Box>
      );
    }

    // Desktop: split-screen or single view
    if (isSplitScreen) {
      return (
        <Grid container spacing={2} sx={{ mt: 2, height: 'calc(100vh - 120px)' }}>
          <Grid item xs={12} md={6}>
            {renderBackstagePanel()}
          </Grid>
          <Grid item xs={12} md={6}>
            {renderTemporalPanel()}
          </Grid>
        </Grid>
      );
    }

    // Single view
    return (
      <Box sx={{ mt: 2 }}>
        {showBackstageOnly && renderBackstagePanel()}
        {showTemporalOnly && renderTemporalPanel()}
        {!showBackstageOnly && !showTemporalOnly && renderBackstagePanel()}
      </Box>
    );
  };

  return (
    <Page themeId="tool">
      <Header title="Split Screen Integration" />
      <Content>
        {renderToolbar()}
        {renderContent()}
      </Content>
    </Page>
  );
};
