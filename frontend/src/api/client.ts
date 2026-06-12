import axios from 'axios';

const API_BASE = 'http://127.0.0.1:8000/api';

const api = axios.create({
  baseURL: API_BASE,
  headers: { 'Content-Type': 'application/json' },
});

// --- Types ---
export interface TraitScores {
  content_ideas: number;
  organization: number;
  language_use: number;
  conventions: number;
  vocabulary: number;
}

export interface GrammarError {
  message: string;
  context: string;
  offset: number;
  length: number;
  rule: string;
  replacements: string[];
  category: string;
}

export interface EvaluateResponse {
  score_100: number;
  grade: string;
  confidence: number;
  raw_score: number;
  raw_score_range: number[];
  prompt_id: number;
  traits: TraitScores;
  trait_total: number;
  trait_max: number;
  grammar_errors: GrammarError[];
  grammar_error_count: number;
  word_count: number;
  char_count: number;
  sentence_count: number;
  paragraph_count: number;
  unique_words: number;
  language_detected: string;
  writing_consistency: number;
  readability: Record<string, number>;
  analytics: Record<string, number>;
  essay_id?: number;
}

export interface EssayListItem {
  id: number;
  title: string;
  language: string;
  word_count: number;
  score_100: number;
  grade: string;
  created_at: string;
}

export interface DashboardStats {
  average_score: number;
  essays_evaluated: number;
  best_grade: string;
  best_essay_title: string;
  recent_essays: EssayListItem[];
  skill_breakdown: Record<string, number>;
  improvement_plan: {
    strengths: string[];
    focus_areas: string[];
  };
}

export interface AnalyticsData {
  metrics: Record<string, number>;
  score_progress: Array<{
    label: string;
    english: number;
    kannada: number;
  }>;
  writing_consistency: number;
  total_essays: number;
}

// --- API calls ---
export async function evaluateEssay(
  text: string,
  promptId: number = 1,
  title?: string,
  save: boolean = true
): Promise<EvaluateResponse> {
  const res = await api.post('/evaluate', {
    text,
    prompt_id: promptId,
    title,
    save,
  });
  return res.data;
}

export async function getEssays(limit = 20): Promise<EssayListItem[]> {
  const res = await api.get('/essays', { params: { limit } });
  return res.data;
}

export async function getEssay(id: number): Promise<EvaluateResponse> {
  const res = await api.get(`/essays/${id}`);
  return res.data;
}

export async function deleteEssay(id: number): Promise<void> {
  await api.delete(`/essays/${id}`);
}

export async function getDashboard(): Promise<DashboardStats> {
  const res = await api.get('/dashboard');
  return res.data;
}

export async function getAnalytics(): Promise<AnalyticsData> {
  const res = await api.get('/analytics');
  return res.data;
}

export default api;
