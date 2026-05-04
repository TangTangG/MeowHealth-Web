// Cat 类型
export interface Cat {
  id: string;
  name: string;
  breed: string;
  birthday: string;
  gender: string;
  is_neutered: boolean;
  photo_path?: string;
  target_weight_min?: number;
  target_weight_max?: number;
  created_at: string;
  updated_at: string;
}

// 创建猫咪请求
export interface CatCreate {
  name: string;
  breed: string;
  birthday: string;
  gender: string;
  is_neutered?: boolean;
  photo_path?: string;
  target_weight_min?: number;
  target_weight_max?: number;
}

// 体重记录
export interface WeightLog {
  id: string;
  cat_id: string;
  date: string;
  value: number;
  note?: string;
  created_at: string;
  updated_at: string;
}

// 创建体重记录
export interface WeightLogCreate {
  date: string;
  value: number;
  note?: string;
}

// 待办提醒
export interface Reminder {
  id: string;
  cat_id?: string;
  title: string;
  description?: string;
  reminder_type: string;
  due_date: string;
  is_completed: boolean;
  completed_at?: string;
  created_at: string;
  updated_at: string;
}

// 创建提醒
export interface ReminderCreate {
  cat_id?: string;
  title: string;
  description?: string;
  reminder_type: string;
  due_date: string;
  is_completed?: boolean;
}

// 健康记录
export interface HealthRecord {
  id: string;
  cat_id: string;
  date: string;
  type: string;
  title: string;
  note?: string;
  ai_summary?: string;
  actionable_advice?: string[];
  created_at: string;
  updated_at: string;
}

// 健康指标
export interface HealthIndicator {
  id: string;
  record_id: string;
  name: string;
  display_name: string;
  value?: number;
  unit: string;
  reference_min?: number;
  reference_max?: number;
  is_abnormal: boolean;
  explanation?: string;
}

// 症状记录
export interface SymptomLog {
  id: string;
  cat_id: string;
  record_id?: string;
  symptom_description: string;
  severity: number; // 1-5
  onset_time: string;
  duration_hours?: number;
  is_ongoing: boolean;
  photo_urls?: string[];
  triggers?: string;
  created_at: string;
  updated_at: string;
}

// 生命体征
export interface VitalSign {
  id: string;
  cat_id: string;
  record_id?: string;
  weight_kg: number;
  temperature_celsius?: number;
  heart_rate?: number;
  respiratory_rate?: number;
  spirit_status?: string;
  appetite_score?: number; // 1-5
  water_intake_ml?: number;
  stool_status?: string;
  measured_at: string;
  created_at: string;
  updated_at: string;
}

// 报告附件
export interface ReportAttachment {
  id: string;
  record_id: string;
  file_name: string;
  file_type: string;
  file_path: string;
  created_at: string;
}

// 健康记录详情（含 symptom_logs, vital_signs, indicators, attachments）
export interface HealthRecordWithDetails {
  id: string;
  cat_id: string;
  date: string;
  type: string;
  title: string;
  note?: string;
  ai_summary?: string;
  actionable_advice?: string[];
  consultation_type: string;
  triage_level?: string;
  treatment_status: string;
  next_followup_at?: string;
  symptom_logs: SymptomLog[];
  vital_signs: VitalSign[];
  indicators: HealthIndicator[];
  attachments: ReportAttachment[];
  created_at: string;
  updated_at: string;
}

export interface VaccinationRecord {
  id: string;
  cat_id: string;
  vaccine_type: 'FVRCP' | 'rabies' | 'other';
  vaccine_name: string;
  batch_number?: string;
  administered_at: string;
  next_due_at?: string;
  administered_by?: string;
  note?: string;
  created_at: string;
  updated_at: string;
}

export interface DewormingRecord {
  id: string;
  cat_id: string;
  product_name: string;
  deworm_type: 'internal' | 'external' | 'combo';
  administered_at: string;
  next_due_at?: string;
  dosage?: string;
  note?: string;
  created_at: string;
  updated_at: string;
}


// ========== 分析图表类型 (Phase 9) ==========

export interface WeightTrendData {
  date: string;
  weight: number;
}

export interface WeightTrendResponse {
  cat_id: string;
  days: number;
  data: WeightTrendData[];
  count: number;
}

export interface IndicatorHistoryPoint {
  date: string;
  value: number | null;
  unit: string;
  reference_min: number | null;
  reference_max: number | null;
  is_abnormal: boolean;
}

export interface HealthScorePoint {
  date: string;
  score: number;
  weight: number;
}

export interface HealthScoreHistoryResponse {
  cat_id: string;
  days: number;
  data: HealthScorePoint[];
}

export interface IndicatorNameItem {
  name: string;
  display_name: string;
}
