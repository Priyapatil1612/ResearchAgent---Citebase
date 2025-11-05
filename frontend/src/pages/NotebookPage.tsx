import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import {
  Container,
  Typography,
  Box,
  Paper,
  Button,
  Alert,
  CircularProgress,
  IconButton,
  Card,
  CardContent,
  CardActions,
  Chip,
  Divider,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  TextField,
  List,
  ListItem,
  ListItemText,
  ListItemSecondaryAction,
  Collapse,
} from '@mui/material';
import {
  ArrowBack as ArrowBackIcon,
  Delete as DeleteIcon,
  Edit as EditIcon,
  OpenInNew as OpenInNewIcon,
  ContentCopy as CopyIcon,
  BookmarkAdd as BookmarkAddIcon,
  ExpandMore as ExpandMoreIcon,
  ExpandLess as ExpandLessIcon,
} from '@mui/icons-material';
import ReactMarkdown from 'react-markdown';
import { Notebook, NotebookEntry } from '../types';
import { notebookApi, projectApi } from '../services/api';

const stripSources = (text: string): string => {
  const pattern = /(\n|^)\s*(#+\s*)?(sources|citations|references)\s*:?\s*[\s\S]*$/i;
  return text.replace(pattern, '').trim();
};

const NotebookPage: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const [notebook, setNotebook] = useState<Notebook | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [deleteDialogOpen, setDeleteDialogOpen] = useState(false);
  const [entryToDelete, setEntryToDelete] = useState<NotebookEntry | null>(null);
  const [openCitations, setOpenCitations] = useState<Record<string, boolean>>({});
  const toggleCitations = (entryId: string) =>
    setOpenCitations(prev => ({ ...prev, [entryId]: !prev[entryId] }));

  // Notebook-level notes state
  const [notebookNotesEditing, setNotebookNotesEditing] = useState(false);
  const [notebookNotesDraft, setNotebookNotesDraft] = useState('');

  // Per-entry notes editing state
  const [editingEntryNotes, setEditingEntryNotes] = useState<Record<string, boolean>>({});
  const [entryNotesDraft, setEntryNotesDraft] = useState<Record<string, string>>({});

  useEffect(() => {
    if (id) {
      loadNotebook();
    }
  }, [id]);

  const loadNotebook = async () => {
    try {
      setLoading(true);
      setError(null);
      const data = await notebookApi.getById(id!);
      setNotebook(data);
      setNotebookNotesDraft(data.notes || '');
    } catch (err) {
      setError('Failed to load notebook. Please try again.');
      console.error('Error loading notebook:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleDeleteEntry = async (entry: NotebookEntry) => {
    if (!notebook) return;
    
    try {
      await notebookApi.deleteEntry(notebook.id, entry.id);
      setNotebook(prev => prev ? {
        ...prev,
        entries: prev.entries.filter(e => e.id !== entry.id)
      } : null);
      setDeleteDialogOpen(false);
      setEntryToDelete(null);
    } catch (err) {
      setError('Failed to delete entry. Please try again.');
      console.error('Error deleting entry:', err);
    }
  };

  const copyToClipboard = (text: string) => {
    navigator.clipboard.writeText(text);
  };

  const openProject = (projectId: string) => {
    navigate(`/project/${projectId}`);
  };

  const handleSaveNotebookNotes = async () => {
    if (!notebook) return;
    try {
      const updated = await notebookApi.update(notebook.id, { notes: notebookNotesDraft });
      setNotebook(updated);
      setNotebookNotesEditing(false);
    } catch (err) {
      console.error('Error updating notebook notes:', err);
    }
  };

  const startEditEntryNotes = (entryId: string, current: string | undefined) => {
    setEditingEntryNotes(prev => ({ ...prev, [entryId]: true }));
    setEntryNotesDraft(prev => ({ ...prev, [entryId]: current || '' }));
  };

  const cancelEditEntryNotes = (entryId: string) => {
    setEditingEntryNotes(prev => ({ ...prev, [entryId]: false }));
  };

  const handleSaveEntryNotes = async (entryId: string) => {
    if (!notebook) return;
    try {
      const notes = entryNotesDraft[entryId] || '';
      await notebookApi.updateEntry(notebook.id, entryId, { notes });
      setNotebook(prev => prev ? {
        ...prev,
        entries: prev.entries.map(e => e.id === entryId ? { ...e, notes } : e)
      } : prev);
      setEditingEntryNotes(prev => ({ ...prev, [entryId]: false }));
    } catch (err) {
      console.error('Error updating entry notes:', err);
    }
  };

  if (loading) {
    return (
      <Container maxWidth="lg" sx={{ mt: 4, textAlign: 'center' }}>
        <CircularProgress size={60} />
        <Typography variant="h6" sx={{ mt: 2 }}>
          Loading notebook...
        </Typography>
      </Container>
    );
  }

  if (error || !notebook) {
    return (
      <Container maxWidth="lg" sx={{ mt: 4 }}>
        <Alert severity="error" sx={{ mb: 3 }}>
          {error || 'Notebook not found'}
        </Alert>
        <Button
          variant="contained"
          startIcon={<ArrowBackIcon />}
          onClick={() => navigate('/notebooks')}
        >
          Back to Notebooks
        </Button>
      </Container>
    );
  }

  return (
    <Container maxWidth="lg" sx={{ mt: 4 }}>
      <Box sx={{ display: 'flex', alignItems: 'center', mb: 3 }}>
        <IconButton onClick={() => navigate('/notebooks')} sx={{ mr: 2 }}>
          <ArrowBackIcon />
        </IconButton>
        <Box sx={{ flexGrow: 1 }}>
          <Typography variant="h4" component="h1">
            {notebook.name}
          </Typography>
          {notebook.description && (
            <Typography variant="body1" color="text.secondary">
              {notebook.description}
            </Typography>
          )}
        </Box>
        <Chip
          label={`${notebook.entries.length} entries`}
          color="primary"
        />
      </Box>

      {/* Notebook-level Notes */}
      <Box sx={{ mb: 3 }}>
        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 1 }}>
          <Typography variant="h6">Notes</Typography>
          {!notebookNotesEditing && (
            <Button size="small" variant="outlined" onClick={() => setNotebookNotesEditing(true)}>
              {notebook?.notes ? 'Edit Notes' : 'Add Notes'}
            </Button>
          )}
        </Box>
        {notebookNotesEditing ? (
          <Box>
            <TextField
              fullWidth
              multiline
              minRows={5}
              value={notebookNotesDraft}
              onChange={(e) => setNotebookNotesDraft(e.target.value)}
              placeholder="Write notebook-level notes in Markdown..."
              sx={{ mb: 1 }}
            />
            <Box sx={{ display: 'flex', gap: 1 }}>
              <Button variant="contained" size="small" onClick={handleSaveNotebookNotes}>Save</Button>
              <Button size="small" onClick={() => { setNotebookNotesEditing(false); setNotebookNotesDraft(notebook?.notes || ''); }}>Cancel</Button>
            </Box>
          </Box>
        ) : (
          <Paper sx={{ p: 2, backgroundColor: 'grey.50' }}>
            {notebook?.notes ? (
              <ReactMarkdown>{notebook.notes}</ReactMarkdown>
            ) : (
              <Typography variant="body2" color="text.secondary">No notes yet.</Typography>
            )}
          </Paper>
        )}
      </Box>

      {notebook.entries.length === 0 ? (
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
            No entries yet
          </Typography>
          <Typography variant="body2" color="text.secondary" sx={{ mb: 3 }}>
            This notebook is empty. Start a research project and save Q&A pairs to populate it.
          </Typography>
          <Button
            variant="contained"
            onClick={() => navigate('/')}
          >
            Go to Projects
          </Button>
        </Box>
      ) : (
        <Box sx={{ display: 'flex', flexDirection: 'column', gap: 3 }}>
          {notebook.entries.map((entry, index) => (
            <Card key={entry.id} elevation={2}>
              <CardContent>
                <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', mb: 2 }}>
                  <Typography variant="h6" color="primary" gutterBottom>
                    Entry #{index + 1}
                  </Typography>
                  <Box>
                    <IconButton
                      size="small"
                      onClick={() => copyToClipboard(`${entry.question}\n\n${entry.answer}`)}
                    >
                      <CopyIcon fontSize="small" />
                    </IconButton>
                    <IconButton
                      size="small"
                      onClick={() => {
                        setEntryToDelete(entry);
                        setDeleteDialogOpen(true);
                      }}
                    >
                      <DeleteIcon fontSize="small" />
                    </IconButton>
                  </Box>
                </Box>

                <Box sx={{ mb: 2 }}>
                  <Typography variant="subtitle2" color="text.secondary" gutterBottom>
                    Question:
                  </Typography>
                  <Paper sx={{ p: 2, backgroundColor: 'primary.50', mb: 2 }}>
                    <Typography variant="body1">
                      {entry.question}
                    </Typography>
                  </Paper>
                </Box>

                <Box sx={{ mb: 2 }}>
                  <Typography variant="subtitle2" color="text.secondary" gutterBottom>
                    Answer:
                  </Typography>
                  <Paper sx={{ p: 2, backgroundColor: 'grey.50' }}>
                    <ReactMarkdown>{stripSources(entry.answer)}</ReactMarkdown>
                  </Paper>
                </Box>

                {entry.citations && entry.citations.length > 0 && (
                  <Box sx={{ mb: 2 }}>
                    <Button
                      size="small"
                      onClick={() => toggleCitations(entry.id)}
                      endIcon={openCitations[entry.id] ? <ExpandLessIcon /> : <ExpandMoreIcon />}
                      aria-expanded={Boolean(openCitations[entry.id])}
                      aria-controls={`citations-${entry.id}`}
                    >
                      Citations ({entry.citations.length})
                    </Button>
                    <Collapse in={Boolean(openCitations[entry.id])}>
                      <List id={`citations-${entry.id}`} dense>
                        {entry.citations.map((citation, idx) => (
                          <ListItem key={idx} sx={{ py: 0.5 }}>
                            <ListItemText
                              primary={
                                <Button
                                  size="small"
                                  startIcon={<OpenInNewIcon />}
                                  href={citation.url}
                                  target="_blank"
                                  rel="noopener noreferrer"
                                  sx={{ textTransform: 'none', justifyContent: 'flex-start' }}
                                >
                                  {citation.title}
                                </Button>
                              }
                            />
                          </ListItem>
                        ))}
                      </List>
                    </Collapse>
                  </Box>
                )}

                {/* Per-entry Notes */}
                <Box sx={{ mb: 2 }}>
                  <Typography variant="subtitle2" color="text.secondary" gutterBottom>
                    Notes:
                  </Typography>
                  {editingEntryNotes[entry.id] ? (
                    <Box>
                      <TextField
                        fullWidth
                        multiline
                        minRows={3}
                        value={entryNotesDraft[entry.id] || ''}
                        onChange={(e) => setEntryNotesDraft(prev => ({ ...prev, [entry.id]: e.target.value }))}
                        placeholder="Add personal notes (plain text, rendered in italics)..."
                        sx={{ mb: 1 }}
                      />
                      <Box sx={{ display: 'flex', gap: 1 }}>
                        <Button variant="contained" size="small" onClick={() => handleSaveEntryNotes(entry.id)}>Save</Button>
                        <Button size="small" onClick={() => cancelEditEntryNotes(entry.id)}>Cancel</Button>
                      </Box>
                    </Box>
                  ) : (
                    <Box>
                      {entry.notes ? (
                        <Typography variant="body2" sx={{ fontStyle: 'italic', whiteSpace: 'pre-wrap' }}>
                          {entry.notes}
                        </Typography>
                      ) : (
                        <Typography variant="body2" color="text.secondary" sx={{ fontStyle: 'italic' }}>
                          No notes yet.
                        </Typography>
                      )}
                      <Box sx={{ mt: 1 }}>
                        <Button size="small" variant="outlined" onClick={() => startEditEntryNotes(entry.id, entry.notes)}>
                          {entry.notes ? 'Edit' : 'Add Note'}
                        </Button>
                      </Box>
                    </Box>
                  )}
                </Box>

                <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mt: 2 }}>
                  <Typography variant="caption" color="text.secondary">
                    Added: {new Date(entry.created_at).toLocaleString()}
                  </Typography>
                  <Button
                    size="small"
                    onClick={() => openProject(entry.project_id)}
                    startIcon={<OpenInNewIcon />}
                  >
                    View Project
                  </Button>
                </Box>
              </CardContent>
            </Card>
          ))}
        </Box>
      )}

      {/* Delete Confirmation Dialog */}
      <Dialog open={deleteDialogOpen} onClose={() => setDeleteDialogOpen(false)}>
        <DialogTitle>Delete Entry</DialogTitle>
        <DialogContent>
          <Typography>
            Are you sure you want to delete this entry? This action cannot be undone.
          </Typography>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setDeleteDialogOpen(false)}>Cancel</Button>
          <Button
            onClick={() => entryToDelete && handleDeleteEntry(entryToDelete)}
            color="error"
            variant="contained"
          >
            Delete
          </Button>
        </DialogActions>
      </Dialog>
    </Container>
  );
};

export default NotebookPage;

