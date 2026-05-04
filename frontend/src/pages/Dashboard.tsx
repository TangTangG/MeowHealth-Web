import { useState, useEffect } from 'react';
import { useOutletContext } from 'react-router-dom';
import { Plus, Activity, Scale, Calendar } from 'lucide-react';
import WeightChart from '@/components/WeightChart';
import DashboardIndicatorCard from '@/components/DashboardIndicatorCard';
import Timeline from '@/components/Timeline';
import TodoCard from '@/components/TodoCard';
import { getHealthRecords, getWeightLogs, getReminders, createReminder } from '@/lib/api';
import type { HealthRecord, WeightLog, Reminder } from '@/types';

interface OutletContext {
  selectedCatId: string | null;
}

export default function Dashboard() {
  const { selectedCatId } = useOutletContext<OutletContext>();
  const [records, setRecords] = useState<HealthRecord[]>([]);
  const [weightLogs, setWeightLogs] = useState<WeightLog[]>([]);
  const [reminders, setReminders] = useState<Reminder[]>([]);
  const [loading, setLoading] = useState(false);
  const [showAddReminder, setShowAddReminder] = useState(false);
  const [newReminder, setNewReminder] = useState({
    title: '',
    description: '',
    due_date: '',
    reminder_type: 'other',
  });

  const loadData = async () => {
    if (!selectedCatId) return;
    setLoading(true);
    try {
      const [recordsData, logsData, remindersData] = await Promise.all([
        getHealthRecords(selectedCatId),
        getWeightLogs(selectedCatId, 10),
        getReminders(selectedCatId, false),
      ]);
      setRecords(recordsData);
      setWeightLogs(logsData);
      setReminders(remindersData);
    } catch (error) {
      console.error('Failed to load dashboard data:', error);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, [selectedCatId]);

  const handleAddReminder = async () => {
    if (!selectedCatId || !newReminder.title || !newReminder.due_date) return;
    try {
      await createReminder(selectedCatId, {
        ...newReminder,
        due_date: new Date(newReminder.due_date).toISOString(),
      });
      setShowAddReminder(false);
      setNewReminder({ title: '', description: '', due_date: '', reminder_type: 'other' });
      loadData();
    } catch (error) {
      console.error('Failed to add reminder:', error);
    }
  };

  if (!selectedCatId) {
    return (
      <div className="flex items-center justify-center h-96">
        <div className="text-center">
          <p className="text-gray-500 mb-4">请先在侧边栏选择一只猫咪</p>
          <a href="/cats" className="text-blue-600 hover:underline">去添加猫咪 →</a>
        </div>
      </div>
    );
  }

  if (loading) {
    return <div className="flex items-center justify-center h-96 text-gray-400">加载中...</div>;
  }

  return (
    <div>
      {/* Header */}
      <div className="mb-6">
        <h2 className="text-2xl font-bold text-gray-800">Dashboard</h2>
        <p className="text-gray-500">猫咪健康概览</p>
      </div>

      {/* Stats Cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
        <div className="bg-white rounded-lg p-4 shadow-sm border">
          <div className="flex items-center gap-3">
            <div className="p-2 bg-blue-100 rounded-lg">
              <Scale className="text-blue-600" size={20} />
            </div>
            <div>
              <p className="text-sm text-gray-500">最新体重</p>
              <p className="text-lg font-semibold">
                {weightLogs[0]?.value ? `${weightLogs[0].value} kg` : '暂无数据'}
              </p>
            </div>
          </div>
        </div>
        
        <div className="bg-white rounded-lg p-4 shadow-sm border">
          <div className="flex items-center gap-3">
            <div className="p-2 bg-orange-100 rounded-lg">
              <Calendar className="text-orange-600" size={20} />
            </div>
            <div>
              <p className="text-sm text-gray-500">待办提醒</p>
              <p className="text-lg font-semibold">{reminders.length} 个</p>
            </div>
          </div>
        </div>
        
        <div className="bg-white rounded-lg p-4 shadow-sm border">
          <div className="flex items-center gap-3">
            <div className="p-2 bg-green-100 rounded-lg">
              <Activity className="text-green-600" size={20} />
            </div>
            <div>
              <p className="text-sm text-gray-500">健康记录</p>
              <p className="text-lg font-semibold">{records.length} 条</p>
            </div>
          </div>
        </div>
      </div>

      {/* Main Content Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Left Column */}
        <div className="space-y-6">
          {/* Weight Chart */}
          <div className="bg-white rounded-lg p-4 shadow-sm border">
            <h3 className="font-semibold text-gray-800 mb-4">体重趋势</h3>
            <WeightChart catId={selectedCatId} />
          </div>

          {/* Indicator Card */}
          <DashboardIndicatorCard catId={selectedCatId} />

          {/* Recent Timeline */}
          <div className="bg-white rounded-lg p-4 shadow-sm border">
            <h3 className="font-semibold text-gray-800 mb-4">近期动态</h3>
            <Timeline records={records.slice(0, 5)} weightLogs={weightLogs.slice(0, 3)} />
          </div>
        </div>

        {/* Right Column */}
        <div className="space-y-6">
          {/* Reminders */}
          <div className="bg-white rounded-lg p-4 shadow-sm border">
            <div className="flex justify-between items-center mb-4">
              <h3 className="font-semibold text-gray-800">待办提醒</h3>
              <button
                onClick={() => setShowAddReminder(true)}
                className="p-1.5 text-blue-600 hover:bg-blue-50 rounded transition-colors"
              >
                <Plus size={18} />
              </button>
            </div>

            {showAddReminder && (
              <div className="mb-4 p-3 bg-gray-50 rounded-lg space-y-2">
                <input
                  type="text"
                  placeholder="提醒标题"
                  value={newReminder.title}
                  onChange={(e) => setNewReminder({ ...newReminder, title: e.target.value })}
                  className="w-full px-3 py-2 border rounded text-sm"
                />
                <input
                  type="text"
                  placeholder="描述（可选）"
                  value={newReminder.description}
                  onChange={(e) => setNewReminder({ ...newReminder, description: e.target.value })}
                  className="w-full px-3 py-2 border rounded text-sm"
                />
                <input
                  type="datetime-local"
                  value={newReminder.due_date}
                  onChange={(e) => setNewReminder({ ...newReminder, due_date: e.target.value })}
                  className="w-full px-3 py-2 border rounded text-sm"
                />
                <div className="flex gap-2">
                  <button
                    onClick={handleAddReminder}
                    className="px-3 py-1.5 bg-blue-600 text-white rounded text-sm hover:bg-blue-700"
                  >
                    添加
                  </button>
                  <button
                    onClick={() => setShowAddReminder(false)}
                    className="px-3 py-1.5 text-gray-600 hover:bg-gray-200 rounded text-sm"
                  >
                    取消
                  </button>
                </div>
              </div>
            )}

            <div className="space-y-3">
              {reminders.map(reminder => (
                <TodoCard key={reminder.id} reminder={reminder} onUpdate={loadData} />
              ))}
              {reminders.length === 0 && (
                <div className="text-center text-gray-400 py-8">暂无待办提醒</div>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}