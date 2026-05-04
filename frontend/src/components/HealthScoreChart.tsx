import { useEffect, useState } from 'react';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, ReferenceLine } from 'recharts';
import { getHealthScoreHistory } from '@/lib/api';
import type { HealthScorePoint } from '@/types';

interface Props {
  catId: string;
}

export default function HealthScoreChart({ catId }: Props) {
  const [data, setData] = useState<HealthScorePoint[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!catId) return;
    setLoading(true);
    getHealthScoreHistory(catId, 180)
      .then((res) => setData(res.data))
      .finally(() => setLoading(false));
  }, [catId]);

  if (loading) return <div className="h-64 flex items-center justify-center text-gray-400">加载中...</div>;
  if (data.length === 0) return <div className="h-64 flex items-center justify-center text-gray-400">暂无评分数据</div>;

  return (
    <div className="h-72">
      <ResponsiveContainer width="100%" height="100%">
        <LineChart data={data}>
          <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
          <XAxis dataKey="date" tick={{ fontSize: 12 }} />
          <YAxis tick={{ fontSize: 12 }} domain={[40, 100]} />
          <Tooltip formatter={(value: number) => [`${value} 分`, '健康评分']} />
          <ReferenceLine y={80} stroke="#22c55e" strokeDasharray="3 3" label="优秀" />
          <ReferenceLine y={60} stroke="#eab308" strokeDasharray="3 3" label="良好" />
          <Line type="monotone" dataKey="score" stroke="#3b82f6" strokeWidth={2} dot={{ r: 3 }} />
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
}
