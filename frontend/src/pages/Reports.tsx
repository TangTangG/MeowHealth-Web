import { useState, useEffect } from 'react';
import { useOutletContext } from 'react-router-dom';
import { UploadZone } from '@/components/UploadZone';
import { ReportCard } from '@/components/ReportCard';
import { ChatAssistant } from '@/components/ChatAssistant';
import { api } from '@/lib/api';
import { FileText, Loader2, Sparkles, Trash2, Key, ChevronLeft } from 'lucide-react';

interface OutletContext {
  selectedCatId: string | null;
}

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

interface Report {
  id: string;
  cat_id: string;
  title: string;
  date: string;
  ai_summary: string;
  actionable_advice: string[];
  indicators: Indicator[];
  file_name?: string;
  created_at: string;
}

export default function Reports() {
  const { selectedCatId } = useOutletContext<OutletContext>();
  const [reports, setReports] = useState<Report[]>([]);
  const [selectedReport, setSelectedReport] = useState<Report | null>(null);
  const [loading, setLoading] = useState(false);
  const [apiKeyConfigured, setApiKeyConfigured] = useState(false);
  const [showApiKeyInput, setShowApiKeyInput] = useState(false);
  const [apiKey, setApiKey] = useState('');

  const loadReports = async () => {
    if (!selectedCatId) return;
    try {
      setLoading(true);
      const { data } = await api.get('/reports/', { params: { cat_id: selectedCatId } });
      setReports(data);
    } catch (error) {
      console.error('Failed to load reports:', error);
    } finally {
      setLoading(false);
    }
  };

  const checkApiKey = async () => {
    try {
      const { data } = await api.get('/settings/gemini-api-key');
      setApiKeyConfigured(!!data.api_key);
    } catch (error) {
      setApiKeyConfigured(false);
    }
  };

  useEffect(() => {
    loadReports();
    checkApiKey();
  }, [selectedCatId]);

  const handleUploadComplete = (reportId: string) => {
    // 上传完成后刷新列表并显示新报告
    loadReports();
    // 可选：自动打开新报告
    // const newReport = reports.find(r => r.id === reportId);
    // if (newReport) setSelectedReport(newReport);
  };

  const handleDelete = async (reportId: string) => {
    if (!confirm('确定要删除这个化验单吗？')) return;
    try {
      await api.delete(`/reports/${reportId}`);
      if (selectedReport?.id === reportId) {
        setSelectedReport(null);
      }
      loadReports();
    } catch (error) {
      console.error('Failed to delete:', error);
      alert('删除失败');
    }
  };

  const handleSetApiKey = async () => {
    if (!apiKey.trim()) return;
    try {
      await api.post('/settings/gemini-api-key', { api_key: apiKey.trim() });
      setApiKeyConfigured(true);
      setShowApiKeyInput(false);
      setApiKey('');
      alert('API Key 设置成功！');
    } catch (error) {
      alert('设置失败');
    }
  };

  if (!selectedCatId) {
    return (
      <div className="flex items-center justify-center h-96">
        <p className="text-gray-500">请先在侧边栏选择一只猫咪</p>
      </div>
    );
  }

  // 显示单个报告详情
  if (selectedReport) {
    return (
      <div>
        <div className="flex items-center gap-4 mb-6">
          <button
            onClick={() => setSelectedReport(null)}
            className="flex items-center gap-2 text-gray-600 hover:text-gray-900"
          >
            <ChevronLeft size={20} />
            返回列表
          </button>
          <h2 className="text-2xl font-bold text-gray-800">{selectedReport.title}</h2>
          <button
            onClick={() => handleDelete(selectedReport.id)}
            className="ml-auto p-2 text-red-600 hover:bg-red-50 rounded"
          >
            <Trash2 size={18} />
          </button>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          <div className="lg:col-span-2">
            <ReportCard
              title={selectedReport.title}
              date={selectedReport.date}
              summary={selectedReport.ai_summary}
              indicators={selectedReport.indicators}
              recommendations={selectedReport.actionable_advice}
            />
          </div>
          <div className="lg:col-span-1">
            <ChatAssistant reportId={selectedReport.id} />
          </div>
        </div>
      </div>
    );
  }

  return (
    <div>
      <div className="flex justify-between items-center mb-6">
        <div>
          <h2 className="text-2xl font-bold text-gray-800">化验报告</h2>
          <p className="text-gray-500">上传并 AI 解读化验单</p>
        </div>
        <button
          onClick={() => setShowApiKeyInput(true)}
          className={`flex items-center gap-2 px-4 py-2 rounded-lg transition-colors ${
            apiKeyConfigured 
              ? 'bg-green-100 text-green-700' 
              : 'bg-yellow-100 text-yellow-700'
          }`}
        >
          <Key size={18} />
          {apiKeyConfigured ? 'API Key 已配置' : '配置 API Key'}
        </button>
      </div>

      {/* API Key Input Modal */}
      {showApiKeyInput && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-6 w-96">
            <h3 className="font-semibold text-lg mb-4">配置 Gemini API Key</h3>
            <p className="text-sm text-gray-500 mb-4">
              请输入你的 Gemini API Key。你可以在 
              <a href="https://aistudio.google.com/app/apikey" target="_blank" className="text-blue-600">Google AI Studio</a>
              获取。
            </p>
            <input
              type="password"
              value={apiKey}
              onChange={(e) => setApiKey(e.target.value)}
              placeholder="输入 API Key"
              className="w-full px-3 py-2 border rounded mb-4"
            />
            <div className="flex gap-2">
              <button
                onClick={handleSetApiKey}
                className="flex-1 px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700"
              >
                保存
              </button>
              <button
                onClick={() => setShowApiKeyInput(false)}
                className="flex-1 px-4 py-2 text-gray-600 hover:bg-gray-100 rounded"
              >
                取消
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Upload Zone */}
      <div className="mb-8">
        <UploadZone catId={selectedCatId} onUploadComplete={handleUploadComplete} />
      </div>

      {/* Reports List */}
      {loading ? (
        <div className="flex items-center justify-center py-12">
          <Loader2 className="animate-spin text-blue-600" size={32} />
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {reports.map(report => (
            <div 
              key={report.id} 
              onClick={() => setSelectedReport(report)}
              className="bg-white rounded-lg p-4 shadow-sm border cursor-pointer hover:shadow-md transition-shadow"
            >
              <div className="flex items-start gap-3">
                <FileText className="text-gray-400 flex-shrink-0" size={24} />
                <div className="flex-1 min-w-0">
                  <p className="font-medium truncate">{report.title}</p>
                  <p className="text-sm text-gray-500">
                    {new Date(report.date).toLocaleDateString('zh-CN')}
                  </p>
                  {report.ai_summary && (
                    <p className="text-sm text-blue-600 mt-2 line-clamp-2">
                      {report.ai_summary}
                    </p>
                  )}
                </div>
              </div>
              
              {!report.ai_summary && (
                <div className="mt-4 flex items-center gap-2 text-yellow-600 text-sm">
                  <Sparkles size={14} />
                  等待 AI 分析
                </div>
              )}
            </div>
          ))}
        </div>
      )}

      {!loading && reports.length === 0 && (
        <div className="text-center py-12 text-gray-400">
          还没有上传化验单，点击上方区域上传
        </div>
      )}
    </div>
  );
}