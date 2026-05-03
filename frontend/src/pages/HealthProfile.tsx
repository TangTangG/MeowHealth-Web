import { useState, useEffect, useMemo } from 'react';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Legend } from 'recharts';
import {
  Heart, Thermometer, Activity, FileText, Stethoscope, Star, ChevronDown, ChevronUp,
  AlertTriangle, CheckCircle, Clock, Scale, TrendingUp, AlertCircle, Plus
} from 'lucide-react';
import type { Cat, HealthRecordWithDetails, SymptomLog, VitalSign, HealthIndicator } from '@/types';
import { getCat, getCatHealthRecords } from '@/lib/api';
import { CatSelector } from '@/components/CatSelector';

const TABS = [
  { key: 'records', label: '🏥 就诊记录', icon: FileText },
  { key: 'symptoms', label: '📝 症状日志', icon: Stethoscope },
  { key: 'vitals', label: '📊 体征趋势', icon: TrendingUp },
  { key: 'indicators', label: '🔬 化验指标', icon: Activity },
  { key: 'score', label: '📈 健康评分', icon: Star },
];

function calculateAge(birthday: string): string {
  const birth = new Date(birthday);
  const now = new Date();
  let years = now.getFullYear() - birth.getFullYear();
  let months = now.getMonth() - birth.getMonth();
  if (months < 0) {
    years--;
    months += 12;
  }
  if (years < 0) return '未知';
  if (years === 0) return `${months}个月`;
  return `${years}岁${months > 0 ? `${months}个月` : ''}`;
}

function formatDate(dateStr: string): string {
  return new Date(dateStr).toLocaleDateString('zh-CN');
}

function formatDateTime(dateStr: string): string {
  return new Date(dateStr).toLocaleString('zh-CN', {
    month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit'
  });
}

function getSeverityColor(severity: number): string {
  if (severity <= 2) return 'text-green-600 bg-green-50 border-green-200';
  if (severity === 3) return 'text-yellow-600 bg-yellow-50 border-yellow-200';
  return 'text-red-600 bg-red-50 border-red-200';
}

function getSeverityStars(severity: number): string {
  return '★'.repeat(severity) + '☆'.repeat(5 - severity);
}

function getTriageColor(level?: string): string {
  switch (level) {
    case 'emergency': return 'bg-red-100 text-red-700 border-red-200';
    case 'urgent': return 'bg-orange-100 text-orange-700 border-orange-200';
    case 'routine': return 'bg-green-100 text-green-700 border-green-200';
    default: return 'bg-gray-100 text-gray-700 border-gray-200';
  }
}

function getTriageLabel(level?: string): string {
  switch (level) {
    case 'emergency': return '急诊';
    case 'urgent': return '加急';
    case 'routine': return '常规';
    default: return '未分诊';
  }
}

function getStatusColor(status: string): string {
  switch (status) {
    case 'resolved': return 'text-green-600';
    case 'in_progress': return 'text-blue-600';
    case 'pending': return 'text-yellow-600';
    default: return 'text-gray-500';
  }
}

function getStatusLabel(status: string): string {
  switch (status) {
    case 'resolved': return '已解决';
    case 'in_progress': return '进行中';
    case 'pending': return '待处理';
    default: return status;
  }
}

function getScoreColor(score: number): string {
  if (score >= 80) return 'text-green-500';
  if (score >= 60) return 'text-yellow-500';
  return 'text-red-500';
}

function getScoreBgColor(score: number): string {
  if (score >= 80) return 'bg-green-500';
  if (score >= 60) return 'bg-yellow-500';
  return 'bg-red-500';
}

function getIndicatorStatus(indicator: HealthIndicator): { label: string; color: string } {
  if (indicator.is_abnormal) return { label: '异常', color: 'text-red-600 bg-red-50' };
  if (indicator.value === undefined || indicator.value === null) return { label: '无数据', color: 'text-gray-400' };
  return { label: '正常', color: 'text-green-600 bg-green-50' };
}

// ==================== 子组件 ====================

function TimelineItem({ record }: { record: HealthRecordWithDetails }) {
  const [expanded, setExpanded] = useState(false);

  return (
    <div className="relative pl-8 pb-6 border-l-2 border-gray-200 last:border-l-0 last:pb-0">
      <div className="absolute left-[-9px] top-0 w-4 h-4 rounded-full bg-blue-500 border-2 border-white shadow-sm" />
      <div className="bg-white rounded-lg border border-gray-200 p-4 shadow-sm">
        <div className="flex items-center justify-between mb-2">
          <div className="flex items-center gap-3">
            <span className="text-sm text-gray-500">{formatDate(record.date)}</span>
            <span className="font-medium text-gray-800">{record.title}</span>
          </div>
          <div className="flex items-center gap-2">
            <span className={`px-2 py-0.5 rounded text-xs border ${getTriageColor(record.triage_level)}`}>
              {getTriageLabel(record.triage_level)}
            </span>
            <span className={`text-xs font-medium ${getStatusColor(record.treatment_status)}`}>
              {getStatusLabel(record.treatment_status)}
            </span>
          </div>
        </div>
        {record.ai_summary && (
          <p className="text-sm text-gray-600 mb-2 line-clamp-2">{record.ai_summary}</p>
        )}
        <button
          onClick={() => setExpanded(!expanded)}
          className="flex items-center gap-1 text-sm text-blue-600 hover:text-blue-700 transition-colors"
        >
          {expanded ? <ChevronUp size={16} /> : <ChevronDown size={16} />}
          {expanded ? '收起' : '展开详情'}
        </button>
        {expanded && (
          <div className="mt-3 pt-3 border-t border-gray-100 space-y-3">
            {record.symptom_logs.length > 0 && (
              <div>
                <h4 className="text-sm font-medium text-gray-700 mb-1">症状</h4>
                <div className="flex flex-wrap gap-2">
                  {record.symptom_logs.map(s => (
                    <span key={s.id} className={`px-2 py-1 rounded text-xs border ${getSeverityColor(s.severity)}`}>
                      {s.symptom_description} ({getSeverityStars(s.severity)})
                    </span>
                  ))}
                </div>
              </div>
            )}
            {record.vital_signs.length > 0 && (
              <div>
                <h4 className="text-sm font-medium text-gray-700 mb-1">体征</h4>
                <div className="flex flex-wrap gap-3 text-sm text-gray-600">
                  {record.vital_signs.map(v => (
                    <span key={v.id}>
                      {v.weight_kg && <span className="mr-3">体重: {v.weight_kg}kg</span>}
                      {v.temperature_celsius && <span className="mr-3">体温: {v.temperature_celsius}°C</span>}
                      {v.heart_rate && <span className="mr-3">心率: {v.heart_rate}bpm</span>}
                      {v.respiratory_rate && <span>呼吸: {v.respiratory_rate}次/分</span>}
                    </span>
                  ))}
                </div>
              </div>
            )}
            {record.note && (
              <div>
                <h4 className="text-sm font-medium text-gray-700 mb-1">备注</h4>
                <p className="text-sm text-gray-600">{record.note}</p>
              </div>
            )}
            {record.ai_summary && (
              <div className="bg-blue-50 rounded-lg p-3">
                <h4 className="text-sm font-medium text-blue-800 mb-1">🤖 AI 总结</h4>
                <p className="text-sm text-blue-700">{record.ai_summary}</p>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}

function EmptyState({ message, icon: Icon }: { message: string; icon: any }) {
  return (
    <div className="flex flex-col items-center justify-center py-16 text-gray-400">
      <Icon size={48} strokeWidth={1.2} className="mb-3" />
      <p className="text-sm">{message}</p>
    </div>
  );
}

function LoadingSpinner() {
  return (
    <div className="flex items-center justify-center py-16">
      <div className="w-8 h-8 border-2 border-blue-500 border-t-transparent rounded-full animate-spin" />
    </div>
  );
}

// ==================== 主页面 ====================

export default function HealthProfile() {
  const [selectedCatId, setSelectedCatId] = useState<string | null>(null);
  const [records, setRecords] = useState<HealthRecordWithDetails[]>([]);
  const [cat, setCat] = useState<Cat | null>(null);
  const [activeTab, setActiveTab] = useState('records');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!selectedCatId) return;
    setLoading(true);
    setError(null);
    Promise.all([
      getCat(selectedCatId),
      getCatHealthRecords(selectedCatId)
    ])
      .then(([catData, recordsData]) => {
        setCat(catData);
        setRecords(recordsData);
      })
      .catch(err => {
        setError('加载数据失败，请稍后重试');
        console.error(err);
      })
      .finally(() => setLoading(false));
  }, [selectedCatId]);

  // 从所有记录中提取体征数据
  const allVitalSigns = useMemo(() => {
    const signs: (VitalSign & { recordDate: string })[] = [];
    records.forEach(r => {
      r.vital_signs.forEach(v => {
        signs.push({ ...v, recordDate: r.date });
      });
    });
    return signs.sort((a, b) => new Date(a.measured_at).getTime() - new Date(b.measured_at).getTime());
  }, [records]);

  // 从所有记录中提取症状
  const allSymptoms = useMemo(() => {
    const symptoms: (SymptomLog & { recordDate: string })[] = [];
    records.forEach(r => {
      r.symptom_logs.forEach(s => {
        symptoms.push({ ...s, recordDate: r.date });
      });
    });
    return symptoms.sort((a, b) => new Date(b.onset_time).getTime() - new Date(a.onset_time).getTime());
  }, [records]);

  // 从所有记录中提取化验指标
  const allIndicators = useMemo(() => {
    const indicators: (HealthIndicator & { recordDate: string })[] = [];
    records.forEach(r => {
      r.indicators.forEach(i => {
        indicators.push({ ...i, recordDate: r.date });
      });
    });
    return indicators;
  }, [records]);

  // 计算健康评分
  const healthScore = useMemo(() => {
    if (!cat || records.length === 0) return null;

    let score = 80;

    // 体重加分
    const latestWeight = allVitalSigns.length > 0 ? allVitalSigns[allVitalSigns.length - 1].weight_kg : null;
    if (latestWeight && latestWeight >= 3 && latestWeight <= 6) score += 5;

    // 化验指标正常率
    if (allIndicators.length > 0) {
      const normalRate = allIndicators.filter(i => !i.is_abnormal).length / allIndicators.length;
      if (normalRate > 0.8) score += 5;
    }

    // 近期症状检查（30天内）
    const thirtyDaysAgo = new Date();
    thirtyDaysAgo.setDate(thirtyDaysAgo.getDate() - 30);
    const recentSymptoms = allSymptoms.filter(s => new Date(s.onset_time) >= thirtyDaysAgo);
    if (recentSymptoms.length === 0) score += 5;

    // 诊疗完成度
    const unresolvedRecords = records.filter(r => r.treatment_status !== 'resolved');
    if (unresolvedRecords.length === 0 && records.length > 0) score += 5;

    return Math.max(40, Math.min(100, score));
  }, [cat, records, allVitalSigns, allIndicators, allSymptoms]);

  // 评分维度
  const scoreDimensions = useMemo(() => {
    const dims = [];

    // 体重稳定性
    const weights = allVitalSigns.map(v => v.weight_kg).filter(Boolean);
    let weightScore = 50;
    if (weights.length >= 2) {
      const maxW = Math.max(...weights);
      const minW = Math.min(...weights);
      const range = maxW - minW;
      if (range <= 0.2) weightScore = 100;
      else if (range <= 0.5) weightScore = 80;
      else if (range <= 1) weightScore = 60;
      else weightScore = 40;
    } else if (weights.length === 1) {
      weightScore = 70;
    }
    dims.push({ label: '体重稳定性', score: weightScore });

    // 化验正常率
    let indicatorScore = 50;
    if (allIndicators.length > 0) {
      const normalRate = allIndicators.filter(i => !i.is_abnormal).length / allIndicators.length;
      indicatorScore = Math.round(normalRate * 100);
    }
    dims.push({ label: '化验指标正常率', score: indicatorScore });

    // 症状活跃度
    const thirtyDaysAgo = new Date();
    thirtyDaysAgo.setDate(thirtyDaysAgo.getDate() - 30);
    const recentSymptoms = allSymptoms.filter(s => new Date(s.onset_time) >= thirtyDaysAgo);
    let symptomScore = recentSymptoms.length === 0 ? 100 : recentSymptoms.length <= 2 ? 70 : 40;
    dims.push({ label: '症状活跃度', score: symptomScore });

    // 诊疗完成度
    let treatmentScore = records.length === 0 ? 50 : 100;
    if (records.length > 0) {
      const resolvedRate = records.filter(r => r.treatment_status === 'resolved').length / records.length;
      treatmentScore = Math.round(resolvedRate * 100);
    }
    dims.push({ label: '诊疗完成度', score: treatmentScore });

    return dims;
  }, [allVitalSigns, allIndicators, allSymptoms, records]);

  // 图表数据
  const chartData = useMemo(() => {
    return allVitalSigns.map(v => ({
      date: formatDate(v.measured_at),
      weight: v.weight_kg,
      temperature: v.temperature_celsius,
      heartRate: v.heart_rate,
      respiratoryRate: v.respiratory_rate,
    }));
  }, [allVitalSigns]);

  const latestWeight = allVitalSigns.length > 0 ? allVitalSigns[allVitalSigns.length - 1].weight_kg : null;

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="max-w-6xl mx-auto px-4 py-6">
        {/* 猫咪选择器 */}
        <div className="mb-6">
          <CatSelector selectedId={selectedCatId} onSelect={setSelectedCatId} />
        </div>

        {!selectedCatId && (
          <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-12 text-center">
            <Heart size={48} className="mx-auto text-gray-300 mb-4" />
            <h2 className="text-lg font-medium text-gray-600 mb-2">请先选择一只猫咪</h2>
            <p className="text-sm text-gray-400">选择猫咪后查看健康档案</p>
          </div>
        )}

        {selectedCatId && loading && <LoadingSpinner />}

        {selectedCatId && error && (
          <div className="bg-red-50 rounded-xl border border-red-200 p-8 text-center">
            <AlertCircle size={40} className="mx-auto text-red-400 mb-3" />
            <p className="text-red-600">{error}</p>
          </div>
        )}

        {selectedCatId && !loading && !error && cat && (
          <>
            {/* 顶部信息卡片 */}
            <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6 mb-6">
              <div className="flex items-center gap-6">
                <div className="w-20 h-20 rounded-full bg-gradient-to-br from-blue-100 to-purple-100 flex items-center justify-center text-3xl shadow-inner">
                  🐱
                </div>
                <div className="flex-1">
                  <div className="flex items-center gap-3 mb-1">
                    <h1 className="text-xl font-bold text-gray-800">{cat.name}</h1>
                    <span className="text-sm text-gray-500">{cat.breed}</span>
                    <span className="text-sm text-gray-400">{calculateAge(cat.birthday)}</span>
                  </div>
                  <div className="flex items-center gap-4 text-sm text-gray-500">
                    <span className="flex items-center gap-1">
                      <Scale size={14} />
                      当前体重: <strong className="text-gray-700">{latestWeight ? `${latestWeight} kg` : '暂无数据'}</strong>
                    </span>
                    {healthScore !== null && (
                      <span className="flex items-center gap-1">
                        <Heart size={14} className={getScoreColor(healthScore)} />
                        健康评分:
                        <strong className={getScoreColor(healthScore)}>{healthScore} 分</strong>
                      </span>
                    )}
                  </div>
                </div>
              </div>
            </div>

            {/* Tab 导航 */}
            <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-2 mb-6">
              <div className="flex flex-wrap gap-1">
                {TABS.map(tab => {
                  const Icon = tab.icon;
                  const active = activeTab === tab.key;
                  return (
                    <button
                      key={tab.key}
                      onClick={() => setActiveTab(tab.key)}
                      className={`flex items-center gap-2 px-4 py-2.5 rounded-lg text-sm font-medium transition-all ${
                        active
                          ? 'bg-blue-50 text-blue-700 shadow-sm'
                          : 'text-gray-600 hover:bg-gray-50 hover:text-gray-800'
                      }`}
                    >
                      <Icon size={16} />
                      {tab.label}
                    </button>
                  );
                })}
              </div>
            </div>

            {/* Tab 内容区 */}
            <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6 min-h-[300px]">

              {/* 就诊记录 */}
              {activeTab === 'records' && (
                records.length === 0
                  ? <EmptyState message="暂无就诊记录" icon={FileText} />
                  : <div className="space-y-2">
                      {records.map(record => (
                        <TimelineItem key={record.id} record={record} />
                      ))}
                    </div>
              )}

              {/* 症状日志 */}
              {activeTab === 'symptoms' && (
                allSymptoms.length === 0
                  ? <EmptyState message="暂无症状记录" icon={Stethoscope} />
                  : <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                      {allSymptoms.map(s => (
                        <div key={s.id} className={`rounded-lg border p-4 ${getSeverityColor(s.severity)}`}>
                          <div className="flex items-center justify-between mb-2">
                            <span className="font-medium">{s.symptom_description}</span>
                            <span className="text-lg">{getSeverityStars(s.severity)}</span>
                          </div>
                          <div className="text-xs space-y-1 opacity-80">
                            <div className="flex items-center gap-1">
                              <Clock size={12} />
                              开始时间: {formatDateTime(s.onset_time)}
                            </div>
                            {s.duration_hours && (
                              <div>持续时间: {s.duration_hours} 小时</div>
                            )}
                            {s.is_ongoing && (
                              <div className="flex items-center gap-1 font-medium">
                                <AlertTriangle size={12} />
                                持续中
                              </div>
                            )}
                            {s.triggers && <div>诱因: {s.triggers}</div>}
                          </div>
                        </div>
                      ))}
                    </div>
              )}

              {/* 体征趋势 */}
              {activeTab === 'vitals' && (
                allVitalSigns.length === 0
                  ? <EmptyState message="暂无体征数据" icon={TrendingUp} />
                  : <div className="space-y-6">
                      {chartData.length > 0 && (
                        <>
                          <div>
                            <h3 className="text-sm font-medium text-gray-700 mb-3 flex items-center gap-2">
                              <Scale size={16} /> 体重趋势 (kg)
                            </h3>
                            <div className="h-64">
                              <ResponsiveContainer width="100%" height="100%">
                                <LineChart data={chartData}>
                                  <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
                                  <XAxis dataKey="date" tick={{ fontSize: 12 }} />
                                  <YAxis tick={{ fontSize: 12 }} domain={['auto', 'auto']} />
                                  <Tooltip />
                                  <Line type="monotone" dataKey="weight" stroke="#3b82f6" strokeWidth={2} dot={{ fill: '#3b82f6', r: 4 }} name="体重(kg)" />
                                </LineChart>
                              </ResponsiveContainer>
                            </div>
                          </div>
                          {chartData.some(d => d.temperature) && (
                            <div>
                              <h3 className="text-sm font-medium text-gray-700 mb-3 flex items-center gap-2">
                                <Thermometer size={16} /> 体温趋势 (°C)
                              </h3>
                              <div className="h-64">
                                <ResponsiveContainer width="100%" height="100%">
                                  <LineChart data={chartData}>
                                    <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
                                    <XAxis dataKey="date" tick={{ fontSize: 12 }} />
                                    <YAxis tick={{ fontSize: 12 }} domain={['auto', 'auto']} />
                                    <Tooltip />
                                    <Line type="monotone" dataKey="temperature" stroke="#f59e0b" strokeWidth={2} dot={{ fill: '#f59e0b', r: 4 }} name="体温(°C)" />
                                  </LineChart>
                                </ResponsiveContainer>
                              </div>
                            </div>
                          )}
                          {(chartData.some(d => d.heartRate) || chartData.some(d => d.respiratoryRate)) && (
                            <div>
                              <h3 className="text-sm font-medium text-gray-700 mb-3 flex items-center gap-2">
                                <Activity size={16} /> 心率 & 呼吸频率
                              </h3>
                              <div className="h-64">
                                <ResponsiveContainer width="100%" height="100%">
                                  <LineChart data={chartData}>
                                    <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
                                    <XAxis dataKey="date" tick={{ fontSize: 12 }} />
                                    <YAxis tick={{ fontSize: 12 }} domain={['auto', 'auto']} />
                                    <Tooltip />
                                    <Legend />
                                    {chartData.some(d => d.heartRate) && (
                                      <Line type="monotone" dataKey="heartRate" stroke="#ef4444" strokeWidth={2} dot={{ fill: '#ef4444', r: 4 }} name="心率(bpm)" />
                                    )}
                                    {chartData.some(d => d.respiratoryRate) && (
                                      <Line type="monotone" dataKey="respiratoryRate" stroke="#10b981" strokeWidth={2} dot={{ fill: '#10b981', r: 4 }} name="呼吸(次/分)" />
                                    )}
                                  </LineChart>
                                </ResponsiveContainer>
                              </div>
                            </div>
                          )}
                        </>
                      )}
                    </div>
              )}

              {/* 化验指标 */}
              {activeTab === 'indicators' && (
                allIndicators.length === 0
                  ? <EmptyState message="暂无化验指标" icon={Activity} />
                  : <div className="overflow-x-auto">
                      <table className="w-full text-sm">
                        <thead>
                          <tr className="border-b border-gray-200">
                            <th className="text-left py-3 px-4 font-medium text-gray-700">指标</th>
                            <th className="text-left py-3 px-4 font-medium text-gray-700">数值</th>
                            <th className="text-left py-3 px-4 font-medium text-gray-700">参考范围</th>
                            <th className="text-left py-3 px-4 font-medium text-gray-700">状态</th>
                            <th className="text-left py-3 px-4 font-medium text-gray-700">说明</th>
                          </tr>
                        </thead>
                        <tbody>
                          {allIndicators.map(ind => {
                            const status = getIndicatorStatus(ind);
                            return (
                              <tr
                                key={ind.id}
                                className={`border-b border-gray-100 hover:bg-gray-50 transition-colors ${ind.is_abnormal ? 'bg-red-50' : ''}`}
                              >
                                <td className="py-3 px-4 font-medium text-gray-800">{ind.display_name}</td>
                                <td className="py-3 px-4">
                                  {ind.value !== undefined && ind.value !== null
                                    ? <span className="font-mono">{ind.value} {ind.unit}</span>
                                    : <span className="text-gray-400">-</span>
                                  }
                                </td>
                                <td className="py-3 px-4 text-gray-500">
                                  {ind.reference_min !== undefined && ind.reference_max !== undefined
                                    ? `${ind.reference_min} ~ ${ind.reference_max} ${ind.unit}`
                                    : '-'
                                  }
                                </td>
                                <td className="py-3 px-4">
                                  <span className={`inline-flex items-center px-2 py-0.5 rounded text-xs font-medium ${status.color}`}>
                                    {ind.is_abnormal && <AlertTriangle size={12} className="mr-1" />}
                                    {status.label}
                                  </span>
                                </td>
                                <td className="py-3 px-4 text-gray-500 max-w-xs">
                                  <div className="group relative">
                                    <span className="line-clamp-2">{ind.explanation || '-'}</span>
                                    {ind.explanation && ind.explanation.length > 40 && (
                                      <div className="hidden group-hover:block absolute z-10 bg-gray-800 text-white text-xs rounded-lg p-2 max-w-xs shadow-lg -top-2 left-0 transform -translate-y-full">
                                        {ind.explanation}
                                      </div>
                                    )}
                                  </div>
                                </td>
                              </tr>
                            );
                          })}
                        </tbody>
                      </table>
                    </div>
              )}

              {/* 健康评分 */}
              {activeTab === 'score' && (
                healthScore === null
                  ? <EmptyState message="数据不足，无法计算评分" icon={Star} />
                  : <div className="space-y-6">
                      {/* 大数字评分 */}
                      <div className="flex flex-col items-center py-8">
                        <div className={`w-40 h-40 rounded-full flex flex-col items-center justify-center shadow-lg ${getScoreBgColor(healthScore)} bg-opacity-10 border-4 border-opacity-30 ${getScoreBgColor(healthScore).replace('bg-', 'border-')}`}>
                          <span className={`text-5xl font-bold ${getScoreColor(healthScore)}`}>{healthScore}</span>
                          <span className="text-sm text-gray-500 mt-1">健康评分</span>
                        </div>
                        <p className="text-sm text-gray-500 mt-4">
                          {healthScore >= 80 ? '健康状况良好 👍' : healthScore >= 60 ? '健康状态一般，建议关注' : '健康状况需要重视 ⚠️'}
                        </p>
                      </div>

                      {/* 维度拆解 */}
                      <div className="space-y-4 max-w-lg mx-auto">
                        <h3 className="text-sm font-medium text-gray-700 text-center mb-4">评分维度</h3>
                        {scoreDimensions.map(dim => (
                          <div key={dim.label}>
                            <div className="flex items-center justify-between mb-1">
                              <span className="text-sm text-gray-600">{dim.label}</span>
                              <span className={`text-sm font-medium ${getScoreColor(dim.score)}`}>{dim.score}分</span>
                            </div>
                            <div className="w-full h-2.5 bg-gray-100 rounded-full overflow-hidden">
                              <div
                                className={`h-full rounded-full transition-all duration-500 ${getScoreBgColor(dim.score)}`}
                                style={{ width: `${dim.score}%` }}
                              />
                            </div>
                          </div>
                        ))}
                      </div>

                      {/* 评分规则说明 */}
                      <div className="bg-gray-50 rounded-lg p-4 mt-6 max-w-lg mx-auto">
                        <h4 className="text-sm font-medium text-gray-700 mb-2">评分规则</h4>
                        <ul className="text-xs text-gray-500 space-y-1">
                          <li>• 基础分: 80 分</li>
                          <li>• 体重在正常范围 (3-6kg): +5 分</li>
                          <li>• 化验指标正常率 &gt; 80%: +5 分</li>
                          <li>• 近 30 天无新增症状: +5 分</li>
                          <li>• 所有就诊记录已解决: +5 分</li>
                          <li>• 最低 40 分，最高 100 分</li>
                        </ul>
                      </div>
                    </div>
              )}
            </div>
          </>
        )}
      </div>
    </div>
  );
}
