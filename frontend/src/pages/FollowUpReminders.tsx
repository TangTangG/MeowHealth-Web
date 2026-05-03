import { useState, useEffect, useMemo } from 'react';
import { useOutletContext } from 'react-router-dom';
import { Bell, Syringe, ClipboardList, Pill, Pin, Plus, AlertCircle, Check, Trash2, Clock, ChevronDown, ChevronUp } from 'lucide-react';
import { getReminders, createReminder, completeReminder, deleteReminder, getFollowUpRecords } from '@/lib/api';
import type { Reminder, HealthRecordWithDetails } from '@/types';

interface OutletContext {
  selectedCatId: string | null;
}

type FollowUpItemType = 'follow_up' | 'symptom_track' | 'medication' | 'general';

interface FollowUpItem {
  id: string;
  title: string;
  description?: string;
  dueDate: string;
  type: FollowUpItemType;
  source?: string;
  isCompleted: boolean;
  originalReminder?: Reminder;
  originalRecord?: HealthRecordWithDetails;
}

function getTypeFromReminderType(reminderType: string): FollowUpItemType {
  const t = reminderType.toLowerCase();
  if (t.includes('follow') || t.includes('复查')) return 'follow_up';
  if (t.includes('symptom') || t.includes('症状')) return 'symptom_track';
  if (t.includes('med') || t.includes('pill') || t.includes('drug') || t.includes('药')) return 'medication';
  return 'general';
}

function getIconForType(type: FollowUpItemType) {
  switch (type) {
    case 'follow_up': return <Syringe size={18} className="text-blue-500" />;
    case 'symptom_track': return <ClipboardList size={18} className="text-purple-500" />;
    case 'medication': return <Pill size={18} className="text-pink-500" />;
    default: return <Pin size={18} className="text-gray-500" />;
  }
}

function getTypeLabel(type: FollowUpItemType): string {
  switch (type) {
    case 'follow_up': return '复查提醒';
    case 'symptom_track': return '症状追踪';
    case 'medication': return '用药提醒';
    default: return '普通提醒';
  }
}

function daysUntil(dueDate: string): number {
  return Math.ceil((new Date(dueDate).getTime() - Date.now()) / (1000 * 60 * 60 * 24));
}

function isExpired(dueDate: string): boolean {
  return daysUntil(dueDate) < 0;
}

function isUrgent(dueDate: string): boolean {
  const d = daysUntil(dueDate);
  return d >= 0 && d <= 3;
}

function sameDay(a: string, b: string): boolean {
  const da = new Date(a).toDateString();
  const db = new Date(b).toDateString();
  return da === db;
}

function formatDueText(dueDate: string): string {
  const d = daysUntil(dueDate);
  if (d < 0) return `已过期 ${Math.abs(d)} 天`;
  if (d === 0) return '今天到期';
  if (d === 1) return '明天到期';
  return `${d} 天后到期`;
}

const TABS = [
  { key: 'all', label: '全部提醒' },
  { key: 'follow_up', label: '复查提醒' },
  { key: 'symptom_track', label: '症状追踪' },
  { key: 'expired', label: '已过期' },
];

export default function FollowUpReminders() {
  const { selectedCatId } = useOutletContext<OutletContext>();
  const [items, setItems] = useState<FollowUpItem[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState('all');
  const [showAddForm, setShowAddForm] = useState(false);

  const [newTitle, setNewTitle] = useState('');
  const [newType, setNewType] = useState<FollowUpItemType>('general');
  const [newDueDate, setNewDueDate] = useState('');
  const [newDescription, setNewDescription] = useState('');

  const loadData = async () => {
    if (!selectedCatId) return;
    setLoading(true);
    setError(null);
    try {
      const [remindersData, followUpData] = await Promise.all([
        getReminders(selectedCatId, false),
        getFollowUpRecords(selectedCatId),
      ]);

      const reminderItems: FollowUpItem[] = remindersData.map(r => ({
        id: r.id,
        title: r.title,
        description: r.description,
        dueDate: r.due_date,
        type: getTypeFromReminderType(r.reminder_type),
        source: undefined,
        isCompleted: r.is_completed,
        originalReminder: r,
      }));

      const followUpItems: FollowUpItem[] = followUpData
        .filter(record => record.next_followup_at)
        .map(record => ({
          id: `followup-${record.id}`,
          title: record.title || '复查提醒',
          description: record.note,
          dueDate: record.next_followup_at!,
          type: 'follow_up',
          source: `来自就诊记录：${new Date(record.date).toLocaleDateString('zh-CN')} ${record.type || ''}`,
          isCompleted: false,
          originalRecord: record,
        }));

      // Merge and deduplicate: if a reminder has same title and same due day as a follow-up record, keep reminder
      const merged: FollowUpItem[] = [...reminderItems];
      for (const fu of followUpItems) {
        const dup = merged.some(m => m.title === fu.title && sameDay(m.dueDate, fu.dueDate));
        if (!dup) {
          merged.push(fu);
        }
      }

      // Sort: expired first, then urgent, then by due date
      merged.sort((a, b) => new Date(a.dueDate).getTime() - new Date(b.dueDate).getTime());
      setItems(merged);
    } catch (err) {
      console.error('Failed to load follow-up data:', err);
      setError('加载提醒数据失败，请稍后重试');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, [selectedCatId]);

  const stats = useMemo(() => {
    const pending = items.filter(i => !i.isCompleted);
    const followUpPending = pending.filter(i => i.type === 'follow_up' && !isExpired(i.dueDate));
    const expiredCount = pending.filter(i => isExpired(i.dueDate)).length;
    return {
      totalPending: pending.length,
      followUpPending: followUpPending.length,
      expiredCount,
    };
  }, [items]);

  const filteredItems = useMemo(() => {
    if (activeTab === 'all') return items.filter(i => !i.isCompleted);
    if (activeTab === 'follow_up') return items.filter(i => !i.isCompleted && i.type === 'follow_up');
    if (activeTab === 'symptom_track') return items.filter(i => !i.isCompleted && i.type === 'symptom_track');
    if (activeTab === 'expired') return items.filter(i => !i.isCompleted && isExpired(i.dueDate));
    return items;
  }, [items, activeTab]);

  const handleComplete = async (item: FollowUpItem) => {
    if (!item.originalReminder) return;
    try {
      await completeReminder(item.originalReminder.id);
      loadData();
    } catch (err) {
      console.error('Failed to complete reminder:', err);
      setError('标记完成失败，请重试');
    }
  };

  const handleDelete = async (item: FollowUpItem) => {
    if (!item.originalReminder) {
      // Follow-up records from health records cannot be deleted via reminder API
      setError('系统生成的复查提醒无法删除，请在健康记录中修改');
      return;
    }
    if (!confirm('确定要删除这个提醒吗？')) return;
    try {
      await deleteReminder(item.originalReminder.id);
      loadData();
    } catch (err) {
      console.error('Failed to delete reminder:', err);
      setError('删除提醒失败，请重试');
    }
  };

  const handleSymptomTrackResponse = async (item: FollowUpItem, response: 'better' | 'same' | 'worse') => {
    console.log(`症状追踪 ${item.id}: ${response}`);
    if (item.originalReminder) {
      try {
        await completeReminder(item.originalReminder.id);
        loadData();
      } catch (err) {
        console.error('Failed to complete symptom track:', err);
      }
    }
  };

  const handleAddReminder = async () => {
    if (!selectedCatId || !newTitle || !newDueDate) return;
    try {
      await createReminder(selectedCatId, {
        title: newTitle,
        description: newDescription || undefined,
        reminder_type: newType,
        due_date: new Date(newDueDate).toISOString(),
      });
      setNewTitle('');
      setNewType('general');
      setNewDueDate('');
      setNewDescription('');
      setShowAddForm(false);
      loadData();
    } catch (err) {
      console.error('Failed to add reminder:', err);
      setError('添加提醒失败，请重试');
    }
  };

  if (!selectedCatId) {
    return (
      <div className="flex items-center justify-center h-96">
        <div className="text-center">
          <Bell size={48} className="text-gray-300 mx-auto mb-4" />
          <p className="text-gray-500 mb-4">请先在侧边栏选择一只猫咪</p>
          <a href="/cats" className="text-blue-600 hover:underline">去添加猫咪 →</a>
        </div>
      </div>
    );
  }

  return (
    <div className="max-w-4xl mx-auto p-4 space-y-4">
      {/* Header */}
      <div className="flex items-center justify-between">
        <h1 className="text-xl font-bold flex items-center gap-2">
          <Bell size={22} className="text-blue-600" />
          随访提醒管理
        </h1>
      </div>

      {/* Stats Bar */}
      <div className="grid grid-cols-3 gap-3">
        <div className="bg-white border border-gray-200 rounded-lg p-3">
          <div className="text-sm text-gray-500 mb-1">📋 待处理随访</div>
          <div className="text-2xl font-bold text-gray-800">{stats.totalPending}</div>
        </div>
        <div className="bg-white border border-gray-200 rounded-lg p-3">
          <div className="text-sm text-gray-500 mb-1">🏥 待复查</div>
          <div className="text-2xl font-bold text-blue-600">{stats.followUpPending}</div>
        </div>
        <div className="bg-white border border-gray-200 rounded-lg p-3">
          <div className="text-sm text-gray-500 mb-1">⚠️ 已过期</div>
          <div className="text-2xl font-bold text-red-600">{stats.expiredCount}</div>
        </div>
      </div>

      {/* Error Banner */}
      {error && (
        <div className="bg-red-50 border border-red-200 rounded-lg p-3 flex items-center gap-2 text-red-700">
          <AlertCircle size={18} />
          <span className="text-sm">{error}</span>
          <button onClick={() => setError(null)} className="ml-auto text-xs text-red-500 hover:underline">清除</button>
        </div>
      )}

      {/* Tab Navigation */}
      <div className="flex gap-1 bg-gray-100 p-1 rounded-lg">
        {TABS.map(tab => (
          <button
            key={tab.key}
            onClick={() => setActiveTab(tab.key)}
            className={`flex-1 py-2 px-3 text-sm font-medium rounded-md transition-colors ${
              activeTab === tab.key
                ? 'bg-white text-gray-900 shadow-sm'
                : 'text-gray-500 hover:text-gray-700'
            }`}
          >
            {tab.label}
          </button>
        ))}
      </div>

      {/* List */}
      {loading ? (
        <div className="flex items-center justify-center h-40 text-gray-400">
          <div className="animate-spin mr-2">
            <Clock size={20} />
          </div>
          加载中...
        </div>
      ) : filteredItems.length === 0 ? (
        <div className="bg-gray-50 border border-dashed border-gray-300 rounded-lg p-8 text-center">
          <Bell size={40} className="text-gray-300 mx-auto mb-3" />
          <p className="text-gray-500 text-sm">
            {activeTab === 'all' && '暂无待处理提醒'}
            {activeTab === 'follow_up' && '暂无复查提醒'}
            {activeTab === 'symptom_track' && '暂无症状追踪任务'}
            {activeTab === 'expired' && '暂无已过期提醒'}
          </p>
        </div>
      ) : (
        <div className="space-y-3">
          {filteredItems.map(item => (
            <div key={item.id}>
              {item.type === 'symptom_track' ? (
                /* Symptom Tracking Card */
                <div className={`p-4 rounded-lg border ${isExpired(item.dueDate) ? 'border-red-300 bg-red-50' : isUrgent(item.dueDate) ? 'border-orange-300 bg-orange-50' : 'border-purple-200 bg-white'}`}>
                  <div className="flex items-start gap-3 mb-3">
                    <div className="mt-0.5">{getIconForType(item.type)}</div>
                    <div className="flex-1">
                      <p className="font-medium text-sm text-gray-900">
                        {item.title}
                        <span className="ml-2 text-xs px-2 py-0.5 rounded-full bg-purple-100 text-purple-700">
                          {getTypeLabel(item.type)}
                        </span>
                      </p>
                      {item.description && (
                        <p className="text-sm text-gray-500 mt-1">{item.description}</p>
                      )}
                      <div className="flex items-center gap-1 mt-2 text-sm">
                        <Clock size={14} />
                        <span className={isExpired(item.dueDate) ? 'text-red-600 font-medium' : isUrgent(item.dueDate) ? 'text-orange-600 font-medium' : 'text-gray-500'}>
                          {formatDueText(item.dueDate)}
                        </span>
                      </div>
                      {item.source && (
                        <p className="text-xs text-gray-400 mt-1">{item.source}</p>
                      )}
                    </div>
                  </div>

                  {/* Quick Response Buttons */}
                  <div className="mt-3 pt-3 border-t border-gray-200/60">
                    <p className="text-sm text-gray-600 mb-2">症状有变化吗？</p>
                    <div className="flex gap-2">
                      <button
                        onClick={() => handleSymptomTrackResponse(item, 'better')}
                        className="flex-1 py-2 px-3 bg-green-50 hover:bg-green-100 text-green-700 text-sm rounded-lg border border-green-200 transition-colors"
                      >
                        好多了 😊
                      </button>
                      <button
                        onClick={() => handleSymptomTrackResponse(item, 'same')}
                        className="flex-1 py-2 px-3 bg-gray-50 hover:bg-gray-100 text-gray-700 text-sm rounded-lg border border-gray-200 transition-colors"
                      >
                        还是老样子 😐
                      </button>
                      <button
                        onClick={() => handleSymptomTrackResponse(item, 'worse')}
                        className="flex-1 py-2 px-3 bg-red-50 hover:bg-red-100 text-red-700 text-sm rounded-lg border border-red-200 transition-colors"
                      >
                        更差了 😟
                      </button>
                    </div>
                  </div>
                </div>
              ) : (
                /* General Reminder Card */
                <div className={`p-3 rounded-lg border ${isExpired(item.dueDate) ? 'border-red-300 bg-red-50' : isUrgent(item.dueDate) ? 'border-orange-300 bg-orange-50' : 'border-gray-200 bg-white'}`}>
                  <div className="flex items-start gap-3">
                    <div className="mt-0.5">{getIconForType(item.type)}</div>
                    <div className="flex-1 min-w-0">
                      <p className={`font-medium text-sm ${item.isCompleted ? 'line-through text-gray-400' : 'text-gray-900'}`}>
                        {item.title}
                      </p>
                      {item.description && (
                        <p className="text-sm text-gray-500 mt-0.5 truncate">{item.description}</p>
                      )}
                      <div className="flex items-center gap-1 mt-1 text-sm">
                        <Clock size={12} />
                        <span className={isExpired(item.dueDate) ? 'text-red-600 font-medium' : isUrgent(item.dueDate) ? 'text-orange-600 font-medium' : 'text-gray-500'}>
                          {formatDueText(item.dueDate)}
                        </span>
                        <span className="text-xs px-1.5 py-0.5 rounded ml-1 bg-gray-100 text-gray-600">
                          {getTypeLabel(item.type)}
                        </span>
                      </div>
                      {item.source && (
                        <p className="text-xs text-gray-400 mt-1">{item.source}</p>
                      )}
                    </div>
                    <div className="flex gap-1 shrink-0">
                      {!item.isCompleted && (
                        <button
                          onClick={() => handleComplete(item)}
                          className="p-1.5 text-green-600 hover:bg-green-100 rounded transition-colors"
                          title="标记完成"
                        >
                          <Check size={16} />
                        </button>
                      )}
                      <button
                        onClick={() => handleDelete(item)}
                        className="p-1.5 text-red-600 hover:bg-red-100 rounded transition-colors"
                        title="删除"
                      >
                        <Trash2 size={16} />
                      </button>
                    </div>
                  </div>
                </div>
              )}
            </div>
          ))}
        </div>
      )}

      {/* Add Form */}
      <div className="pt-4 border-t border-gray-200">
        <button
          onClick={() => setShowAddForm(!showAddForm)}
          className="flex items-center gap-2 text-sm font-medium text-blue-600 hover:text-blue-700 transition-colors"
        >
          {showAddForm ? <ChevronUp size={16} /> : <ChevronDown size={16} />}
          <Plus size={16} />
          {showAddForm ? '收起添加表单' : '添加新提醒'}
        </button>

        {showAddForm && (
          <div className="mt-3 bg-gray-50 border border-gray-200 rounded-lg p-4 space-y-3">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">提醒标题</label>
              <input
                type="text"
                value={newTitle}
                onChange={e => setNewTitle(e.target.value)}
                placeholder="例如：给豆豆喂药"
                className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
            </div>
            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">类型</label>
                <select
                  value={newType}
                  onChange={e => setNewType(e.target.value as FollowUpItemType)}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 bg-white"
                >
                  <option value="follow_up">复查</option>
                  <option value="symptom_track">症状追踪</option>
                  <option value="medication">用药</option>
                  <option value="general">普通</option>
                </select>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">到期时间</label>
                <input
                  type="datetime-local"
                  value={newDueDate}
                  onChange={e => setNewDueDate(e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
              </div>
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">描述（可选）</label>
              <textarea
                value={newDescription}
                onChange={e => setNewDescription(e.target.value)}
                placeholder="补充说明..."
                rows={2}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 resize-none"
              />
            </div>
            <button
              onClick={handleAddReminder}
              disabled={!newTitle || !newDueDate}
              className="w-full py-2 px-4 bg-blue-600 hover:bg-blue-700 disabled:bg-gray-300 disabled:cursor-not-allowed text-white text-sm font-medium rounded-lg transition-colors"
            >
              添加提醒
            </button>
          </div>
        )}
      </div>
    </div>
  );
}
