import React, { useState } from 'react';
import { ChevronDown, ChevronUp, AlertCircle, TrendingUp, TrendingDown } from 'lucide-react';

interface Indicator {
  id: string;
  name: string;
  display_name: string;
  value: number | null;
  unit: string;
  reference_min: number | null;
  reference_max: number | null;
  is_abnormal: boolean;
  explanation: string | null;
}

interface ReportCardProps {
  title: string;
  date: string;
  summary: string;
  indicators: Indicator[];
  recommendations: string[];
}

const IndicatorCard: React.FC<{ indicator: Indicator }> = ({ indicator }) => {
  const isHigh = indicator.value && indicator.reference_max && indicator.value > indicator.reference_max;
  const isLow = indicator.value && indicator.reference_min && indicator.value < indicator.reference_min;
  
  const getStatusColor = () => {
    if (!indicator.is_abnormal) return 'bg-green-50 border-green-200';
    if (isHigh) return 'bg-red-50 border-red-200';
    if (isLow) return 'bg-yellow-50 border-yellow-200';
    return 'bg-gray-50 border-gray-200';
  };
  
  const getStatusIcon = () => {
    if (!indicator.is_abnormal) return null;
    if (isHigh) return <TrendingUp className="w-4 h-4 text-red-500" />;
    if (isLow) return <TrendingDown className="w-4 h-4 text-yellow-500" />;
    return <AlertCircle className="w-4 h-4 text-orange-500" />;
  };

  return (
    <div className={`p-4 rounded-lg border ${getStatusColor()} transition-all`}>
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <span className="font-medium text-gray-900">{indicator.display_name}</span>
          <span className="text-xs text-gray-500">({indicator.name})</span>
          {getStatusIcon()}
        </div>
        <div className="text-right">
          <span className={`text-lg font-bold ${indicator.is_abnormal ? 'text-red-600' : 'text-gray-900'}`}>
            {indicator.value !== null ? indicator.value.toFixed(2) : '-'}
          </span>
          <span className="text-sm text-gray-500 ml-1">{indicator.unit}</span>
        </div>
      </div>
      
      <div className="mt-2 text-sm text-gray-600">
        参考范围: {indicator.reference_min !== null ? indicator.reference_min : '-'} - 
        {indicator.reference_max !== null ? indicator.reference_max : '-'} {indicator.unit}
      </div>
      
      {indicator.explanation && (
        <p className="mt-2 text-sm text-gray-600">{indicator.explanation}</p>
      )}
    </div>
  );
};

const IndicatorCategory: React.FC<{ title: string; indicators: Indicator[] }> = ({ title, indicators }) => {
  const [isExpanded, setIsExpanded] = useState(() => 
    indicators.some(i => i.is_abnormal)
  );
  
  const abnormalCount = indicators.filter(i => i.is_abnormal).length;
  
  return (
    <div className="border rounded-lg overflow-hidden">
      <button
        onClick={() => setIsExpanded(!isExpanded)}
        className="w-full flex items-center justify-between p-4 bg-gray-50 hover:bg-gray-100 transition-colors"
      >
        <div className="flex items-center gap-2">
          <span className="font-semibold text-gray-900">{title}</span>
          {abnormalCount > 0 && (
            <span className="px-2 py-0.5 bg-red-100 text-red-700 text-xs rounded-full">
              {abnormalCount} 项异常
            </span>
          )}
        </div>
        {isExpanded ? <ChevronUp className="w-5 h-5 text-gray-500" /> : <ChevronDown className="w-5 h-5 text-gray-500" />}
      </button>
      
      {isExpanded && (
        <div className="p-4 space-y-3">
          {indicators.map(indicator => (
            <IndicatorCard key={indicator.id} indicator={indicator} />
          ))}
        </div>
      )}
    </div>
  );
};

export const ReportCard: React.FC<ReportCardProps> = ({ 
  title, 
  date, 
  summary, 
  indicators, 
  recommendations 
}) => {
  // 按系统分类指标
  const categories = {
    '血液系统': indicators.filter(i => ['WBC', 'RBC', 'HGB', 'PLT', 'HCT'].includes(i.name)),
    '肝脏功能': indicators.filter(i => ['ALT', 'AST', 'ALP', 'TBIL', 'ALB'].includes(i.name)),
    '肾脏功能': indicators.filter(i => ['CREA', 'BUN', 'PHOS', 'SDMA'].includes(i.name)),
    '其他指标': indicators.filter(i => 
      !['WBC', 'RBC', 'HGB', 'PLT', 'HCT', 'ALT', 'AST', 'ALP', 'TBIL', 'ALB', 'CREA', 'BUN', 'PHOS', 'SDMA'].includes(i.name)
    )
  };

  return (
    <div className="bg-white rounded-xl shadow-sm border p-6 space-y-6">
      {/* 顶部概览 */}
      <div className="border-b pb-4">
        <h2 className="text-xl font-bold text-gray-900">{title}</h2>
        <p className="text-sm text-gray-500 mt-1">{new Date(date).toLocaleDateString('zh-CN')}</p>
        
        <div className="mt-4 p-4 bg-blue-50 rounded-lg">
          <p className="text-blue-900 font-medium">{summary}</p>
        </div>
      </div>

      {/* 指标分类展示 */}
      <div className="space-y-4">
        <h3 className="font-semibold text-gray-900">检测指标</h3>
        {Object.entries(categories).map(([categoryName, categoryIndicators]) => 
          categoryIndicators.length > 0 ? (
            <IndicatorCategory 
              key={categoryName}
              title={categoryName}
              indicators={categoryIndicators}
            />
          ) : null
        )}
      </div>

      {/* 建议 */}
      {recommendations && recommendations.length > 0 && (
        <div className="border-t pt-4">
          <h3 className="font-semibold text-gray-900 mb-3">AI 建议</h3>
          <ul className="space-y-2">
            {recommendations.map((rec, index) => (
              <li key={index} className="flex items-start gap-2">
                <span className="flex-shrink-0 w-6 h-6 bg-blue-100 text-blue-700 rounded-full flex items-center justify-center text-sm font-medium">
                  {index + 1}
                </span>
                <span className="text-gray-700">{rec}</span>
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
};