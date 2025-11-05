import React from 'react';
import {
  Card,
  CardContent,
  CardActions,
  Typography,
  Button,
  Chip,
  Box,
  LinearProgress,
} from '@mui/material';
import {
  PlayArrow as PlayIcon,
  QuestionAnswer as QAIcon,
  Description as DescriptionIcon,
} from '@mui/icons-material';
import { Project } from '../types';
import DeleteIcon from '@mui/icons-material/Delete';
import { useNavigate } from 'react-router-dom';

interface ProjectCardProps {
  project: Project;
  onStartResearch: (projectId: string) => void;
  onDeleteProject: (projectId: string) => void;
  isResearching: boolean;
}

const ProjectCard: React.FC<ProjectCardProps> = ({
  project,
  onStartResearch,
  onDeleteProject,
  isResearching,
}) => {
  const navigate = useNavigate();

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'completed':
        return 'success';
      case 'researching':
        return 'warning';
      case 'error':
        return 'error';
      default:
        return 'default';
    }
  };

  const getStatusText = (status: string) => {
    switch (status) {
      case 'completed':
        return 'Ready';
      case 'researching':
        return 'Researching...';
      case 'error':
        return 'Error';
      default:
        return 'Created';
    }
  };

  return (
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
            {project.name}
          </Typography>
          <Chip
            label={getStatusText(project.status)}
            color={getStatusColor(project.status) as any}
            size="small"
          />
        </Box>

        {project.description && (
          <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
            {project.description}
          </Typography>
        )}

        <Typography variant="body2" sx={{ mb: 2 }}>
          <strong>Topic:</strong> {project.topic}
        </Typography>

        {/* Research summary hidden per requirements */}

        {isResearching && (
          <Box sx={{ mb: 2 }}>
            <Typography variant="body2" color="text.secondary" sx={{ mb: 1 }}>
              Research in progress...
            </Typography>
            <LinearProgress />
          </Box>
        )}

        <Typography variant="caption" color="text.secondary">
          Created: {new Date(project.created_at).toLocaleDateString()}
        </Typography>
      </CardContent>

      <CardActions sx={{ p: 2, pt: 0 }}>
        <Button
          variant="outlined"
          color="error"
          startIcon={<DeleteIcon />}
          onClick={() => onDeleteProject(project.id)}
        >
          Delete
        </Button>
        {project.status === 'created' && (
          <Button
            variant="contained"
            startIcon={<PlayIcon />}
            onClick={() => onStartResearch(project.id)}
            disabled={isResearching}
            fullWidth
          >
            Start Research
          </Button>
        )}

        {project.status === 'completed' && (
          <Button
            variant="contained"
            startIcon={<QAIcon />}
            onClick={() => navigate(`/project/${project.id}`)}
            fullWidth
          >
            Ask Questions
          </Button>
        )}

        {project.status === 'error' && (
          <Button
            variant="outlined"
            startIcon={<PlayIcon />}
            onClick={() => onStartResearch(project.id)}
            disabled={isResearching}
            fullWidth
          >
            Retry Research
          </Button>
        )}
      </CardActions>
    </Card>
  );
};

export default ProjectCard;

