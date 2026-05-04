import { useState, useEffect } from 'react';
import { useOutletContext } from 'react-router-dom';
import { BarChart3, Activity, TrendingUp } from 'lucide-react';
import WeightChart from '@/components/WeightChart';
import IndicatorChart from '@/components/IndicatorChart';
import HealthScoreChart from '@/components/HealthScoreChart';
import { getIndicatorNames } from '@/lib/api';
import type { IndicatorNameItem } from '@/types';

interface OutletContext {
  selectedCatId: string | null;
}

export default function Analytics() {
  const { selectedCatId } = useOutletContext<OutletContext>();
  const [indicatorNames, setIndicatorNames] = useState<IndicatorNameItem[]>([]);
  const [selectedIndicator, setSelectedIndicator] = useState<string>('');

  useEffect(() => {
    if (!selectedCatId) return;
    getIndicatorNames(selectedCatId).then((names) => {
      setIndicatorNames(names);
      if (names.length > 0) setSelectedIndicator(names[0].name);
    });
  }, [selectedCatId]);

  if (!selectedCatId) {
    return <div className="p-8 text-center text-gray-400">请先选择一只猫咪</div>;
  }

  const selectedDisplayName = indicatorNames.find((n) => n.name === selectedIndicator)?.display_name || '';

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold text-gray-800">数据洞察</h1>

      {/* 体重趋势 */}
      <div className="bg-white rounded-lg shadow p-4">
        <div className="flex items-center gap-2 text-blue-600 mb-3">
          <TrendingUp size={18} />
          <h2 className="font-semibold">体重趋势 (90天)</h2>
        </div>
        <WeightChart catId={selectedCatId} />
      </div>

      {/* 健康评分趋势 */}
      <div className="bg-white rounded-lg shadow p-4">
        <div className="flex items-center gap-2 text-green-600 mb-3">
          <Activity size={18} />
          <h2 className="font-semibold">健康评分趋势 (180天)</h2>
        </div>
        <HealthScoreChart catId={selectedCatId} />
      </div>

      {/* 化验指标对比 */}
      <div className="bg-white rounded-lg shadow p-4">
        <div className="flex items-center justify-between mb-3">
          <div className="flex items-center gap-2 text-purple-600">
            <BarChart3 size={18} />
            <h2 className="font-semibold">化验指标历史对比</h2>
          </div>
          <select
            value={selectedIndicator}
            onChange={(e) => setSelectedIndicator(e.target.value)}
            className="border border-gray-200 rounded-lg px-3 py-1 text-sm"
          >
            {indicatorNames.map((n) => (
              <option key={n.name} value={n.name}>{n.display_name}</option>
            ))}
          </select>
        </div>
        {selectedIndicator && (
          <IndicatorChart
            catId={selectedCatId}
            indicatorName={selectedIndicator}
            displayName={selectedDisplayName}
          />
        )}
      </div>
    </div>
  );
}
