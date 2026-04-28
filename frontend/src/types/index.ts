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

// 聊天消息
export interface ChatMessage {
  id: string;
  record_id: string;
  role: 'user' | 'model';
  content: string;
  created_at: string;
}