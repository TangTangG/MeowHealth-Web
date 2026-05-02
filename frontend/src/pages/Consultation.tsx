import { useState, useEffect, useRef } from 'react';
import { useNavigate, useOutletContext } from 'react-router-dom';
import {
  startConsultation,
  continueConsultation,
  getConsultationStatus,
  cancelConsultation,
  uploadReport,
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
  User,
  ImagePlus,
  ChevronDown,
} from 'lucide-react';

// ========== 类型 ==========

type ConsultationPhase = 'entry' | 'collecting' | 'completed' | 'error';

interface ChatMessage {
  role: 'agent' | 'user' | 'system';
  type: 'triage' | 'question' | 'answer' | 'diagnosis' | 'system' | 'upload';
  content: string;
  meta?: any;
  timestamp: number;
}

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
  chatHistory: ChatMessage[];
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
  chatHistory: [],
  loading: false,
  error: null,
};

// ========== 辅助函数 ==========

const triageColor = (level: string | null) => {
  switch (level) {
    case 'emergency': return 'bg-red-50 border-red-200 text-red-700';
    case 'urgent': return 'bg-orange-50 border-orange-200 text-orange-700';
    case 'routine': return 'bg-blue-50 border-blue-200 text-blue-700';
    case 'non_urgent': return 'bg-green-50 border-green-200 text-green-700';
    default: return 'bg-gray-50 border-gray-200 text-gray-700';
  }
};

const triageBadgeColor = (level: string | null) => {
  switch (level) {
    case 'emergency': return 'bg-red-100 text-red-800';
    case 'urgent': return 'bg-orange-100 text-orange-800';
    case 'routine': return 'bg-blue-100 text-blue-800';
    case 'non_urgent': return 'bg-green-100 text-green-800';
    default: return 'bg-gray-100 text-gray-800';
  }
};

const triageLabel = (level: string | null) => {
  switch (level) {
    case 'emergency': return '急诊';
    case 'urgent': return '紧急';
    case 'routine': return '常规';
    case 'non_urgent': return '非紧急';
    default: return level || '未知';
  }
};

const actionAdvice = (level: string | null) => {
  switch (level) {
    case 'emergency': return '建议立即前往最近的宠物医院急诊';
    case 'urgent': return '建议今天内预约宠物医院检查';
    case 'routine': return '可预约近期体检，注意观察症状变化';
    case 'non_urgent': return '症状轻微，可居家观察或择期咨询';
    default: return '请根据实际情况决定就医时间';
  }
};

const inferInputType = (question: string): 'text' | 'textarea' | 'yesno' => {
  const q = question.toLowerCase();
  if (q.includes('是否') || q.includes('有没有') || q.includes('吗') || q.includes('是不是')) return 'yesno';
  if (q.includes('频率') || q.includes('几次') || q.includes('颜色') || q.includes('性状') || q.includes('多久')) return 'text';
  if (question.length > 40) return 'textarea';
  return 'text';
};

const symptomCategories = [
  { name: '消化系统', tags: ['呕吐', '腹泻', '软便', '拒食', '食欲下降', '吐毛球', '便秘'] },
  { name: '呼吸系统', tags: ['打喷嚏', '咳嗽', '流鼻涕', '呼吸困难', '鼻塞'] },
  { name: '泌尿生殖', tags: ['尿频', '尿血', '排尿困难', '乱尿', '尿少'] },
  { name: '皮肤毛发', tags: ['掉毛', '抓挠', '红疹', '皮屑', '流泪', '耳垢'] },
  { name: '行为精神', tags: ['精神萎靡', '亢奋', '躲藏', '攻击性', '过度舔毛', '叫唤'] },
  { name: '全身症状', tags: ['发烧', '脱水', '体重下降', '腹部疼痛', '黄疸', '抽搐'] },
];

// ========== 主组件 ==========

export default function Consultation() {
  const { selectedCatId } = useOutletContext<{ selectedCatId: string | null }>();
  const [state, setState] = useState<ConsultationState>(initialState);
  const [symptoms, setSymptoms] = useState('');
  const [currentAnswer, setCurrentAnswer] = useState('');
  const [expandedCategories, setExpandedCategories] = useState<Record<string, boolean>>({});
  const fileInputRef = useRef<HTMLInputElement>(null);
  const chatEndRef = useRef<HTMLDivElement>(null);
  const navigate = useNavigate();

  useEffect(() => {
    if (chatEndRef.current) chatEndRef.current.scrollIntoView({ behavior: 'smooth' });
  }, [state.chatHistory, state.questions]);

  useEffect(() => {
    const savedSessionId = localStorage.getItem('consultation_session_id');
    if (savedSessionId) {
      setState(s => ({ ...s, loading: true }));
      getConsultationStatus(savedSessionId)
        .then(res => {
          if (res.status === 'collecting') {
            setState({ ...initialState, phase: 'collecting', sessionId: res.session_id, currentRound: res.current_round, triageResult: res.triage_result, loading: false });
          } else if (res.status === 'completed') {
            setState({ ...initialState, phase: 'completed', sessionId: res.session_id, triageResult: res.triage_result, loading: false });
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
      const res: ConsultationStartResponse = await startConsultation({ cat_id: selectedCatId, initial_symptoms: symptoms.trim() });
      localStorage.setItem('consultation_session_id', res.session_id);
      const triageMsg: ChatMessage = {
        role: 'system', type: 'triage',
        content: `分诊结果：${triageLabel(res.triage_level)} — ${res.triage_advice || actionAdvice(res.triage_level)}`,
        meta: { level: res.triage_level }, timestamp: Date.now(),
      };
      if (res.is_sufficient || res.next_action === 'diagnose') {
        setState({ ...initialState, phase: 'completed', sessionId: res.session_id, triageLevel: res.triage_level, triageAdvice: res.triage_advice, triageResult: { level: res.triage_level, advice: res.triage_advice }, chatHistory: [triageMsg], loading: false });
      } else {
        const questionMsgs: ChatMessage[] = res.questions.map((q, i) => ({ role: 'agent', type: 'question', content: q, meta: { index: i, total: res.questions.length, round: 1 }, timestamp: Date.now() + i }));
        setState({ ...initialState, phase: 'collecting', sessionId: res.session_id, triageLevel: res.triage_level, triageAdvice: res.triage_advice, questions: res.questions, currentRound: 1, chatHistory: [triageMsg, ...questionMsgs], loading: false });
      }
    } catch (err: any) {
      setState(s => ({ ...s, phase: 'error', error: err?.response?.data?.detail || err?.message || '启动咨询失败，请重试', loading: false }));
    }
  };

  const handleSubmitAnswers = async () => {
    if (!state.sessionId) return;
    setState(s => ({ ...s, loading: true, error: null }));
    try {
      const res: ConsultationContinueResponse = await continueConsultation(state.sessionId, { user_input: state.answers });
      if (res.status === 'completed' || res.next_action === 'diagnose' || res.is_sufficient) {
        const diagMsg: ChatMessage = { role: 'agent', type: 'diagnosis', content: '诊断分析完成', meta: res.diagnosis, timestamp: Date.now() };
        setState(s => ({ ...s, phase: 'completed', diagnosis: res.diagnosis, triageResult: res.triage_result, triageLevel: res.triage_result?.level || s.triageLevel, triageAdvice: res.triage_result?.advice || s.triageAdvice, questions: [], answers: {}, currentRound: res.current_round, chatHistory: [...s.chatHistory, diagMsg], loading: false }));
      } else {
        const questionMsgs: ChatMessage[] = res.questions.map((q, i) => ({ role: 'agent', type: 'question', content: q, meta: { index: i, total: res.questions.length, round: res.current_round }, timestamp: Date.now() + i }));
        const roundMsg: ChatMessage = { role: 'system', type: 'system', content: `Round ${res.current_round} · ${res.questions.length} 个问题`, timestamp: Date.now() - 1 };
        setState(s => ({ ...s, questions: res.questions, currentRound: res.current_round, answers: {}, chatHistory: [...s.chatHistory, roundMsg, ...questionMsgs], loading: false }));
      }
    } catch (err: any) {
      setState(s => ({ ...s, phase: 'error', error: err?.response?.data?.detail || err?.message || '提交回答失败，请重试', loading: false }));
    }
  };

  const handleRestart = async () => {
    if (state.sessionId) { try { await cancelConsultation(state.sessionId); } catch {} localStorage.removeItem('consultation_session_id'); }
    setState(initialState); setSymptoms(''); setCurrentAnswer('');
  };

  const handleAnswerChange = (question: string, value: string) => { setState(s => ({ ...s, answers: { ...s.answers, [question]: value } })); };

  const handlePhotoUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0]; if (!file || !selectedCatId) return;
    try {
      const res = await uploadReport(selectedCatId, file);
      const uploadMsg: ChatMessage = { role: 'user', type: 'upload', content: `已上传症状照片：${res.filename || file.name}`, meta: { url: res.url, filename: res.filename || file.name }, timestamp: Date.now() };
      setState(s => ({ ...s, chatHistory: [...s.chatHistory, uploadMsg] }));
      handleAnswerChange('uploaded_photo', res.url || res.filename || file.name);
    } catch { setState(s => ({ ...s, error: '上传照片失败，请重试' })); }
  };

  const handleSendAnswer = (question: string) => {
    if (!currentAnswer.trim()) return;
    handleAnswerChange(question, currentAnswer.trim());
    const answerMsg: ChatMessage = { role: 'user', type: 'answer', content: currentAnswer.trim(), meta: { question }, timestamp: Date.now() };
    setState(s => ({ ...s, chatHistory: [...s.chatHistory, answerMsg] }));
    setCurrentAnswer('');
    const newAnswers = { ...state.answers, [question]: currentAnswer.trim() };
    if (state.questions.every(q => newAnswers[q]?.trim())) handleSubmitAnswers();
  };

  const toggleCategory = (name: string) => setExpandedCategories(prev => ({ ...prev, [name]: !prev[name] }));

  // ========== 入口界面 ==========
  if (state.phase === 'entry') {
    return (
      <div className="max-w-2xl mx-auto p-4 md:p-6">
        <div className="mb-6">
          <div className="flex items-center gap-3 mb-2">
            <Stethoscope className="text-blue-600" size={28} />
            <h1 className="text-2xl font-bold text-gray-900">症状咨询</h1>
          </div>
          <p className="text-gray-500">描述症状，AI 分诊引擎将引导您完成初步评估</p>
        </div>
        {!selectedCatId && (
          <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4 mb-4 flex items-start gap-3">
            <AlertTriangle className="text-yellow-600 shrink-0 mt-0.5" size={18} />
            <p className="text-sm text-yellow-800">请先选择一只猫咪，再进行症状咨询。</p>
          </div>
        )}
        <div className="bg-white rounded-xl border shadow-sm p-5 md:p-6 space-y-5">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">症状描述</label>
            <textarea className="w-full rounded-lg border border-gray-300 p-3 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 min-h-[120px] resize-y" placeholder="请详细描述猫咪的症状，例如：'我家猫昨天开始呕吐，一天吐了3次，精神不太好，也不怎么吃东西'" value={symptoms} onChange={e => setSymptoms(e.target.value)} maxLength={500} />
            <div className="flex items-center justify-between mt-1.5">
              <span className="text-xs text-gray-400">已输入 {symptoms.length} 字，建议 20 字以上</span>
              {symptoms.length > 0 && symptoms.length < 10 && <span className="text-xs text-orange-500">至少需要 10 个字</span>}
            </div>
          </div>
          <div className="space-y-3">
            <label className="block text-sm font-medium text-gray-700">快速添加常见症状</label>
            {symptomCategories.map(cat => (
              <div key={cat.name} className="border rounded-lg overflow-hidden">
                <button onClick={() => toggleCategory(cat.name)} className="w-full flex items-center justify-between px-4 py-2.5 bg-gray-50 hover:bg-gray-100 transition-colors">
                  <span className="text-sm font-medium text-gray-700">{cat.name}</span>
                  <ChevronDown size={16} className={`text-gray-400 transition-transform ${expandedCategories[cat.name] ? 'rotate-180' : ''}`} />
                </button>
                {expandedCategories[cat.name] && (
                  <div className="p-3 flex flex-wrap gap-2">
                    {cat.tags.map(tag => (
                      <button key={tag} onClick={() => setSymptoms(s => s ? `${s}，${tag}` : tag)} className="px-3 py-1.5 rounded-full bg-gray-100 text-sm text-gray-700 hover:bg-blue-50 hover:text-blue-700 transition-colors">{tag}</button>
                    ))}
                  </div>
                )}
              </div>
            ))}
          </div>
          <button onClick={handleStart} disabled={!selectedCatId || symptoms.trim().length < 10 || state.loading} className="w-full flex items-center justify-center gap-2 rounded-lg bg-blue-600 text-white py-3 font-medium hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors">
            {state.loading ? <Loader2 className="animate-spin" size={20} /> : <><Send size={18} /> 开始咨询</>}
          </button>
          <div className="flex items-start gap-2 text-xs text-gray-400 border-t pt-4">
            <AlertTriangle size={14} className="shrink-0 mt-0.5" />
            <p>本工具仅供参考，不构成医疗建议。紧急情况请立即就医。</p>
          </div>
        </div>
      </div>
    );
  }

  // ========== 追问界面（聊天式）==========
  if (state.phase === 'collecting') {
    const unansweredQuestions = state.questions.filter(q => !state.answers[q]?.trim());
    const currentQuestion = unansweredQuestions[0];
    const progress = Math.min((state.currentRound / 3) * 100, 100);
    return (
      <div className="max-w-2xl mx-auto h-[calc(100vh-4rem)] flex flex-col">
        <div className="shrink-0 bg-white border-b px-4 py-3 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Stethoscope className="text-blue-600" size={20} />
            <h1 className="font-semibold text-gray-900">症状咨询</h1>
          </div>
          {state.triageLevel && (
            <div className={`px-3 py-1 rounded-full text-xs font-medium ${triageBadgeColor(state.triageLevel)} ${state.triageLevel === 'emergency' ? 'animate-pulse' : state.triageLevel === 'urgent' ? 'animate-bounce' : ''}`}>
              {triageLabel(state.triageLevel)}
            </div>
          )}
        </div>
        <div className="shrink-0 bg-white px-4 py-2 border-b">
          <div className="flex items-center justify-between mb-1">
            <span className="text-xs text-gray-500">信息收集中</span>
            <span className="text-xs text-gray-500">Round {state.currentRound}/3</span>
          </div>
          <div className="w-full bg-gray-200 rounded-full h-1.5"><div className="bg-blue-600 h-1.5 rounded-full transition-all" style={{ width: `${progress}%` }} /></div>
        </div>
        <div className="flex-1 overflow-y-auto px-4 py-4 space-y-4 bg-gray-50">
          {state.triageLevel && (
            <div className={`rounded-xl border p-3 ${triageColor(state.triageLevel)}`}>
              <div className="flex items-center gap-2 mb-1">
                <span className={`px-2 py-0.5 rounded text-xs font-medium ${triageBadgeColor(state.triageLevel)}`}>{triageLabel(state.triageLevel)}</span>
              </div>
              <p className="text-sm">{state.triageAdvice || actionAdvice(state.triageLevel)}</p>
            </div>
          )}
          {state.chatHistory.map((msg, idx) => {
            if (msg.type === 'triage') return null;
            if (msg.role === 'system') return <div key={idx} className="text-center"><span className="text-xs text-gray-400 bg-gray-200 px-3 py-1 rounded-full">{msg.content}</span></div>;
            if (msg.role === 'agent') return (
              <div key={idx} className="flex items-start gap-2">
                <div className="w-8 h-8 rounded-full bg-blue-100 flex items-center justify-center shrink-0"><Stethoscope size={16} className="text-blue-600" /></div>
                <div className="bg-white rounded-2xl rounded-tl-sm border shadow-sm px-4 py-3 max-w-[80%]"><p className="text-sm text-gray-800">{msg.content}</p></div>
              </div>
            );
            return (
              <div key={idx} className="flex items-start gap-2 flex-row-reverse">
                <div className="w-8 h-8 rounded-full bg-gray-200 flex items-center justify-center shrink-0"><User size={16} className="text-gray-600" /></div>
                <div className="bg-blue-600 rounded-2xl rounded-tr-sm px-4 py-3 max-w-[80%]"><p className="text-sm text-white">{msg.content}</p></div>
              </div>
            );
          })}
          {currentQuestion && (
            <div className="flex items-start gap-2">
              <div className="w-8 h-8 rounded-full bg-blue-100 flex items-center justify-center shrink-0"><Stethoscope size={16} className="text-blue-600" /></div>
              <div className="bg-white rounded-2xl rounded-tl-sm border shadow-sm px-4 py-3 max-w-[80%] space-y-3">
                <p className="text-sm text-gray-800 font-medium">{currentQuestion}</p>
                {inferInputType(currentQuestion) === 'yesno' ? (
                  <div className="flex gap-2">
                    {['是', '否'].map(opt => (
                      <button key={opt} onClick={() => { handleAnswerChange(currentQuestion, opt); const answerMsg: ChatMessage = { role: 'user', type: 'answer', content: opt, meta: { question: currentQuestion }, timestamp: Date.now() }; setState(s => ({ ...s, chatHistory: [...s.chatHistory, answerMsg], answers: { ...s.answers, [currentQuestion]: opt } })); const newAnswers = { ...state.answers, [currentQuestion]: opt }; if (state.questions.every(q => newAnswers[q]?.trim())) setTimeout(() => handleSubmitAnswers(), 300); }} className={`px-4 py-2 rounded-lg border text-sm transition-colors ${state.answers[currentQuestion] === opt ? 'border-blue-500 bg-blue-50 text-blue-700' : 'border-gray-200 hover:bg-gray-50 text-gray-700'}`}>{opt}</button>
                    ))}
                  </div>
                ) : (
                  <div className="flex gap-2">
                    <input type="text" className="flex-1 rounded-lg border border-gray-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500" placeholder="请输入..." value={currentAnswer} onChange={e => setCurrentAnswer(e.target.value)} onKeyDown={e => { if (e.key === 'Enter' && currentAnswer.trim()) handleSendAnswer(currentQuestion); }} />
                    <button onClick={() => handleSendAnswer(currentQuestion)} disabled={!currentAnswer.trim()} className="p-2 rounded-lg bg-blue-600 text-white hover:bg-blue-700 disabled:opacity-50"><Send size={16} /></button>
                  </div>
                )}
              </div>
            </div>
          )}
          {state.loading && (
            <div className="flex items-start gap-2">
              <div className="w-8 h-8 rounded-full bg-blue-100 flex items-center justify-center shrink-0"><Stethoscope size={16} className="text-blue-600" /></div>
              <div className="bg-white rounded-2xl rounded-tl-sm border shadow-sm px-4 py-3"><Loader2 className="animate-spin text-blue-600" size={18} /></div>
            </div>
          )}
          <div ref={chatEndRef} />
        </div>
        <div className="shrink-0 border-t bg-white p-3 flex items-end gap-2">
          <input ref={fileInputRef} type="file" accept="image/*" className="hidden" onChange={handlePhotoUpload} />
          <button onClick={() => fileInputRef.current?.click()} className="p-2 rounded-lg hover:bg-gray-100 text-gray-500 transition-colors" title="上传症状照片"><ImagePlus size={20} /></button>
          <input className="flex-1 rounded-lg border border-gray-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500" placeholder="输入回答..." value={currentAnswer} onChange={e => setCurrentAnswer(e.target.value)} onKeyDown={e => { if (e.key === 'Enter' && currentAnswer.trim() && currentQuestion) handleSendAnswer(currentQuestion); }} />
          <button onClick={() => currentQuestion && handleSendAnswer(currentQuestion)} disabled={!currentAnswer.trim() || !currentQuestion} className="p-2 rounded-lg bg-blue-600 text-white hover:bg-blue-700 disabled:opacity-50 transition-colors"><Send size={18} /></button>
        </div>
      </div>
    );
  }

  // ========== 诊断结果 ==========
  if (state.phase === 'completed') {
    const topDiseases = state.diagnosis?.top_diseases || [];
    const suggestedExams = state.diagnosis?.suggested_exams || [];
    return (
      <div className="max-w-2xl mx-auto p-4 md:p-6">
        <div className="mb-6">
          <h1 className="text-xl font-bold text-gray-900 flex items-center gap-2"><Stethoscope className="text-blue-600" size={24} /> 咨询结果</h1>
        </div>
        {state.chatHistory.length > 0 && (
          <details className="mb-4 bg-white rounded-xl border shadow-sm">
            <summary className="px-5 py-3 text-sm text-gray-500 cursor-pointer font-medium flex items-center gap-2"><ChevronRight size={16} className="text-gray-400" /> 查看问诊过程（{state.chatHistory.length} 条消息）</summary>
            <div className="px-5 pb-4 max-h-60 overflow-y-auto space-y-3">
              {state.chatHistory.map((msg, idx) => (
                <div key={idx} className={`flex items-start gap-2 ${msg.role === 'user' ? 'flex-row-reverse' : ''}`}>
                  <div className={`w-6 h-6 rounded-full flex items-center justify-center shrink-0 ${msg.role === 'agent' ? 'bg-blue-100' : msg.role === 'user' ? 'bg-gray-200' : 'bg-gray-100'}`}>
                    {msg.role === 'agent' ? <Stethoscope size={12} className="text-blue-600" /> : msg.role === 'user' ? <User size={12} className="text-gray-600" /> : <span className="text-[10px] text-gray-500">S</span>}
                  </div>
                  <div className={`rounded-lg px-3 py-2 text-xs max-w-[85%] ${msg.role === 'agent' ? 'bg-white border' : msg.role === 'user' ? 'bg-blue-600 text-white' : 'bg-gray-100 text-gray-500'}`}>{msg.content}</div>
                </div>
              ))}
            </div>
          </details>
        )}
        {state.triageLevel && (
          <div className={`rounded-xl border p-4 mb-4 ${triageColor(state.triageLevel)}`}>
            <div className="flex items-center gap-2 mb-2"><span className={`inline-block px-2.5 py-1 rounded text-xs font-medium ${triageBadgeColor(state.triageLevel)}`}>{triageLabel(state.triageLevel)}</span></div>
            <p className="text-sm font-medium">{state.triageAdvice || actionAdvice(state.triageLevel)}</p>
          </div>
        )}
        <div className="bg-white rounded-xl border shadow-sm p-5 mb-4">
          <h2 className="text-sm font-semibold text-gray-500 uppercase tracking-wide mb-3">行动建议</h2>
          <p className="text-gray-800">{actionAdvice(state.triageLevel)}</p>
        </div>
        <div className="bg-white rounded-xl border shadow-sm p-5 md:p-6 mb-4 space-y-5">
          <h2 className="text-sm font-semibold text-gray-500 uppercase tracking-wide">可能的疾病（Top {topDiseases.length || 3}）</h2>
          {topDiseases.length === 0 && <p className="text-sm text-gray-400">暂无详细疾病分析数据。</p>}
          {topDiseases.map((d: any, idx: number) => (
            <div key={idx} className="border rounded-lg p-4 space-y-2">
              <div className="flex items-center justify-between"><span className="font-medium text-gray-900">{d.name || d.disease || '未知疾病'}</span><span className="text-sm font-medium text-blue-600">{(d.probability || d.confidence || 0).toFixed ? `${(d.probability || d.confidence * 100 || 0).toFixed(1)}%` : (d.probability || d.confidence || '-')}</span></div>
              <p className="text-sm text-gray-500">{d.differential || d.reasoning || d.description || ''}</p>
            </div>
          ))}
          {suggestedExams.length > 0 && (
            <div className="pt-2">
              <h3 className="text-sm font-medium text-gray-700 mb-2">建议检查项目</h3>
              <div className="flex flex-wrap gap-2">
                {suggestedExams.map((exam: string, idx: number) => (<span key={idx} className="px-3 py-1 rounded-full bg-blue-50 text-blue-700 text-xs font-medium">{exam}</span>))}
              </div>
            </div>
          )}
        </div>
        <div className="flex flex-col sm:flex-row gap-3">
          <button onClick={handleRestart} className="flex-1 flex items-center justify-center gap-2 rounded-lg bg-blue-600 text-white py-3 font-medium hover:bg-blue-700 transition-colors"><RefreshCw size={18} /> 重新咨询</button>
          <button onClick={() => navigate('/')} className="flex-1 flex items-center justify-center gap-2 rounded-lg border border-gray-300 text-gray-700 py-3 font-medium hover:bg-gray-50 transition-colors"><FileText size={18} /> 查看健康档案</button>
        </div>
      </div>
    );
  }

  // ========== 错误状态 ==========
  return (
    <div className="max-w-2xl mx-auto p-4 md:p-6">
      <div className="bg-red-50 border border-red-200 rounded-xl p-6 text-center space-y-4">
        <AlertTriangle className="mx-auto text-red-500" size={40} />
        <h2 className="text-lg font-semibold text-red-800">出错了</h2>
        <p className="text-sm text-red-700">{state.error || '未知错误'}</p>
        <button onClick={handleRestart} className="inline-flex items-center gap-2 rounded-lg bg-red-600 text-white px-5 py-2.5 font-medium hover:bg-red-700 transition-colors"><RotateCcw size={18} /> 重试</button>
      </div>
    </div>
  );
}
