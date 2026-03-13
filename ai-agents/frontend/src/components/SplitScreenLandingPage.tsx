import React from 'react';
import { Grid, Paper, Typography, Button, Box } from '@mui/material';
import {
  Extension,
  ViewQuilt,
  Autorenew,
  LibraryBooks,
} from '@mui/icons-material';

export const SplitScreenLandingPage: React.FC = () => {
  const features = [
    {
      icon: <Extension fontSize="large" />,
      title: 'AI Agent Skills',
      description: '.agents/skills/ and .claude/skills/',
      path: '/skills'
    },
    {
      icon: <ViewQuilt fontSize="large" />,
      title: 'Split Screen View',
      description: 'View Backstage and Temporal side-by-side for seamless workflow management',
      path: '/split-screen'
    },
    {
      icon: <Autorenew fontSize="large" />,
      title: 'Temporal Workflows',
      description: 'Manage and monitor your Temporal workflows with advanced AI agent orchestration',
      path: '/temporal'
    },
    {
      icon: <LibraryBooks fontSize="large" />,
      title: 'Backstage Catalog',
      description: 'Explore your software catalog and manage components, APIs, and infrastructure',
      path: '/catalog'
    }
  ];

  return (
    <Box sx={{ flexGrow: 1, p: 3 }}>
      <Typography variant="h3" gutterBottom align="center">
        ai agents sandbox
      </Typography>

      <Grid container spacing={4} sx={{ mt: 2 }}>
        {features.map((feature, index) => (
          <Grid item xs={12} sm={6} md={3} key={index}>
            <Paper
              sx={{
                p: 3,
                height: '100%',
                display: 'flex',
                flexDirection: 'column',
                alignItems: 'center',
                textAlign: 'center',
                cursor: 'pointer',
                transition: 'transform 0.2s, box-shadow 0.2s',
                '&:hover': {
                  transform: 'translateY(-4px)',
                  boxShadow: 4,
                },
              }}
              onClick={() => window.location.href = feature.path}
            >
              <Box sx={{ color: 'primary.main', mb: 2 }}>
                {feature.icon}
              </Box>
              
              <Typography variant="h6" gutterBottom>
                {feature.title}
              </Typography>
              
              <Typography variant="body2" color="textSecondary" paragraph>
                {feature.description}
              </Typography>
              
              <Button
                variant="outlined"
                size="small"
                sx={{ mt: 'auto' }}
              >
                Launch
              </Button>
            </Paper>
          </Grid>
        ))}
      </Grid>

    </Box>
  );
};
