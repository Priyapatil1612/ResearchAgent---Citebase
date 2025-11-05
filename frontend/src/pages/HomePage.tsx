import React, { useState, useEffect } from 'react';
import {
  Container,
  Typography,
  Button,
  Grid,
  Box,
  Alert,
  CircularProgress,
  Fab,
} from '@mui/material';
import {
  Add as AddIcon,
  Refresh as RefreshIcon,
} from '@mui/icons-material';

import { Project } from '../types';
import { projectApi } from '../services/api';
import ProjectCard from '../components/ProjectCard';
import CreateProjectDialog from '../components/CreateProjectDialog';

const HomePage: React.FC = () => {
  const [projects, setProjects] = useState<Project[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [createDialogOpen, setCreateDialogOpen] = useState(false);
  const [researchingProjects, setResearchingProjects] = useState<Set<string>>(new Set());

  const loadProjects = async () => {
    try {
      setLoading(true);
      setError(null);
      const data = await projectApi.getAll();
      setProjects(data);
    } catch (err) {
      setError('Failed to load projects. Please try again.');
      console.error('Error loading projects:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadProjects();
  }, []);

  const handleCreateProject = async (projectData: any) => {
    try {
      const newProject = await projectApi.create(projectData);
      setProjects(prev => [newProject, ...prev]);
      setCreateDialogOpen(false);
    } catch (err) {
      setError('Failed to create project. Please try again.');
      console.error('Error creating project:', err);
    }
  };

  const handleStartResearch = async (projectId: string) => {
    try {
      setResearchingProjects(prev => new Set(prev).add(projectId));
      
      // Update project status to researching
      setProjects(prev => prev.map(p => 
        p.id === projectId ? { ...p, status: 'researching' as const } : p
      ));

      await projectApi.startResearch(projectId);
      
      // Reload projects to get updated data
      await loadProjects();
    } catch (err) {
      setError('Failed to start research. Please try again.');
      console.error('Error starting research:', err);
      
      // Update project status to error
      setProjects(prev => prev.map(p => 
        p.id === projectId ? { ...p, status: 'error' as const } : p
      ));
    } finally {
      setResearchingProjects(prev => {
        const newSet = new Set(prev);
        newSet.delete(projectId);
        return newSet;
      });
    }
  };

  const handleRefresh = () => {
    loadProjects();
  };

  const handleDeleteProject = async (projectId: string) => {
    if (!window.confirm('Delete this project? This will remove its chat and related notebook entries.')) return;
    try {
      await projectApi.delete(projectId);
      setProjects(prev => prev.filter(p => p.id !== projectId));
    } catch (err) {
      setError('Failed to delete project. Please try again.');
      console.error('Error deleting project:', err);
    }
  };

  if (loading) {
    return (
      <Container maxWidth="lg" sx={{ mt: 4, textAlign: 'center' }}>
        <CircularProgress size={60} />
        <Typography variant="h6" sx={{ mt: 2 }}>
          Loading projects...
        </Typography>
      </Container>
    );
  }

  return (
    <Container maxWidth="lg" sx={{ mt: 4 }}>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 4 }}>
        <Box>
          <Typography variant="h4" component="h1" gutterBottom>
            Research Projects
          </Typography>
          <Typography variant="body1" color="text.secondary">
            Manage your research projects and start new investigations
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
            New Project
          </Button>
        </Box>
      </Box>

      {error && (
        <Alert severity="error" sx={{ mb: 3 }} onClose={() => setError(null)}>
          {error}
        </Alert>
      )}

      {projects.length === 0 ? (
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
          <Typography variant="h6" color="text.secondary" gutterBottom>
            No projects yet
          </Typography>
          <Typography variant="body2" color="text.secondary" sx={{ mb: 3 }}>
            Create your first research project to get started
          </Typography>
          <Button
            variant="contained"
            startIcon={<AddIcon />}
            onClick={() => setCreateDialogOpen(true)}
            size="large"
          >
            Create Project
          </Button>
        </Box>
      ) : (
        <Grid container spacing={3}>
          {projects.map((project) => (
            <Grid item xs={12} sm={6} md={4} key={project.id}>
              <ProjectCard
                project={project}
                onStartResearch={handleStartResearch}
                onDeleteProject={handleDeleteProject}
                isResearching={researchingProjects.has(project.id)}
              />
            </Grid>
          ))}
        </Grid>
      )}

      <CreateProjectDialog
        open={createDialogOpen}
        onClose={() => setCreateDialogOpen(false)}
        onCreate={handleCreateProject}
      />

      {/* Floating Action Button for mobile */}
      <Fab
        color="primary"
        aria-label="add project"
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

export default HomePage;

