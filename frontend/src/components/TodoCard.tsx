import { useState } from 'react';
import { Check, Trash2, Clock } from 'lucide-react';
import { completeReminder, deleteReminder } from '@/lib/api';
import type { Reminder } from '@/types';

interface TodoCardProps {
  reminder: Reminder;
  onUpdate: () => void;
}

export default function TodoCard({ reminder, onUpdate }: TodoCardProps) {
  const [isCompleted, setIsCompleted] = useState(reminder.is_completed);

  const handleComplete = async () => {
    await completeReminder(reminder.id);
    setIsCompleted(true);
    onUpdate();
  };

  const handleDelete = async () => {
    if (!confirm('确定要删除这个提醒吗？')) return;
    await deleteReminder(reminder.id);
    onUpdate();
  };

  const daysUntil = Math.ceil((new Date(reminder.due_date).getTime() - Date.now()) / (1000 * 60 * 60 * 24));
  const isUrgent = daysUntil <= 3 && !isCompleted;

  return (
    <div className={`p-3 rounded-lg border ${isUrgent ? 'border-orange-300 bg-orange-50' : 'border-gray-200 bg-white'}`}>
      <div className="flex justify-between items-start">
        <div className="flex-1">
          <p className={`font-medium text-sm ${isCompleted ? 'line-through text-gray-400' : ''}`}>
            {reminder.title}
          </p>
          <div className="flex items-center gap-1 mt-1 text-sm text-gray-500">
            <Clock size={12} />
            <span className={isUrgent ? 'text-orange-600 font-medium' : ''}>
              {daysUntil <= 0 ? '今天到期' : `${daysUntil}天后到期`}
            </span>
          </div>
        </div>
        <div className="flex gap-1">
          {!isCompleted && (
            <button
              onClick={handleComplete}
              className="p-1.5 text-green-600 hover:bg-green-100 rounded"
            >
              <Check size={16} />
            </button>
          )}
          <button
            onClick={handleDelete}
            className="p-1.5 text-red-600 hover:bg-red-100 rounded"
          >
            <Trash2 size={16} />
          </button>
        </div>
      </div>
    </div>
  );
}