import React from 'react';
import {
  AppBar,
  Toolbar,
  Typography,
  Button,
  Box,
  IconButton,
} from '@mui/material';
import {
  Home as HomeIcon,
  Book as BookIcon,
  Science as ScienceIcon,
} from '@mui/icons-material';
import { useNavigate, useLocation } from 'react-router-dom';

const Navbar: React.FC = () => {
  const navigate = useNavigate();
  const location = useLocation();

  const isActive = (path: string) => location.pathname === path;
  const isAuthed = Boolean(localStorage.getItem('auth_token'));

  const handleSignOut = () => {
    localStorage.removeItem('auth_token');
    navigate('/login');
  };

  return (
    <AppBar position="static" elevation={1}>
      <Toolbar>
        <IconButton
          edge="start"
          color="inherit"
          aria-label="home"
          onClick={() => navigate('/')}
          sx={{ mr: 2 }}
        >
          <ScienceIcon />
        </IconButton>
        
        <Typography variant="h6" component="div" sx={{ flexGrow: 1 }}>
          Research Agent
        </Typography>

        <Box sx={{ display: 'flex', gap: 1, alignItems: 'center' }}>
          {isAuthed && (
            <>
              <Button
                color="inherit"
                startIcon={<HomeIcon />}
                onClick={() => navigate('/')}
                sx={{ backgroundColor: isActive('/') ? 'rgba(255,255,255,0.1)' : 'transparent' }}
              >
                Projects
              </Button>
              <Button
                color="inherit"
                startIcon={<BookIcon />}
                onClick={() => navigate('/notebooks')}
                sx={{ backgroundColor: isActive('/notebooks') ? 'rgba(255,255,255,0.1)' : 'transparent' }}
              >
                Notebooks
              </Button>
              <Button color="inherit" onClick={handleSignOut}>Sign out</Button>
            </>
          )}
          {!isAuthed && (
            <>
              <Button color="inherit" onClick={() => navigate('/login')}>Sign in</Button>
              <Button color="inherit" onClick={() => navigate('/signup')}>Sign up</Button>
            </>
          )}
        </Box>
      </Toolbar>
    </AppBar>
  );
};

export default Navbar;

