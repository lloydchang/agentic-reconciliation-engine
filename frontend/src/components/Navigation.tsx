import React from 'react';
import { 
  Box, 
  List, 
  ListItem, 
  Tooltip, 
  IconButton,
  useTheme
} from '@mui/material';
import { 
  Extension, 
  Autorenew, 
  LibraryBooks, 
  Chat, 
  ViewQuilt,
  Home
} from '@mui/icons-material';
import { useNavigate, useLocation } from 'react-router-dom';

const navItems = [
  { path: '/', icon: <Home />, label: 'Home' },
  { path: '/skills', icon: <Extension />, label: 'AI Agent Skills' },
  { path: '/split-screen', icon: <ViewQuilt />, label: 'Split View' },
  { path: '/temporal', icon: <Autorenew />, label: 'Temporal Workflows' },
  { path: '/catalog', icon: <LibraryBooks />, label: 'Backstage Catalog' },
  { path: '/rag-ai', icon: <Chat />, label: 'RAG AI Assistant' },
];

export const Navigation: React.FC = () => {
  const navigate = useNavigate();
  const location = useLocation();
  const theme = useTheme();

  return (
    <Box
      sx={{
        position: 'fixed',
        top: 16,
        right: 16,
        zIndex: 1300,
        borderRadius: 4,
        display: 'flex',
        flexDirection: 'row',
        gap: 2,
        transition: 'all 0.3s cubic-bezier(0.4, 0, 0.2, 1)',
        '&:hover': {
          transform: 'scale(1.02)',
        }
      }}
    >
      <List sx={{ display: 'flex', flexDirection: 'row', gap: 1 }}>
        {navItems.map((item) => {
          const isActive = location.pathname === item.path;
          return (
            <ListItem key={item.path} disablePadding sx={{ display: 'block' }}>
              <Tooltip title={item.label} placement="bottom" arrow>
                <IconButton
                  onClick={() => navigate(item.path)}
                  sx={{
                    color: isActive ? theme.palette.primary.main : theme.palette.text.secondary,
                    backgroundColor: isActive ? 'rgba(25, 118, 210, 0.08)' : 'transparent',
                    transition: 'all 0.2s ease-in-out',
                    width: 48,
                    height: 48,
                    '&:hover': {
                      backgroundColor: 'rgba(25, 118, 210, 0.12)',
                      transform: 'scale(1.1) translateZ(20px)',
                      color: theme.palette.primary.main,
                      zIndex: 10,
                    },
                  }}
                >
                  {React.cloneElement(item.icon as React.ReactElement, {
                    fontSize: 'medium'
                  })}
                </IconButton>
              </Tooltip>
            </ListItem>
          );
        })}
      </List>
    </Box>
  );
};
