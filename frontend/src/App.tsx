import React, { useState } from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate, useNavigate } from 'react-router-dom';
import { ThemeProvider, createTheme } from '@mui/material/styles';
import CssBaseline from '@mui/material/CssBaseline';
import { Box, Container, Paper, Typography, TextField, Button, Alert, Link } from '@mui/material';

import Navbar from './components/Navbar';
import HomePage from './pages/HomePage';
import ProjectPage from './pages/ProjectPage';
import NotebooksPage from './pages/NotebooksPage';
import NotebookPage from './pages/NotebookPage';
import api, { authApi } from './services/api';

const theme = createTheme({
  palette: {
    mode: 'light',
    primary: {
      main: '#1976d2',
    },
    secondary: {
      main: '#dc004e',
    },
    background: {
      default: '#f5f5f5',
    },
  },
  typography: {
    fontFamily: 'Roboto, Arial, sans-serif',
  },
});

const isAuthed = () => Boolean(localStorage.getItem('auth_token'));

const ProtectedRoute: React.FC<{ children: React.ReactElement }> = ({ children }) => {
  if (!isAuthed()) {
    return <Navigate to="/login" replace />;
  }
  return children;
};

const LoginInline: React.FC = () => {
  const navigate = useNavigate();
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setLoading(true);
    try {
      const res = await authApi.login(email, password);
      localStorage.setItem('auth_token', res.access_token);
      try {
        const dh: any = (api.defaults.headers as any);
        if (dh && typeof dh.set === 'function') {
          dh.set('Authorization', `Bearer ${res.access_token}`);
        } else if (dh && dh.common) {
          dh.common['Authorization'] = `Bearer ${res.access_token}`;
        } else {
          (api.defaults.headers as any)['Authorization'] = `Bearer ${res.access_token}`;
        }
      } catch {}
      navigate('/');
    } catch (err) {
      setError('Invalid credentials');
    } finally {
      setLoading(false);
    }
  };

  return (
    <Container maxWidth="sm" sx={{ mt: 8 }}>
      <Paper sx={{ p: 3 }}>
        <Typography variant="h5" gutterBottom>Sign in</Typography>
        {error && <Alert severity="error" sx={{ mb: 2 }}>{error}</Alert>}
        <Box component="form" onSubmit={handleSubmit}>
          <TextField label="Email" type="email" fullWidth sx={{ mb: 2 }} value={email} onChange={(e) => setEmail(e.target.value)} required />
          <TextField label="Password" type="password" fullWidth sx={{ mb: 2 }} value={password} onChange={(e) => setPassword(e.target.value)} required />
          <Button type="submit" variant="contained" fullWidth disabled={loading}>Sign in</Button>
        </Box>
        <Box sx={{ mt: 2 }}>
          <Typography variant="body2">Don’t have an account? <Link href="/signup">Sign up</Link></Typography>
        </Box>
      </Paper>
    </Container>
  );
};

const SignupInline: React.FC = () => {
  const navigate = useNavigate();
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setLoading(true);
    try {
      const res = await authApi.signup(email, password);
      localStorage.setItem('auth_token', res.access_token);
      try {
        const dh: any = (api.defaults.headers as any);
        if (dh && typeof dh.set === 'function') {
          dh.set('Authorization', `Bearer ${res.access_token}`);
        } else if (dh && dh.common) {
          dh.common['Authorization'] = `Bearer ${res.access_token}`;
        } else {
          (api.defaults.headers as any)['Authorization'] = `Bearer ${res.access_token}`;
        }
      } catch {}
      navigate('/');
    } catch (err: any) {
      setError(err?.response?.data?.detail || 'Failed to sign up');
    } finally {
      setLoading(false);
    }
  };

  return (
    <Container maxWidth="sm" sx={{ mt: 8 }}>
      <Paper sx={{ p: 3 }}>
        <Typography variant="h5" gutterBottom>Create account</Typography>
        {error && <Alert severity="error" sx={{ mb: 2 }}>{error}</Alert>}
        <Box component="form" onSubmit={handleSubmit}>
          <TextField label="Email" type="email" fullWidth sx={{ mb: 2 }} value={email} onChange={(e) => setEmail(e.target.value)} required />
          <TextField label="Password" type="password" fullWidth sx={{ mb: 2 }} value={password} onChange={(e) => setPassword(e.target.value)} required />
          <Button type="submit" variant="contained" fullWidth disabled={loading}>Sign up</Button>
        </Box>
        <Box sx={{ mt: 2 }}>
          <Typography variant="body2">Already have an account? <Link href="/login">Sign in</Link></Typography>
        </Box>
      </Paper>
    </Container>
  );
};

function App() {
  return (
    <ThemeProvider theme={theme}>
      <CssBaseline />
      <Router>
        <Box sx={{ display: 'flex', flexDirection: 'column', minHeight: '100vh' }}>
          <Navbar />
          <Box component="main" sx={{ flexGrow: 1, p: 3 }}>
            <Routes>
              <Route path="/login" element={<LoginInline />} />
              <Route path="/signup" element={<SignupInline />} />

              <Route path="/" element={<ProtectedRoute><HomePage /></ProtectedRoute>} />
              <Route path="/project/:id" element={<ProtectedRoute><ProjectPage /></ProtectedRoute>} />
              <Route path="/notebooks" element={<ProtectedRoute><NotebooksPage /></ProtectedRoute>} />
              <Route path="/notebook/:id" element={<ProtectedRoute><NotebookPage /></ProtectedRoute>} />

              <Route path="*" element={<Navigate to={isAuthed() ? '/' : '/login'} replace />} />
            </Routes>
          </Box>
        </Box>
      </Router>
    </ThemeProvider>
  );
}

export default App;

