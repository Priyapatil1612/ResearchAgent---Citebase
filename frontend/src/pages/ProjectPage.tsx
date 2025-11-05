import React, { useState, useEffect, useRef } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import {
  Container,
  Typography,
  Box,
  Paper,
  TextField,
  Button,
  Alert,
  CircularProgress,
  Chip,
  List,
  ListItem,
  ListItemText,
  Divider,
  IconButton,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Grid,
  Card,
  CardContent,
  Collapse,
} from '@mui/material';
import {
  Send as SendIcon,
  BookmarkAdd as BookmarkAddIcon,
  ArrowBack as ArrowBackIcon,
  OpenInNew as OpenInNewIcon,
  ContentCopy as CopyIcon,
  ExpandMore as ExpandMoreIcon,
  ExpandLess as ExpandLessIcon,
} from '@mui/icons-material';
import ReactMarkdown from 'react-markdown';
import { Project, QuestionResponse, Notebook, NotebookCreate, ChatMessage } from '../types';
import { projectApi, notebookApi } from '../services/api';

const stripSources = (text: string): string => {
  const pattern = /(\n|^)\s*(#+\s*)?(sources|citations|references)\s*:?\s*[\s\S]*$/i;
  return text.replace(pattern, '').trim();
};

const ProjectPage: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const [project, setProject] = useState<Project | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [question, setQuestion] = useState('');
  const [asking, setAsking] = useState(false);
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [notebooks, setNotebooks] = useState<Notebook[]>([]);
  const [saveDialogOpen, setSaveDialogOpen] = useState(false);
  const [selectedMessage, setSelectedMessage] = useState<ChatMessage | null>(null);
  const [newNotebook, setNewNotebook] = useState<NotebookCreate>({ name: '', description: '' });
  const [selectedNotebookId, setSelectedNotebookId] = useState<string>('');
  const [saveMode, setSaveMode] = useState<'existing' | 'new'>('existing');
  const [openCitations, setOpenCitations] = useState<Record<string, boolean>>({});
  const toggleCitations = (messageId: string) =>
    setOpenCitations(prev => ({ ...prev, [messageId]: !prev[messageId] }));

  useEffect(() => {
    if (id) {
      loadProject();
      loadNotebooks();
      loadChats();
    }
  }, [id]);

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  const loadProject = async () => {
    try {
      setLoading(true);
      setError(null);
      const data = await projectApi.getById(id!);
      setProject(data);
    } catch (err) {
      setError('Failed to load project. Please try again.');
      console.error('Error loading project:', err);
    } finally {
      setLoading(false);
    }
  };

  const loadNotebooks = async () => {
    try {
      const data = await notebookApi.getAll();
      setNotebooks(data);
    } catch (err) {
      console.error('Error loading notebooks:', err);
    }
  };

  const loadChats = async () => {
    try {
      const data = await projectApi.getChats(id!);
      setMessages(data.map(m => ({
        id: m.id,
        type: m.type,
        content: stripSources(m.content),
        citations: m.citations,
        timestamp: m.timestamp,
      })));
    } catch (err) {
      console.error('Error loading chats:', err);
    }
  };

  const handleAskQuestion = async () => {
    if (!question.trim() || !project) return;

    const userMessage: ChatMessage = {
      id: Date.now().toString(),
      type: 'user',
      content: question,
      timestamp: new Date().toISOString(),
    };

    setMessages(prev => [...prev, userMessage]);
    setQuestion('');
    setAsking(true);

    try {
      const response = await projectApi.askQuestion(project.id, {
        question: question,
        top_k: 6,
      });

      const assistantMessage: ChatMessage = {
        id: (Date.now() + 1).toString(),
        type: 'assistant',
        content: stripSources(response.answer),
        citations: response.citations,
        timestamp: new Date().toISOString(),
      };

      setMessages(prev => [...prev, assistantMessage]);
    } catch (err) {
      const errorMessage: ChatMessage = {
        id: (Date.now() + 1).toString(),
        type: 'assistant',
        content: 'Sorry, I encountered an error while processing your question. Please try again.',
        timestamp: new Date().toISOString(),
      };
      setMessages(prev => [...prev, errorMessage]);
      console.error('Error asking question:', err);
    } finally {
      setAsking(false);
    }
  };

  const handleKeyPress = (event: React.KeyboardEvent) => {
    if (event.key === 'Enter' && !event.shiftKey) {
      event.preventDefault();
      handleAskQuestion();
    }
  };

  const handleSaveToNotebook = (message: ChatMessage) => {
    setSelectedMessage(message);
    setSaveMode('existing');
    setSelectedNotebookId('');
    setSaveDialogOpen(true);
  };

  const handleSaveToExistingNotebook = async () => {
    if (!selectedMessage || !project || !selectedNotebookId) return;

    try {
      await notebookApi.addEntry(selectedNotebookId, {
        question: (() => {
          if (selectedMessage.type === 'user') return selectedMessage.content;
          const lastUser = [...messages].reverse().find(m => m.type === 'user');
          return lastUser ? lastUser.content : '';
        })(),
        answer: selectedMessage.type === 'assistant' ? selectedMessage.content : '',
        citations: selectedMessage.citations || [],
        project_id: project.id,
      });

      setSaveDialogOpen(false);
      setSelectedMessage(null);
      setSelectedNotebookId('');
    } catch (err) {
      console.error('Error saving to notebook:', err);
    }
  };

  const handleCreateNotebookAndSave = async () => {
    if (!selectedMessage || !project) return;

    try {
      const notebook = await notebookApi.create(newNotebook);
      await notebookApi.addEntry(notebook.id, {
        question: (() => {
          if (selectedMessage.type === 'user') return selectedMessage.content;
          const lastUser = [...messages].reverse().find(m => m.type === 'user');
          return lastUser ? lastUser.content : '';
        })(),
        answer: selectedMessage.type === 'assistant' ? selectedMessage.content : '',
        citations: selectedMessage.citations || [],
        project_id: project.id,
      });

      setNotebooks(prev => [...prev, notebook]);
      setSaveDialogOpen(false);
      setSelectedMessage(null);
      setNewNotebook({ name: '', description: '' });
    } catch (err) {
      console.error('Error saving to notebook:', err);
    }
  };

  const copyToClipboard = (text: string) => {
    navigator.clipboard.writeText(text);
  };

  if (loading) {
    return (
      <Container maxWidth="lg" sx={{ mt: 4, textAlign: 'center' }}>
        <CircularProgress size={60} />
        <Typography variant="h6" sx={{ mt: 2 }}>
          Loading project...
        </Typography>
      </Container>
    );
  }

  if (error || !project) {
    return (
      <Container maxWidth="lg" sx={{ mt: 4 }}>
        <Alert severity="error" sx={{ mb: 3 }}>
          {error || 'Project not found'}
        </Alert>
        <Button
          variant="contained"
          startIcon={<ArrowBackIcon />}
          onClick={() => navigate('/')}
        >
          Back to Projects
        </Button>
      </Container>
    );
  }

  return (
    <Container maxWidth="lg" sx={{ mt: 4 }}>
      <Box sx={{ display: 'flex', alignItems: 'center', mb: 3 }}>
        <IconButton onClick={() => navigate('/')} sx={{ mr: 2 }}>
          <ArrowBackIcon />
        </IconButton>
        <Box sx={{ flexGrow: 1 }}>
          <Typography variant="h4" component="h1">
            {project.name}
          </Typography>
          <Typography variant="body1" color="text.secondary">
            {project.topic}
          </Typography>
        </Box>
        <Chip
          label={project.status}
          color={project.status === 'completed' ? 'success' : 'default'}
        />
      </Box>

      {project.description && (
        <Alert severity="info" sx={{ mb: 3 }}>
          {project.description}
        </Alert>
      )}

      {/* Research summary intentionally hidden per requirements */}

      <Paper sx={{ height: '60vh', display: 'flex', flexDirection: 'column' }}>
        <Box sx={{ p: 2, borderBottom: 1, borderColor: 'divider' }}>
          <Typography variant="h6">Chat with Research Agent</Typography>
        </Box>
        
        <Box sx={{ flexGrow: 1, overflow: 'auto', p: 2 }}>
          {messages.length === 0 ? (
            <Box sx={{ textAlign: 'center', py: 4 }}>
              <Typography variant="body1" color="text.secondary">
                Ask questions about your research topic to get started
              </Typography>
            </Box>
          ) : (
            <List>
              {messages.map((message) => (
                <React.Fragment key={message.id}>
                  <ListItem
                    sx={{
                      flexDirection: 'column',
                      alignItems: 'flex-start',
                      py: 2,
                    }}
                  >
                    <Box
                      sx={{
                        display: 'flex',
                        justifyContent: 'space-between',
                        alignItems: 'center',
                        width: '100%',
                        mb: 1,
                      }}
                    >
                      <Typography variant="subtitle2" color="text.secondary">
                        {message.type === 'user' ? 'You' : 'Research Agent'}
                      </Typography>
                      <Box>
                        <IconButton
                          size="small"
                          onClick={() => copyToClipboard(message.content)}
                        >
                          <CopyIcon fontSize="small" />
                        </IconButton>
                        {message.type === 'assistant' && (
                          <IconButton
                            size="small"
                            onClick={() => handleSaveToNotebook(message)}
                          >
                            <BookmarkAddIcon fontSize="small" />
                          </IconButton>
                        )}
                      </Box>
                    </Box>
                    
                    <Box
                      sx={{
                        backgroundColor: message.type === 'user' ? 'primary.main' : 'grey.100',
                        color: message.type === 'user' ? 'white' : 'text.primary',
                        p: 2,
                        borderRadius: 2,
                        maxWidth: '80%',
                        alignSelf: message.type === 'user' ? 'flex-end' : 'flex-start',
                      }}
                    >
                      <ReactMarkdown>{message.content}</ReactMarkdown>
                    </Box>

                    {message.citations && message.citations.length > 0 && (
                      <Box sx={{ mt: 1, maxWidth: '80%' }}>
                        <Button
                          size="small"
                          onClick={() => toggleCitations(message.id)}
                          endIcon={openCitations[message.id] ? <ExpandLessIcon /> : <ExpandMoreIcon />}
                          aria-expanded={Boolean(openCitations[message.id])}
                          aria-controls={`citations-${message.id}`}
                        >
                          Citations ({message.citations.length})
                        </Button>
                        {openCitations[message.id] && (
                          <Box id={`citations-${message.id}`} sx={{ mt: 0.5 }}>
                            {message.citations.map((citation, index) => (
                              <Box key={index} sx={{ mb: 0.5 }}>
                                <Button
                                  size="small"
                                  startIcon={<OpenInNewIcon />}
                                  href={citation.url}
                                  target="_blank"
                                  rel="noopener noreferrer"
                                >
                                  {citation.title}
                                </Button>
                              </Box>
                            ))}
                          </Box>
                        )}
                      </Box>
                    )}
                  </ListItem>
                  <Divider />
                </React.Fragment>
              ))}
              {asking && (
                <ListItem>
                  <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                    <CircularProgress size={20} />
                    <Typography variant="body2" color="text.secondary">
                      Thinking...
                    </Typography>
                  </Box>
                </ListItem>
              )}
              <div ref={messagesEndRef} />
            </List>
          )}
        </Box>

        <Box sx={{ p: 2, borderTop: 1, borderColor: 'divider' }}>
          <Box sx={{ display: 'flex', gap: 1 }}>
            <TextField
              fullWidth
              placeholder="Ask a question about your research..."
              value={question}
              onChange={(e) => setQuestion(e.target.value)}
              onKeyPress={handleKeyPress}
              disabled={asking || project.status !== 'completed'}
              multiline
              maxRows={4}
            />
            <Button
              variant="contained"
              onClick={handleAskQuestion}
              disabled={!question.trim() || asking || project.status !== 'completed'}
              startIcon={<SendIcon />}
            >
              Send
            </Button>
          </Box>
        </Box>
      </Paper>

      {/* Save to Notebook Dialog */}
      <Dialog open={saveDialogOpen} onClose={() => setSaveDialogOpen(false)} maxWidth="sm" fullWidth>
        <DialogTitle>Save to Notebook</DialogTitle>
        <DialogContent>
          <Box sx={{ mb: 3 }}>
            <Button
              variant={saveMode === 'existing' ? 'contained' : 'outlined'}
              onClick={() => setSaveMode('existing')}
              sx={{ mr: 2 }}
            >
              Save to Existing Notebook
            </Button>
            <Button
              variant={saveMode === 'new' ? 'contained' : 'outlined'}
              onClick={() => setSaveMode('new')}
            >
              Create New Notebook
            </Button>
          </Box>

          {saveMode === 'existing' ? (
            <TextField
              select
              label="Select Notebook"
              value={selectedNotebookId}
              onChange={(e) => setSelectedNotebookId(e.target.value)}
              fullWidth
              sx={{ mb: 2 }}
              SelectProps={{
                native: true,
              }}
            >
              <option value="">Choose a notebook...</option>
              {notebooks.map((notebook) => (
                <option key={notebook.id} value={notebook.id}>
                  {notebook.name}
                </option>
              ))}
            </TextField>
          ) : (
            <>
              <TextField
                label="Notebook Name"
                value={newNotebook.name}
                onChange={(e) => setNewNotebook(prev => ({ ...prev, name: e.target.value }))}
                fullWidth
                sx={{ mb: 2 }}
              />
              <TextField
                label="Description (Optional)"
                value={newNotebook.description}
                onChange={(e) => setNewNotebook(prev => ({ ...prev, description: e.target.value }))}
                fullWidth
                multiline
                rows={3}
              />
            </>
          )}
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setSaveDialogOpen(false)}>Cancel</Button>
          <Button
            onClick={saveMode === 'existing' ? handleSaveToExistingNotebook : handleCreateNotebookAndSave}
            variant="contained"
            disabled={
              saveMode === 'existing' 
                ? !selectedNotebookId 
                : !newNotebook.name.trim()
            }
          >
            {saveMode === 'existing' ? 'Save to Notebook' : 'Create & Save'}
          </Button>
        </DialogActions>
      </Dialog>
    </Container>
  );
};

export default ProjectPage;

