import type { HealthRecord, WeightLog, Reminder } from '@/types';
import { Activity, Syringe, Pill, AlertCircle, Scale, Calendar } from 'lucide-react';

interface TimelineProps {
  records: HealthRecord[];
  weightLogs?: WeightLog[];
  reminders?: Reminder[];
}

const typeIcons: Record<string, React.ComponentType<{ size?: number }>> = {
  weight: Scale,
  vaccine: Syringe,
  deworm: Pill,
  symptom: AlertCircle,
  checkup: Activity,
  reminder: Calendar,
  other: Activity,
};

const typeColors: Record<string, string> = {
  weight: 'bg-blue-100 text-blue-600',
  vaccine: 'bg-green-100 text-green-600',
  deworm: 'bg-purple-100 text-purple-600',
  symptom: 'bg-red-100 text-red-600',
  checkup: 'bg-yellow-100 text-yellow-600',
  reminder: 'bg-orange-100 text-orange-600',
  other: 'bg-gray-100 text-gray-600',
};

export default function Timeline({ records, weightLogs = [], reminders = [] }: TimelineProps) {
  const allEvents = [
    ...records.map(r => ({ ...r, eventType: r.type, date: r.date })),
    ...weightLogs.map(w => ({ ...w, eventType: 'weight', title: `体重: ${w.value}kg`, date: w.date })),
    ...reminders.filter(r => r.is_completed).map(r => ({ ...r, eventType: 'reminder', date: r.completed_at || r.due_date })),
  ].sort((a, b) => new Date(b.date).getTime() - new Date(a.date).getTime());

  return (
    <div className="space-y-3">
      {allEvents.slice(0, 10).map((event, index) => {
        const Icon = typeIcons[event.eventType] || typeIcons.other;
        const colorClass = typeColors[event.eventType] || typeColors.other;
        
        return (
          <div key={`${event.id}-${index}`} className="flex gap-3 items-start">
            <div className={`p-2 rounded-full ${colorClass}`}>
              <Icon size={16} />
            </div>
            <div className="flex-1 min-w-0">
              <div className="flex justify-between items-start">
                <span className="font-medium text-sm truncate">{event.title}</span>
                <span className="text-xs text-gray-400 whitespace-nowrap ml-2">
                  {new Date(event.date).toLocaleDateString('zh-CN')}
                </span>
              </div>
              {event.note && (
                <p className="text-sm text-gray-600 mt-1 line-clamp-2">{event.note}</p>
              )}
            </div>
          </div>
        );
      })}
      
      {allEvents.length === 0 && (
        <div className="text-center text-gray-400 py-8">暂无健康记录</div>
      )}
    </div>
  );
}