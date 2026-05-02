import { useState, useEffect } from 'react';
import { useNavigate, useOutletContext } from 'react-router-dom';
import {
  startConsultation,
  continueConsultation,
  getConsultationStatus,
  cancelConsultation,
  type ConsultationStartResponse,
  type ConsultationContinueResponse,
} from '@/lib/api';
import {
  Stethoscope,
  Send,
  Loader2,
  AlertTriangle,
  ChevronRight,
  RefreshCw,
  FileText,
  RotateCcw,
} from 'lucide-react';

// ========== 类型 ==========

type ConsultationPhase = 'entry' | 'collecting' | 'completed' | 'error';

interface ConsultationState {
  phase: ConsultationPhase;
  sessionId: string | null;
  triageLevel: string | null;
  triageAdvice: string | null;
  questions: string[];
  currentRound: number;
  answers: Record<string, string>;
  diagnosis: any;
  triageResult: any;
  loading: boolean;
  error: string | null;
}

const initialState: ConsultationState = {
  phase: 'entry',
  sessionId: null,
  triageLevel: null,
  triageAdvice: null,
  questions: [],
  currentRound: 0,
  answers: {},
  diagnosis: null,
  triageResult: null,
  loading: false,
  error: null,
};

// ========== 辅助函数 ==========

const triageColor = (level: string | null) => {
  switch (level) {
    case 'emergency':
      return 'bg-red-50 border-red-200 text-red-700';
    case 'urgent':
      return 'bg-orange-50 border-orange-200 text-orange-700';
    case 'routine':
      return 'bg-blue-50 border-blue-200 text-blue-700';
    case 'non_urgent':
      return 'bg-green-50 border-green-200 text-green-700';
    default:
      return 'bg-gray-50 border-gray-200 text-gray-700';
  }
};

const triageBadgeColor = (level: string | null) => {
  switch (level) {
    case 'emergency':
      return 'bg-red-100 text-red-800';
    case 'urgent':
      return 'bg-orange-100 text-orange-800';
    case 'routine':
      return 'bg-blue-100 text-blue-800';
    case 'non_urgent':
      return 'bg-green-100 text-green-800';
    default:
      return 'bg-gray-100 text-gray-800';
  }
};

const triageLabel = (level: string | null) => {
  switch (level) {
    case 'emergency':
      return '急诊';
    case 'urgent':
      return '紧急';
    case 'routine':
      return '常规';
    case 'non_urgent':
      return '非紧急';
    default:
      return level || '未知';
  }
};

const actionAdvice = (level: string | null) => {
  switch (level) {
    case 'emergency':
      return '建议立即前往最近的宠物医院急诊';
    case 'urgent':
      return '建议今天内预约宠物医院检查';
    case 'routine':
      return '可预约近期体检，注意观察症状变化';
    case 'non_urgent':
      return '症状轻微，可居家观察或择期咨询';
    default:
      return '请根据实际情况决定就医时间';
  }
};

const inferInputType = (question: string): 'text' | 'textarea' | 'yesno' => {
  const q = question.toLowerCase();
  if (q.includes('是否') || q.includes('有没有') || q.includes('吗') || q.includes('是不是')) {
    return 'yesno';
  }
  if (q.includes('频率') || q.includes('几次') || q.includes('颜色') || q.includes('性状') || q.includes('多久')) {
    return 'text';
  }
  if (question.length > 40) {
    return 'textarea';
  }
  return 'text';
};

const quickTags = [
  '呕吐',
  '腹泻',
  '食欲下降',
  '精神萎靡',
  '发烧',
  '排尿异常',
  '皮肤红疹',
  '呼吸困难',
];

// ========== 主组件 ==========

export default function Consultation() {
  const { selectedCatId } = useOutletContext<{ selectedCatId: string | null }>();
  const [state, setState] = useState<ConsultationState>(initialState);
  const [symptoms, setSymptoms] = useState('');
  const navigate = useNavigate();

  // 恢复本地缓存的 session
  useEffect(() => {
    const savedSessionId = localStorage.getItem('consultation_session_id');
    if (savedSessionId) {
      setState(s => ({ ...s, loading: true }));
      getConsultationStatus(savedSessionId)
        .then(res => {
          if (res.status === 'collecting') {
            setState({
              ...initialState,
              phase: 'collecting',
              sessionId: res.session_id,
              currentRound: res.current_round,
              triageResult: res.triage_result,
              loading: false,
            });
          } else if (res.status === 'completed') {
            setState({
              ...initialState,
              phase: 'completed',
              sessionId: res.session_id,
              triageResult: res.triage_result,
              loading: false,
            });
          } else {
            localStorage.removeItem('consultation_session_id');
            setState(initialState);
          }
        })
        .catch(() => {
          localStorage.removeItem('consultation_session_id');
          setState(initialState);
        });
    }
  }, []);

  const handleStart = async () => {
    if (!selectedCatId || symptoms.trim().length < 10) return;
    setState(s => ({ ...s, loading: true, error: null }));
    try {
      const res: ConsultationStartResponse = await startConsultation({
        cat_id: selectedCatId,
        initial_symptoms: symptoms.trim(),
      });
      localStorage.setItem('consultation_session_id', res.session_id);
      if (res.is_sufficient || res.next_action === 'diagnose') {
        // 直接完成
        setState({
          ...initialState,
          phase: 'completed',
          sessionId: res.session_id,
          triageLevel: res.triage_level,
          triageAdvice: res.triage_advice,
          triageResult: { level: res.triage_level, advice: res.triage_advice },
          loading: false,
        });
      } else {
        setState({
          ...initialState,
          phase: 'collecting',
          sessionId: res.session_id,
          triageLevel: res.triage_level,
          triageAdvice: res.triage_advice,
          questions: res.questions,
          currentRound: 1,
          loading: false,
        });
      }
    } catch (err: any) {
      setState(s => ({
        ...s,
        phase: 'error',
        error: err?.response?.data?.detail || err?.message || '启动咨询失败，请重试',
        loading: false,
      }));
    }
  };

  const handleSubmitAnswers = async () => {
    if (!state.sessionId) return;
    setState(s => ({ ...s, loading: true, error: null }));
    try {
      const res: ConsultationContinueResponse = await continueConsultation(
        state.sessionId,
        { user_input: state.answers }
      );
      if (res.status === 'completed' || res.next_action === 'diagnose' || res.is_sufficient) {
        setState(s => ({
          ...s,
          phase: 'completed',
          diagnosis: res.diagnosis,
          triageResult: res.triage_result,
          triageLevel: res.triage_result?.level || s.triageLevel,
          triageAdvice: res.triage_result?.advice || s.triageAdvice,
          questions: [],
          answers: {},
          currentRound: res.current_round,
          loading: false,
        }));
      } else {
        setState(s => ({
          ...s,
          questions: res.questions,
          currentRound: res.current_round,
          answers: {},
          loading: false,
        }));
      }
    } catch (err: any) {
      setState(s => ({
        ...s,
        phase: 'error',
        error: err?.response?.data?.detail || err?.message || '提交回答失败，请重试',
        loading: false,
      }));
    }
  };

  const handleRestart = async () => {
    if (state.sessionId) {
      try { await cancelConsultation(state.sessionId); } catch {}
      localStorage.removeItem('consultation_session_id');
    }
    setState(initialState);
    setSymptoms('');
  };

  const handleAnswerChange = (question: string, value: string) => {
    setState(s => ({
      ...s,
      answers: { ...s.answers, [question]: value },
    }));
  };

  // ========== 渲染：入口界面 ==========
  if (state.phase === 'entry') {
    return (
      <div className="max-w-2xl mx-auto p-4 md:p-6">
        <div className="mb-6">
          <div className="flex items-center gap-3 mb-2">
            <Stethoscope className="text-blue-600" size={28} />
            <h1 className="text-2xl font-bold text-gray-900">症状咨询</h1>
          </div>
          <p className="text-gray-500">
            描述症状，AI 分诊引擎将引导您完成初步评估
          </p>
        </div>

        {!selectedCatId && (
          <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4 mb-4 flex items-start gap-3">
            <AlertTriangle className="text-yellow-600 shrink-0 mt-0.5" size={18} />
            <p className="text-sm text-yellow-800">
              请先选择一只猫咪，再进行症状咨询。
            </p>
          </div>
        )}

        <div className="bg-white rounded-xl border shadow-sm p-5 md:p-6 space-y-5">
          {/* 症状输入 */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              症状描述
            </label>
            <textarea
              className="w-full rounded-lg border border-gray-300 p-3 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 min-h-[120px] resize-y"
              placeholder="请详细描述猫咪的症状，例如：'我家猫昨天开始呕吐，一天吐了3次，精神不太好，也不怎么吃东西'"
              value={symptoms}
              onChange={e => setSymptoms(e.target.value)}
              maxLength={500}
            />
            <div className="flex items-center justify-between mt-1.5">
              <span className="text-xs text-gray-400">
                已输入 {symptoms.length} 字，建议 20 字以上
              </span>
              {symptoms.length > 0 && symptoms.length < 10 && (
                <span className="text-xs text-orange-500">
                  至少需要 10 个字
                </span>
              )}
            </div>
          </div>

          {/* 快速标签 */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              快速添加常见症状
            </label>
            <div className="flex flex-wrap gap-2">
              {quickTags.map(tag => (
                <button
                  key={tag}
                  onClick={() => setSymptoms(s => s ? `${s}，${tag}` : tag)}
                  className="px-3 py-1.5 rounded-full bg-gray-100 text-sm text-gray-700 hover:bg-blue-50 hover:text-blue-700 transition-colors"
                >
                  {tag}
                </button>
              ))}
            </div>
          </div>

          {/* 开始按钮 */}
          <button
            onClick={handleStart}
            disabled={!selectedCatId || symptoms.trim().length < 10 || state.loading}
            className="w-full flex items-center justify-center gap-2 rounded-lg bg-blue-600 text-white py-3 font-medium hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
          >
            {state.loading ? (
              <Loader2 className="animate-spin" size={20} />
            ) : (
              <>
                <Send size={18} />
                开始咨询
              </>
            )}
          </button>

          {/* 免责声明 */}
          <div className="flex items-start gap-2 text-xs text-gray-400 border-t pt-4">
            <AlertTriangle size={14} className="shrink-0 mt-0.5" />
            <p>
              本工具仅供参考，不构成医疗建议。紧急情况请立即就医。
            </p>
          </div>
        </div>
      </div>
    );
  }

  // ========== 渲染：追问界面 ==========
  if (state.phase === 'collecting') {
    return (
      <div className="max-w-2xl mx-auto p-4 md:p-6">
        <div className="mb-6">
          <h1 className="text-xl font-bold text-gray-900 flex items-center gap-2">
            <Stethoscope className="text-blue-600" size={24} />
            症状咨询
          </h1>
        </div>

        {/* 进度条 */}
        <div className="bg-white rounded-xl border shadow-sm p-4 mb-4">
          <div className="flex items-center justify-between mb-2">
            <span className="text-sm font-medium text-gray-700">
              信息收集中
            </span>
            <span className="text-sm text-gray-500">
              Round {state.currentRound}
            </span>
          </div>
          <div className="w-full bg-gray-200 rounded-full h-2">
            <div
              className="bg-blue-600 h-2 rounded-full transition-all"
              style={{ width: `${Math.min((state.currentRound / 3) * 100, 100)}%` }}
            />
          </div>
        </div>

        {/* 分诊卡片 */}
        {state.triageLevel && (
          <div className={`rounded-xl border p-4 mb-4 ${triageColor(state.triageLevel)}`}>
            <div className="flex items-center gap-2 mb-1">
              <span className={`inline-block px-2 py-0.5 rounded text-xs font-medium ${triageBadgeColor(state.triageLevel)}`}>
                {triageLabel(state.triageLevel)}
              </span>
            </div>
            <p className="text-sm">{state.triageAdvice || actionAdvice(state.triageLevel)}</p>
          </div>
        )}

        {/* 问题表单 */}
        <div className="bg-white rounded-xl border shadow-sm p-5 md:p-6 space-y-5">
          <h2 className="text-sm font-semibold text-gray-500 uppercase tracking-wide">
            请回答以下问题
          </h2>

          {state.questions.map((q, idx) => {
            const inputType = inferInputType(q);
            return (
              <div key={idx} className="space-y-2">
                <label className="block text-sm font-medium text-gray-800">
                  {idx + 1}. {q}
                </label>
                {inputType === 'yesno' ? (
                  <div className="flex gap-3">
                    {['是', '否'].map(opt => (
                      <label
                        key={opt}
                        className={`flex items-center gap-2 px-4 py-2 rounded-lg border cursor-pointer transition-colors ${
                          state.answers[q] === opt
                            ? 'border-blue-500 bg-blue-50 text-blue-700'
                            : 'border-gray-200 hover:bg-gray-50'
                        }`}
                      >
                        <input
                          type="radio"
                          name={`q-${idx}`}
                          value={opt}
                          checked={state.answers[q] === opt}
                          onChange={e => handleAnswerChange(q, e.target.value)}
                          className="hidden"
                        />
                        <span className="text-sm">{opt}</span>
                      </label>
                    ))}
                  </div>
                ) : inputType === 'textarea' ? (
                  <textarea
                    className="w-full rounded-lg border border-gray-300 p-3 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 min-h-[80px] resize-y"
                    placeholder="请输入..."
                    value={state.answers[q] || ''}
                    onChange={e => handleAnswerChange(q, e.target.value)}
                  />
                ) : (
                  <input
                    type="text"
                    className="w-full rounded-lg border border-gray-300 p-3 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                    placeholder="请输入..."
                    value={state.answers[q] || ''}
                    onChange={e => handleAnswerChange(q, e.target.value)}
                  />
                )}
              </div>
            );
          })}

          <div className="flex gap-3 pt-2">
            <button
              onClick={handleSubmitAnswers}
              disabled={state.loading || state.questions.some(q => !state.answers[q]?.trim())}
              className="flex-1 flex items-center justify-center gap-2 rounded-lg bg-blue-600 text-white py-2.5 font-medium hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
            >
              {state.loading ? (
                <Loader2 className="animate-spin" size={18} />
              ) : (
                <>
                  <ChevronRight size={18} />
                  提交回答
                </>
              )}
            </button>
            <button
              onClick={handleRestart}
              className="px-4 py-2.5 rounded-lg border border-gray-300 text-gray-600 hover:bg-gray-50 transition-colors"
            >
              <RotateCcw size={18} />
            </button>
          </div>
        </div>
      </div>
    );
  }

  // ========== 渲染：诊断结果界面 ==========
  if (state.phase === 'completed') {
    const topDiseases = state.diagnosis?.top_diseases || [];
    const suggestedExams = state.diagnosis?.suggested_exams || [];

    return (
      <div className="max-w-2xl mx-auto p-4 md:p-6">
        <div className="mb-6">
          <h1 className="text-xl font-bold text-gray-900 flex items-center gap-2">
            <Stethoscope className="text-blue-600" size={24} />
            咨询结果
          </h1>
        </div>

        {/* 分诊回顾 */}
        {state.triageLevel && (
          <div className={`rounded-xl border p-4 mb-4 ${triageColor(state.triageLevel)}`}>
            <div className="flex items-center gap-2 mb-2">
              <span className={`inline-block px-2.5 py-1 rounded text-xs font-medium ${triageBadgeColor(state.triageLevel)}`}>
                {triageLabel(state.triageLevel)}
              </span>
            </div>
            <p className="text-sm font-medium">
              {state.triageAdvice || actionAdvice(state.triageLevel)}
            </p>
          </div>
        )}

        {/* 行动建议 */}
        <div className="bg-white rounded-xl border shadow-sm p-5 mb-4">
          <h2 className="text-sm font-semibold text-gray-500 uppercase tracking-wide mb-3">
            行动建议
          </h2>
          <p className="text-gray-800">{actionAdvice(state.triageLevel)}</p>
        </div>

        {/* 诊断卡片 */}
        <div className="bg-white rounded-xl border shadow-sm p-5 md:p-6 mb-4 space-y-5">
          <h2 className="text-sm font-semibold text-gray-500 uppercase tracking-wide">
            可能的疾病（Top {topDiseases.length || 3}）
          </h2>

          {topDiseases.length === 0 && (
            <p className="text-sm text-gray-400">
              暂无详细疾病分析数据。
            </p>
          )}

          {topDiseases.map((d: any, idx: number) => (
            <div key={idx} className="border rounded-lg p-4 space-y-2">
              <div className="flex items-center justify-between">
                <span className="font-medium text-gray-900">{d.name || d.disease || '未知疾病'}</span>
                <span className="text-sm font-medium text-blue-600">
                  {(d.probability || d.confidence || 0).toFixed ?
                    `${(d.probability || d.confidence * 100 || 0).toFixed(1)}%` :
                    (d.probability || d.confidence || '-')}
                </span>
              </div>
              <p className="text-sm text-gray-500">{d.differential || d.reasoning || d.description || ''}</p>
            </div>
          ))}

          {/* 建议检查 */}
          {suggestedExams.length > 0 && (
            <div className="pt-2">
              <h3 className="text-sm font-medium text-gray-700 mb-2">
                建议检查项目
              </h3>
              <div className="flex flex-wrap gap-2">
                {suggestedExams.map((exam: string, idx: number) => (
                  <span
                    key={idx}
                    className="px-3 py-1 rounded-full bg-blue-50 text-blue-700 text-xs font-medium"
                  >
                    {exam}
                  </span>
                ))}
              </div>
            </div>
          )}
        </div>

        {/* 底部按钮 */}
        <div className="flex flex-col sm:flex-row gap-3">
          <button
            onClick={handleRestart}
            className="flex items-center justify-center gap-2 rounded-lg bg-blue-600 text-white py-3 font-medium hover:bg-blue-700 transition-colors"
          >
            <RefreshCw size={18} />
            重新咨询
          </button>
          <button
            onClick={() => navigate('/')}
            className="flex items-center justify-center gap-2 rounded-lg border border-gray-300 text-gray-700 py-3 font-medium hover:bg-gray-50 transition-colors"
          >
            <FileText size={18} />
            查看健康档案
          </button>
        </div>
      </div>
    );
  }

  // ========== 渲染：错误状态 ==========
  return (
    <div className="max-w-2xl mx-auto p-4 md:p-6">
      <div className="bg-red-50 border border-red-200 rounded-xl p-6 text-center space-y-4">
        <AlertTriangle className="mx-auto text-red-500" size={40} />
        <h2 className="text-lg font-semibold text-red-800">出错了</h2>
        <p className="text-sm text-red-700">{state.error || '未知错误'}</p>
        <button
          onClick={handleRestart}
          className="inline-flex items-center gap-2 rounded-lg bg-red-600 text-white px-5 py-2.5 font-medium hover:bg-red-700 transition-colors"
        >
          <RotateCcw size={18} />
          重试
        </button>
      </div>
    </div>
  );
}
