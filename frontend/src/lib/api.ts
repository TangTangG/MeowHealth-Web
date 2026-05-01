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