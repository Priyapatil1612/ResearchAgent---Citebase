import axios from 'axios';
import { Project, ProjectCreate, QuestionRequest, QuestionResponse, Notebook, NotebookCreate, NotebookEntryCreate, ChatMessage, NotebookUpdate, NotebookEntryUpdate } from '../types';

const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000/api';

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Initialize default Authorization header from localStorage at startup
(() => {
  const token = localStorage.getItem('auth_token');
  if (token) {
    const dh: any = (api.defaults.headers as any);
    if (dh && typeof dh.set === 'function') {
      dh.set('Authorization', `Bearer ${token}`);
    } else if (dh && dh.common) {
      dh.common['Authorization'] = `Bearer ${token}`;
    } else {
      (api.defaults.headers as any)['Authorization'] = `Bearer ${token}`;
    }
  }
})();

// Add auth token to requests (robust to AxiosHeaders)
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('auth_token');
  if (!config.headers) config.headers = {} as any;
  if (token) {
    const h: any = config.headers as any;
    if (typeof h.set === 'function') {
      h.set('Authorization', `Bearer ${token}`);
    } else {
      h['Authorization'] = `Bearer ${token}`;
    }
  }
  return config;
});

// Optional: handle responses here if needed; avoid clearing tokens automatically to prevent loops
api.interceptors.response.use(
  (res) => res,
  (err) => Promise.reject(err)
);

// Project API
export const projectApi = {
  create: async (projectData: ProjectCreate): Promise<Project> => {
    const response = await api.post('/projects', projectData);
    return response.data;
  },

  getAll: async (): Promise<Project[]> => {
    const response = await api.get('/projects');
    return response.data;
  },

  getById: async (id: string): Promise<Project> => {
    const response = await api.get(`/projects/${id}`);
    return response.data;
  },

  delete: async (id: string): Promise<any> => {
    const response = await api.delete(`/projects/${id}`);
    return response.data;
  },

  startResearch: async (id: string, force: boolean = false): Promise<any> => {
    const response = await api.post(`/projects/${id}/research`, null, {
      params: { force }
    });
    return response.data;
  },

  askQuestion: async (id: string, questionData: QuestionRequest): Promise<QuestionResponse> => {
    const response = await api.post(`/projects/${id}/ask`, questionData);
    return response.data;
  },

  getChats: async (id: string): Promise<ChatMessage[]> => {
    const response = await api.get(`/projects/${id}/chats`);
    return response.data;
  },
};

// Notebook API
export const notebookApi = {
  create: async (notebookData: NotebookCreate): Promise<Notebook> => {
    const response = await api.post('/notebooks', notebookData);
    return response.data;
  },

  getAll: async (): Promise<Notebook[]> => {
    const response = await api.get('/notebooks');
    return response.data;
  },

  getById: async (id: string): Promise<Notebook> => {
    const response = await api.get(`/notebooks/${id}`);
    return response.data;
  },

  delete: async (id: string): Promise<any> => {
    const response = await api.delete(`/notebooks/${id}`);
    return response.data;
  },

  addEntry: async (notebookId: string, entryData: NotebookEntryCreate): Promise<any> => {
    const response = await api.post(`/notebooks/${notebookId}/entries`, entryData);
    return response.data;
  },

  update: async (id: string, notebookPatch: NotebookUpdate): Promise<Notebook> => {
    const response = await api.patch(`/notebooks/${id}`, notebookPatch);
    return response.data;
  },

  updateEntry: async (notebookId: string, entryId: string, entryPatch: NotebookEntryUpdate): Promise<any> => {
    const response = await api.patch(`/notebooks/${notebookId}/entries/${entryId}`, entryPatch);
    return response.data;
  },

  deleteEntry: async (notebookId: string, entryId: string): Promise<any> => {
    const response = await api.delete(`/notebooks/${notebookId}/entries/${entryId}`);
    return response.data;
  },
};

// Health check
export const healthApi = {
  check: async (): Promise<any> => {
    const response = await api.get('/health');
    return response.data;
  },
};

export const authApi = {
  signup: async (email: string, password: string): Promise<{ access_token: string; token_type: string }> => {
    const response = await api.post('/auth/signup', { email, password });
    return response.data;
  },
  login: async (email: string, password: string): Promise<{ access_token: string; token_type: string }> => {
    const response = await api.post('/auth/login', { email, password });
    return response.data;
  },
  me: async (): Promise<{ id: string; email: string; created_at: string }> => {
    const response = await api.get('/me');
    return response.data;
  },
};

export default api;

