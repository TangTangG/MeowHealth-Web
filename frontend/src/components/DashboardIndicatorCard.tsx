import { useEffect, useState } from 'react';
import { Activity, TrendingUp, TrendingDown } from 'lucide-react';
import { getIndicatorNames, getIndicatorHistory } from '@/lib/api';

interface Props {
  catId: string;
}

export default function DashboardIndicatorCard({ catId }: Props) {
  const [latestIndicators, setLatestIndicators] = useState<Array<{
    name: string;
    display_name: string;
    value: number | null;
    unit: string;
    is_abnormal: boolean;
    trend: 'up' | 'down' | 'stable';
  }>>([]);

  useEffect(() => {
    if (!catId) return;
    const load = async () => {
      try {
        const names = await getIndicatorNames(catId);
        const indicators = await Promise.all(
          names.slice(0, 4).map(async (n) => {
            const history = await getIndicatorHistory(catId, n.name, 2);
            if (history.length === 0) return null;
            const latest = history[history.length - 1];
            const prev = history.length > 1 ? history[history.length - 2] : null;
            const trend = prev && latest.value && prev.value
              ? latest.value > prev.value ? 'up' : latest.value < prev.value ? 'down' : 'stable'
              : 'stable';
            return {
              name: n.name,
              display_name: n.display_name,
              value: latest.value,
              unit: latest.unit,
              is_abnormal: latest.is_abnormal,
              trend,
            };
          })
        );
        setLatestIndicators(indicators.filter(Boolean) as any);
      } catch (e) {
        console.error('Failed to load indicator card:', e);
      }
    };
    load();
  }, [catId]);

  if (latestIndicators.length === 0) return null;

  return (
    <div className="bg-white rounded-lg shadow p-4">
      <div className="flex items-center gap-2 text-purple-600 mb-3">
        <Activity size={18} />
        <h3 className="font-semibold text-sm">近期化验指标</h3>
      </div>
      <div className="grid grid-cols-2 gap-3">
        {latestIndicators.map((ind) => (
          <div key={ind.name} className={`p-2 rounded ${ind.is_abnormal ? 'bg-red-50' : 'bg-gray-50'}`}>
            <div className="text-xs text-gray-500">{ind.display_name}</div>
            <div className={`text-lg font-bold ${ind.is_abnormal ? 'text-red-600' : 'text-gray-800'}`}>
              {ind.value !== null ? `${ind.value} ${ind.unit}` : '—'}
            </div>
            {ind.trend === 'up' && <TrendingUp size={14} className="text-red-500 inline" />}
            {ind.trend === 'down' && <TrendingDown size={14} className="text-green-500 inline" />}
          </div>
        ))}
      </div>
    </div>
  );
}
