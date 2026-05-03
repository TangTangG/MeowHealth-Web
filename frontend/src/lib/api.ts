import axios from 'axios';
import type {
  Cat, CatCreate,
  WeightLog, WeightLogCreate,
  Reminder, ReminderCreate,
  HealthRecord
} from '@/types';

const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:8000/api/v1';

const api = axios.create({
  baseURL: API_BASE,
  headers: {
    'Content-Type': 'application/json',
  },
});

// ========== 猫咪 API ==========

export const getCats = () => api.get<Cat[]>('/cats/').then(r => r.data);

export const getCat = (id: string) => api.get<Cat>(`/cats/${id}`).then(r => r.data);

export const createCat = (cat: CatCreate) => api.post<Cat>('/cats/', cat).then(r => r.data);

export const updateCat = (id: string, cat: CatCreate) =>
  api.put<Cat>(`/cats/${id}`, cat).then(r => r.data);

export const deleteCat = (id: string) => api.delete(`/cats/${id}`).then(r => r.data);

// ========== 体重记录 API ==========

export const getWeightLogs = (catId: string, limit: number = 30) =>
  api.get<WeightLog[]>(`/cats/${catId}/weights`, { params: { limit } }).then(r => r.data);

export const createWeightLog = (catId: string, log: WeightLogCreate) =>
  api.post<WeightLog>(`/cats/${catId}/weights`, log).then(r => r.data);

// ========== 提醒 API ==========

export const getReminders = (catId: string, includeCompleted: boolean = false) =>
  api.get<Reminder[]>(`/cats/${catId}/reminders`, { params: { include_completed: includeCompleted } }).then(r => r.data);

export const createReminder = (catId: string, reminder: ReminderCreate) =>
  api.post<Reminder>(`/cats/${catId}/reminders`, reminder).then(r => r.data);

export const completeReminder = (reminderId: string) =>
  api.post(`/reminders/${reminderId}/complete`).then(r => r.data);

export const deleteReminder = (reminderId: string) =>
  api.delete(`/reminders/${reminderId}`).then(r => r.data);

// ========== 健康记录 API ==========

export const getHealthRecords = (catId: string, type?: string, limit: number = 50) =>
  api.get<HealthRecord[]>(`/health-records/cat/${catId}`, { params: { type, limit } }).then(r => r.data);

// ========== 化验单 API ==========

export const uploadReport = (catId: string, file: File) => {
  const formData = new FormData();
  formData.append('file', file);
  return api.post('/reports/upload/' + catId, formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
  }).then(r => r.data);
};

export const getReports = (catId: string) =>
  api.get(`/reports/cat/${catId}`).then(r => r.data);

export const deleteReport = (reportId: string) =>
  api.delete(`/reports/${reportId}`).then(r => r.data);

export const analyzeReport = (reportId: string) =>
  api.post(`/reports/${reportId}/analyze`).then(r => r.data);

// ========== 报告聊天 API ==========

export const getReportChatHistory = (reportId: string) =>
  api.get(`/reports/${reportId}/chat/history`).then(r => r.data);

export const sendReportChatMessage = (reportId: string, content: string) =>
  api.post(`/reports/${reportId}/chat`, { content }).then(r => r.data);

// ========== 设置 API ==========

export const setApiKey = (apiKey: string) =>
  api.post('/settings/api-key', { api_key: apiKey }).then(r => r.data);

export const getApiKeyStatus = () =>
  api.get('/settings/api-key/status').then(r => r.data);

// ========== 行动 API (Phase 5) ==========

export const executeActions = (reportId: string) =>
  api.post(`/actions/execute/${reportId}`).then(r => r.data);

// ========== 症状咨询（兽医院式诊疗流水线）API ==========

export interface ConsultationStartRequest {
  cat_id: string;
  initial_symptoms: string;
}

export interface ConsultationStartResponse {
  session_id: string;
  status: string;
  triage_level: string;
  triage_advice: string;
  questions: string[];
  is_sufficient: boolean;
  next_action: string;
  health_record_id: string;
}

export interface ConsultationContinueRequest {
  user_input: Record<string, any>;
}

export interface ConsultationContinueResponse {
  session_id: string;
  status: string;
  current_round: number;
  questions: string[];
  is_sufficient: boolean;
  next_action: string;
  collected_summary: string;
  diagnosis: any;
  triage_result: any;
  error?: string;
}

export interface ConsultationStatusResponse {
  session_id: string;
  status: string;
  current_round: number;
  triage_result: any;
  collected_summary: Record<string, any>;
  error?: string;
}

export const startConsultation = (data: ConsultationStartRequest) =>
  api.post<ConsultationStartResponse>('/consultation/start', data).then(r => r.data);

export const continueConsultation = (sessionId: string, data: ConsultationContinueRequest) =>
  api.post<ConsultationContinueResponse>(`/consultation/${sessionId}/continue`, data).then(r => r.data);

export const getConsultationStatus = (sessionId: string) =>
  api.get<ConsultationStatusResponse>(`/consultation/${sessionId}/status`).then(r => r.data);

export const cancelConsultation = (sessionId: string) =>
  api.post<ConsultationContinueResponse>(`/consultation/${sessionId}/cancel`).then(r => r.data);

// ========== 健康档案 API ==========

export const getCatHealthRecords = (catId: string) =>
  api.get<import('@/types').HealthRecordWithDetails[]>(`/consultation/cats/${catId}/health-records`).then(r => r.data);