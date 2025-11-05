import React, { useState } from 'react';
import {
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  TextField,
  Button,
  Box,
  Typography,
} from '@mui/material';
import { ProjectCreate } from '../types';

interface CreateProjectDialogProps {
  open: boolean;
  onClose: () => void;
  onCreate: (projectData: ProjectCreate) => void;
}

const CreateProjectDialog: React.FC<CreateProjectDialogProps> = ({
  open,
  onClose,
  onCreate,
}) => {
  const [formData, setFormData] = useState<ProjectCreate>({
    name: '',
    description: '',
    topic: '',
    namespace: '',
  });

  const [errors, setErrors] = useState<Partial<ProjectCreate>>({});

  const handleChange = (field: keyof ProjectCreate) => (
    event: React.ChangeEvent<HTMLInputElement>
  ) => {
    setFormData(prev => ({
      ...prev,
      [field]: event.target.value,
    }));
    
    // Clear error when user starts typing
    if (errors[field]) {
      setErrors(prev => ({
        ...prev,
        [field]: undefined,
      }));
    }
  };

  const validateForm = (): boolean => {
    const newErrors: Partial<ProjectCreate> = {};

    if (!formData.name.trim()) {
      newErrors.name = 'Project name is required';
    }

    if (!formData.topic.trim()) {
      newErrors.topic = 'Research topic is required';
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleSubmit = () => {
    if (validateForm()) {
      onCreate(formData);
      setFormData({
        name: '',
        description: '',
        topic: '',
        namespace: '',
      });
      setErrors({});
    }
  };

  const handleClose = () => {
    setFormData({
      name: '',
      description: '',
      topic: '',
      namespace: '',
    });
    setErrors({});
    onClose();
  };

  return (
    <Dialog open={open} onClose={handleClose} maxWidth="sm" fullWidth>
      <DialogTitle>
        <Typography variant="h6" component="div">
          Create New Research Project
        </Typography>
      </DialogTitle>
      
      <DialogContent>
        <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2, pt: 1 }}>
          <TextField
            label="Project Name"
            value={formData.name}
            onChange={handleChange('name')}
            error={!!errors.name}
            helperText={errors.name}
            fullWidth
            required
            placeholder="e.g., AI Research 2024"
          />

          <TextField
            label="Research Topic"
            value={formData.topic}
            onChange={handleChange('topic')}
            error={!!errors.topic}
            helperText={errors.topic || 'What do you want to research?'}
            fullWidth
            required
            placeholder="e.g., artificial intelligence trends 2024"
          />

          <TextField
            label="Description (Optional)"
            value={formData.description}
            onChange={handleChange('description')}
            multiline
            rows={3}
            fullWidth
            placeholder="Brief description of your research project..."
          />

          <TextField
            label="Namespace (Optional)"
            value={formData.namespace}
            onChange={handleChange('namespace')}
            fullWidth
            placeholder="Leave empty for auto-generated"
            helperText="Unique identifier for this project. If empty, it will be auto-generated."
          />
        </Box>
      </DialogContent>

      <DialogActions sx={{ p: 3 }}>
        <Button onClick={handleClose} color="inherit">
          Cancel
        </Button>
        <Button
          onClick={handleSubmit}
          variant="contained"
          disabled={!formData.name.trim() || !formData.topic.trim()}
        >
          Create Project
        </Button>
      </DialogActions>
    </Dialog>
  );
};

export default CreateProjectDialog;

