import { useEffect, useState } from 'react';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, ReferenceArea } from 'recharts';
import { getIndicatorHistory } from '@/lib/api';
import type { IndicatorHistoryPoint } from '@/types';

interface Props {
  catId: string;
  indicatorName: string;
  displayName: string;
}

export default function IndicatorChart({ catId, indicatorName, displayName }: Props) {
  const [data, setData] = useState<IndicatorHistoryPoint[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!catId || !indicatorName) return;
    setLoading(true);
    getIndicatorHistory(catId, indicatorName, 30)
      .then(setData)
      .finally(() => setLoading(false));
  }, [catId, indicatorName]);

  if (loading) return <div className="h-64 flex items-center justify-center text-gray-400">加载中...</div>;
  if (data.length === 0) return <div className="h-64 flex items-center justify-center text-gray-400">暂无数据</div>;

  const minRef = data[0]?.reference_min;
  const maxRef = data[0]?.reference_max;

  return (
    <div className="h-72">
      <ResponsiveContainer width="100%" height="100%">
        <LineChart data={data}>
          <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
          <XAxis dataKey="date" tick={{ fontSize: 12 }} />
          <YAxis tick={{ fontSize: 12 }} />
          <Tooltip />
          {minRef !== null && maxRef !== null && (
            <ReferenceArea y1={minRef} y2={maxRef} stroke="transparent" fill="#22c55e" fillOpacity={0.05} />
          )}
          <Line type="monotone" dataKey="value" stroke="#8b5cf6" strokeWidth={2} dot={{ r: 3 }} />
        </LineChart>
      </ResponsiveContainer>
      <div className="text-center text-sm text-gray-500 mt-1">{displayName}</div>
    </div>
  );
}
