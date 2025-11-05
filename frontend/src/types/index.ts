export interface Project {
  id: string;
  name: string;
  description?: string;
  topic: string;
  namespace: string;
  created_at: string;
  last_accessed: string;
  research_summary?: {
    indexed_pages: number;
    indexed_chunks: number;
    sources: Array<{
      title: string;
      url: string;
      text_len: number;
    }>;
    did_ingest: boolean;
  };
  status: 'created' | 'researching' | 'completed' | 'error';
}

export interface ProjectCreate {
  name: string;
  description?: string;
  topic: string;
  namespace?: string;
}

export interface QuestionRequest {
  question: string;
  top_k?: number;
}

export interface QuestionResponse {
  answer: string;
  citations: Array<{
    url: string;
    title: string;
  }>;
  trace: string[];
}

export interface Notebook {
  id: string;
  name: string;
  description?: string;
  notes?: string;
  created_at: string;
  updated_at: string;
  entries: NotebookEntry[];
}

export interface NotebookCreate {
  name: string;
  description?: string;
}

export interface NotebookEntry {
  id: string;
  question: string;
  answer: string;
  citations: Array<{
    url: string;
    title: string;
  }>;
  project_id: string;
  created_at: string;
  notes?: string;
}

export interface NotebookEntryCreate {
  question: string;
  answer: string;
  citations: Array<{
    url: string;
    title: string;
  }>;
  project_id: string;
  notes?: string;
}

export interface ChatMessage {
  id: string;
  type: 'user' | 'assistant';
  content: string;
  citations?: Array<{ url: string; title: string }>;
  timestamp: string;
}

export interface NotebookUpdate {
  name?: string;
  description?: string;
  notes?: string;
}

export interface NotebookEntryUpdate {
  question?: string;
  answer?: string;
  citations?: Array<{
    url: string;
    title: string;
  }>;
  notes?: string;
}

