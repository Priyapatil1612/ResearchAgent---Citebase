import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Container,
  Typography,
  Box,
  Button,
  Grid,
  Card,
  CardContent,
  CardActions,
  Alert,
  CircularProgress,
  Fab,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  TextField,
  Chip,
} from '@mui/material';
import {
  Add as AddIcon,
  Book as BookIcon,
  Delete as DeleteIcon,
  Refresh as RefreshIcon,
} from '@mui/icons-material';

import { Notebook, NotebookCreate } from '../types';
import { notebookApi } from '../services/api';

const NotebooksPage: React.FC = () => {
  const navigate = useNavigate();
  const [notebooks, setNotebooks] = useState<Notebook[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [createDialogOpen, setCreateDialogOpen] = useState(false);
  const [newNotebook, setNewNotebook] = useState<NotebookCreate>({
    name: '',
    description: '',
  });

  const loadNotebooks = async () => {
    try {
      setLoading(true);
      setError(null);
      const data = await notebookApi.getAll();
      setNotebooks(data);
    } catch (err) {
      setError('Failed to load notebooks. Please try again.');
      console.error('Error loading notebooks:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadNotebooks();
  }, []);

  const handleCreateNotebook = async () => {
    try {
      const notebook = await notebookApi.create(newNotebook);
      setNotebooks(prev => [notebook, ...prev]);
      setCreateDialogOpen(false);
      setNewNotebook({ name: '', description: '' });
    } catch (err) {
      setError('Failed to create notebook. Please try again.');
      console.error('Error creating notebook:', err);
    }
  };

  const handleDeleteNotebook = async (notebookId: string) => {
    if (window.confirm('Delete this notebook and all its entries?')) {
      try {
        await notebookApi.delete(notebookId);
        setNotebooks(prev => prev.filter(n => n.id !== notebookId));
      } catch (err) {
        setError('Failed to delete notebook. Please try again.');
        console.error('Error deleting notebook:', err);
      }
    }
  };

  const handleRefresh = () => {
    loadNotebooks();
  };

  if (loading) {
    return (
      <Container maxWidth="lg" sx={{ mt: 4, textAlign: 'center' }}>
        <CircularProgress size={60} />
        <Typography variant="h6" sx={{ mt: 2 }}>
          Loading notebooks...
        </Typography>
      </Container>
    );
  }

  return (
    <Container maxWidth="lg" sx={{ mt: 4 }}>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 4 }}>
        <Box>
          <Typography variant="h4" component="h1" gutterBottom>
            My Notebooks
          </Typography>
          <Typography variant="body1" color="text.secondary">
            Organize and manage your research notes and Q&A pairs
          </Typography>
        </Box>
        
        <Box sx={{ display: 'flex', gap: 2 }}>
          <Button
            variant="outlined"
            startIcon={<RefreshIcon />}
            onClick={handleRefresh}
            disabled={loading}
          >
            Refresh
          </Button>
          <Button
            variant="contained"
            startIcon={<AddIcon />}
            onClick={() => setCreateDialogOpen(true)}
          >
            New Notebook
          </Button>
        </Box>
      </Box>

      {error && (
        <Alert severity="error" sx={{ mb: 3 }} onClose={() => setError(null)}>
          {error}
        </Alert>
      )}

      {notebooks.length === 0 ? (
        <Box
          sx={{
            textAlign: 'center',
            py: 8,
            px: 4,
            backgroundColor: 'grey.50',
            borderRadius: 2,
            border: '2px dashed',
            borderColor: 'grey.300',
          }}
        >
          <BookIcon sx={{ fontSize: 64, color: 'grey.400', mb: 2 }} />
          <Typography variant="h6" color="text.secondary" gutterBottom>
            No notebooks yet
          </Typography>
          <Typography variant="body2" color="text.secondary" sx={{ mb: 3 }}>
            Create your first notebook to start organizing your research notes
          </Typography>
          <Button
            variant="contained"
            startIcon={<AddIcon />}
            onClick={() => setCreateDialogOpen(true)}
            size="large"
          >
            Create Notebook
          </Button>
        </Box>
      ) : (
        <Grid container spacing={3}>
          {notebooks.map((notebook) => (
            <Grid item xs={12} sm={6} md={4} key={notebook.id}>
              <Card
                sx={{
                  height: '100%',
                  display: 'flex',
                  flexDirection: 'column',
                  transition: 'transform 0.2s ease-in-out, box-shadow 0.2s ease-in-out',
                  '&:hover': {
                    transform: 'translateY(-2px)',
                    boxShadow: 4,
                  },
                }}
              >
                <CardContent sx={{ flexGrow: 1 }}>
                  <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', mb: 2 }}>
                    <Typography variant="h6" component="h2" sx={{ fontWeight: 'bold' }}>
                      {notebook.name}
                    </Typography>
                    <Chip
                      label={`${notebook.entries.length} entries`}
                      size="small"
                      color="primary"
                    />
                  </Box>

                  {notebook.description && (
                    <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
                      {notebook.description}
                    </Typography>
                  )}

                  <Typography variant="caption" color="text.secondary">
                    Created: {new Date(notebook.created_at).toLocaleDateString()}
                  </Typography>
                  
                  {notebook.updated_at !== notebook.created_at && (
                    <Typography variant="caption" color="text.secondary" display="block">
                      Updated: {new Date(notebook.updated_at).toLocaleDateString()}
                    </Typography>
                  )}
                </CardContent>

                <CardActions sx={{ p: 2, pt: 0 }}>
                  <Button
                    variant="contained"
                    onClick={() => navigate(`/notebook/${notebook.id}`)}
                    fullWidth
                    startIcon={<BookIcon />}
                  >
                    Open Notebook
                  </Button>
                  <Button
                    variant="outlined"
                    color="error"
                    startIcon={<DeleteIcon />}
                    onClick={() => handleDeleteNotebook(notebook.id)}
                    fullWidth
                  >
                    Delete
                  </Button>
                </CardActions>
              </Card>
            </Grid>
          ))}
        </Grid>
      )}

      {/* Create Notebook Dialog */}
      <Dialog open={createDialogOpen} onClose={() => setCreateDialogOpen(false)} maxWidth="sm" fullWidth>
        <DialogTitle>
          <Typography variant="h6" component="div">
            Create New Notebook
          </Typography>
        </DialogTitle>
        
        <DialogContent>
          <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2, pt: 1 }}>
            <TextField
              label="Notebook Name"
              value={newNotebook.name}
              onChange={(e) => setNewNotebook(prev => ({ ...prev, name: e.target.value }))}
              fullWidth
              required
              placeholder="e.g., AI Research Notes"
            />

            <TextField
              label="Description (Optional)"
              value={newNotebook.description}
              onChange={(e) => setNewNotebook(prev => ({ ...prev, description: e.target.value }))}
              multiline
              rows={3}
              fullWidth
              placeholder="Brief description of this notebook..."
            />
          </Box>
        </DialogContent>

        <DialogActions sx={{ p: 3 }}>
          <Button onClick={() => setCreateDialogOpen(false)} color="inherit">
            Cancel
          </Button>
          <Button
            onClick={handleCreateNotebook}
            variant="contained"
            disabled={!newNotebook.name.trim()}
          >
            Create Notebook
          </Button>
        </DialogActions>
      </Dialog>

      {/* Floating Action Button for mobile */}
      <Fab
        color="primary"
        aria-label="add notebook"
        sx={{
          position: 'fixed',
          bottom: 16,
          right: 16,
          display: { xs: 'flex', sm: 'none' },
        }}
        onClick={() => setCreateDialogOpen(true)}
      >
        <AddIcon />
      </Fab>
    </Container>
  );
};

export default NotebooksPage;

