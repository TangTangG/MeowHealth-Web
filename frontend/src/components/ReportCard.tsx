import React, { useState, useEffect, useRef } from 'react';
import { ChevronDown, ChevronUp, AlertCircle, TrendingUp, TrendingDown, Bot, BrainCircuit, Activity, HeartPulse, Send, MessageCircle, User, Loader2 } from 'lucide-react';
import { getReportChatHistory, sendReportChatMessage } from '../lib/api';
import { ChatMessage } from '../types';

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
  id: string;
  title: string;
  date: string;
  summary: string;
  note?: string | null;
  indicators: Indicator[];
  recommendations: string[];
}

const IndicatorCard: React.FC<{ indicator: Indicator }> = ({ indicator }) => {
  const isHigh = indicator.value && indicator.reference_max && indicator.value > indicator.reference_max;
  const isLow = indicator.value && indicator.reference_min && indicator.value < indicator.reference_min;
  
  const getStatusColor = () => {
    if (!indicator.is_abnormal) return 'bg-green-50 border-green-200';
    if (isHigh) return 'bg-red-50 border-red-200 shadow-sm shadow-red-100';
    if (isLow) return 'bg-yellow-50 border-yellow-200 shadow-sm shadow-yellow-100';
    return 'bg-gray-50 border-gray-200';
  };
  
  const getStatusIcon = () => {
    if (!indicator.is_abnormal) return null;
    if (isHigh) return <TrendingUp className="w-4 h-4 text-red-500 animate-pulse" />;
    if (isLow) return <TrendingDown className="w-4 h-4 text-yellow-500 animate-pulse" />;
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
          <span className={`text-lg font-bold ${indicator.is_abnormal ? (isHigh ? 'text-red-600' : 'text-yellow-600') : 'text-gray-900'}`}>
            {indicator.value !== null ? indicator.value.toFixed(2) : '-'}
          </span>
          <span className="text-sm text-gray-500 ml-1">{indicator.unit}</span>
        </div>
      </div>
      
      <div className="mt-1 text-xs text-gray-500">
        参考范围: {indicator.reference_min !== null ? indicator.reference_min : '-'} ~ {indicator.reference_max !== null ? indicator.reference_max : '-'} {indicator.unit}
      </div>
      
      {indicator.explanation && (
        <div className="mt-3 text-sm text-gray-800 bg-white/70 p-2.5 rounded-md border border-white/50">
          <span className="font-semibold text-gray-900 flex items-center gap-1 mb-1">
            <BrainCircuit className="w-3.5 h-3.5 text-blue-500" /> AI 诊断
          </span>
          {indicator.explanation}
        </div>
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
  id,
  title, 
  date, 
  summary,
  note,
  indicators, 
  recommendations 
}) => {
  // 解析 agent trace
  let traceData = null;
  if (note) {
    try {
      traceData = JSON.parse(note);
    } catch (e) {
      // 解析失败则忽略
    }
  }

  const [chatMessages, setChatMessages] = useState<ChatMessage[]>([]);
  const [chatInput, setChatInput] = useState('');
  const [isChatLoading, setIsChatLoading] = useState(false);
  const [isChatExpanded, setIsChatExpanded] = useState(false);
  const chatEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (isChatExpanded && chatMessages.length === 0) {
      // 首次展开时加载历史记录
      getReportChatHistory(id).then(msgs => setChatMessages(msgs)).catch(console.error);
    }
  }, [isChatExpanded, id]);

  useEffect(() => {
    // 新消息滚动到底部
    chatEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [chatMessages]);

  const handleSendMessage = async () => {
    if (!chatInput.trim() || isChatLoading) return;
    
    const userMsg = { id: Date.now().toString(), record_id: id, role: 'user' as const, content: chatInput.trim(), created_at: new Date().toISOString() };
    setChatMessages(prev => [...prev, userMsg]);
    setChatInput('');
    setIsChatLoading(true);

    try {
      const response = await sendReportChatMessage(id, userMsg.content);
      setChatMessages(prev => [...prev, response]);
    } catch (error) {
      console.error('Failed to send message:', error);
      // 可选：展示错误提示
    } finally {
      setIsChatLoading(false);
    }
  };

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
        <div className="flex items-center gap-2 mt-1">
          <p className="text-sm text-gray-500">{new Date(date).toLocaleDateString('zh-CN')}</p>
          
          {/* Personalized Badges */}
          {traceData?.skills_loaded?.breed && (
            <span className="px-2 py-0.5 rounded-full bg-purple-100 text-purple-700 text-xs font-medium border border-purple-200">
              🧬 {traceData.skills_loaded.breed}专属分析
            </span>
          )}
          {traceData?.skills_loaded?.weight_status && traceData.skills_loaded.weight_status !== "normal" && (
            <span className="px-2 py-0.5 rounded-full bg-orange-100 text-orange-700 text-xs font-medium border border-orange-200">
              ⚠️ {traceData.skills_loaded.weight_status === "overweight" ? "减脂干预" : "增肌干预"}
            </span>
          )}
        </div>
        
        {/* Agent Orchestration Trace */}
        {traceData && (
          <div className="mt-4 p-3 bg-gray-50 rounded-lg border border-gray-100 text-xs text-gray-600">
            <div className="font-semibold text-gray-700 mb-2 flex items-center gap-1">
              <Activity className="w-3.5 h-3.5" /> AI 多智能体工作流执行记录
            </div>
            <div className="flex flex-col gap-1.5 ml-1 border-l-2 border-blue-200 pl-3">
              <div>
                <span className="font-medium text-blue-700">1. Vision Agent (提取)</span>：成功从图像中提取 {traceData.orchestration?.vision_agent?.extracted_count || indicators.length} 项数值结构。
              </div>
              <div>
                <span className="font-medium text-blue-700">2. Lab Analyzer (病理)</span>：结合通用医学与{traceData.skills_loaded?.breed ? `[${traceData.skills_loaded.breed}]` : '通用'}品系特异性，发现 {traceData.orchestration?.lab_analyzer?.abnormal_count} 项异常。
              </div>
              <div>
                <span className="font-medium text-blue-700">3. Dietitian Agent (营养)</span>：针对上述异常，生成 {traceData.orchestration?.dietitian_agent?.recommendations_count || recommendations.length} 条针对性护理建议。
              </div>
            </div>
          </div>
        )}

        <div className="mt-4 p-4 bg-blue-50 rounded-lg border border-blue-100">
          <p className="text-blue-900 font-medium flex items-start gap-2">
            <Bot className="w-5 h-5 mt-0.5 text-blue-600 shrink-0" />
            <span>{summary}</span>
          </p>
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

      {/* AI Chat 追问区域 */}
      <div className="pt-4 border-t mt-6">
        <button 
          onClick={() => setIsChatExpanded(!isChatExpanded)}
          className="font-semibold text-gray-900 mb-2 flex items-center gap-2 hover:text-blue-600 transition-colors w-full text-left"
        >
          <MessageCircle className="w-5 h-5 text-blue-500" /> 
          主治医生一对一追问 (Dietitian Agent)
          {isChatExpanded ? <ChevronUp className="w-4 h-4 ml-auto" /> : <ChevronDown className="w-4 h-4 ml-auto" />}
        </button>
        
        {isChatExpanded && (
          <div className="bg-slate-50 rounded-lg border border-slate-200 mt-3 flex flex-col h-[400px]">
            {/* 消息列表 */}
            <div className="flex-1 overflow-y-auto p-4 space-y-4">
              {chatMessages.length === 0 ? (
                <div className="text-center text-sm text-slate-500 my-auto h-full flex items-center justify-center">
                  你可以向我提问关于这份化验单的任何细节。
                </div>
              ) : (
                chatMessages.map(msg => (
                  <div key={msg.id} className={`flex gap-3 ${msg.role === 'user' ? 'flex-row-reverse' : ''}`}>
                    <div className={`w-8 h-8 rounded-full flex items-center justify-center shrink-0 ${
                      msg.role === 'user' ? 'bg-blue-100 text-blue-700' : 'bg-purple-100 text-purple-700'
                    }`}>
                      {msg.role === 'user' ? <User className="w-4 h-4" /> : <Bot className="w-4 h-4" />}
                    </div>
                    <div className={`max-w-[75%] rounded-2xl p-3 text-sm ${
                      msg.role === 'user' 
                        ? 'bg-blue-600 text-white rounded-tr-none' 
                        : 'bg-white border border-slate-200 text-slate-800 rounded-tl-none shadow-sm whitespace-pre-wrap'
                    }`}>
                      {msg.content}
                    </div>
                  </div>
                ))
              )}
              {isChatLoading && (
                <div className="flex gap-3">
                  <div className="w-8 h-8 rounded-full bg-purple-100 text-purple-700 flex items-center justify-center shrink-0">
                    <Bot className="w-4 h-4" />
                  </div>
                  <div className="bg-white border border-slate-200 rounded-2xl rounded-tl-none p-3 text-sm shadow-sm flex items-center">
                    <Loader2 className="w-4 h-4 animate-spin text-slate-400 mr-2" /> 医生正在思考...
                  </div>
                </div>
              )}
              <div ref={chatEndRef} />
            </div>

            {/* 输入框 */}
            <div className="p-3 bg-white border-t rounded-b-lg">
              <div className="flex gap-2">
                <input 
                  type="text" 
                  value={chatInput}
                  onChange={e => setChatInput(e.target.value)}
                  onKeyDown={e => e.key === 'Enter' && handleSendMessage()}
                  placeholder="向主治医生提问，例如：这些处方粮建议买哪个牌子？" 
                  className="flex-1 rounded-md border-slate-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 text-sm py-2 px-3 border outline-none"
                  disabled={isChatLoading}
                />
                <button 
                  onClick={handleSendMessage}
                  disabled={isChatLoading || !chatInput.trim()}
                  className="bg-blue-600 hover:bg-blue-700 disabled:bg-slate-300 disabled:cursor-not-allowed text-white px-4 py-2 rounded-md text-sm font-medium transition-colors flex items-center gap-1"
                >
                  <Send className="w-4 h-4" /> 发送
                </button>
              </div>
              <p className="text-[11px] text-slate-400 mt-1.5 ml-1 flex items-center gap-1">
                <BrainCircuit className="w-3 h-3" /> 该追问将自动携带上述品种体型以及所有的化验数据与诊断结论作为 Context。
              </p>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};