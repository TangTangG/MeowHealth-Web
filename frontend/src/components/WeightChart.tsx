import { useEffect, useState } from 'react';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';
import { getWeightLogs } from '@/lib/api';

interface WeightChartProps {
  catId: string;
}

export default function WeightChart({ catId }: WeightChartProps) {
  const [data, setData] = useState<{ date: string; weight: number }[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!catId) return;
    setLoading(true);
    getWeightLogs(catId, 30)
      .then(logs => {
        const formatted = logs.map(log => ({
          date: new Date(log.date).toLocaleDateString('zh-CN', { month: 'short', day: 'numeric' }),
          weight: log.value,
        }));
        setData(formatted);
      })
      .finally(() => setLoading(false));
  }, [catId]);

  if (loading) {
    return <div className="h-64 flex items-center justify-center text-gray-400">加载中...</div>;
  }

  if (data.length === 0) {
    return <div className="h-64 flex items-center justify-center text-gray-400">暂无体重数据</div>;
  }

  return (
    <div className="h-64">
      <ResponsiveContainer width="100%" height="100%">
        <LineChart data={data}>
          <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
          <XAxis dataKey="date" tick={{ fontSize: 12 }} />
          <YAxis tick={{ fontSize: 12 }} domain={['dataMin - 0.5', 'dataMax + 0.5']} />
          <Tooltip />
          <Line type="monotone" dataKey="weight" stroke="#3b82f6" strokeWidth={2} dot={{ r: 4 }} />
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
}