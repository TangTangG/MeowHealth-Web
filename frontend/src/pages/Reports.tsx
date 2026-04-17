import { useState, useEffect } from 'react';
import { useOutletContext } from 'react-router-dom';
import UploadZone from '@/components/UploadZone';
import { getReports, uploadReport, deleteReport, analyzeReport, getApiKeyStatus, setApiKey } from '@/lib/api';
import { FileText, Loader2, Sparkles, Trash2, Key } from 'lucide-react';

interface OutletContext {
  selectedCatId: string | null;
}

interface Report {
  id: string;
  file_name: string;
  file_type: string;
  created_at: string;
}

export default function Reports() {
  const { selectedCatId } = useOutletContext<OutletContext>();
  const [reports, setReports] = useState<Report[]>([]);
  const [uploading, setUploading] = useState(false);
  const [analyzing, setAnalyzing] = useState<string | null>(null);
  const [apiKeyConfigured, setApiKeyConfigured] = useState(false);
  const [showApiKeyInput, setShowApiKeyInput] = useState(false);
  const [apiKey, setApiKey] = useState('');

  const loadReports = async () => {
    if (!selectedCatId) return;
    try {
      const data = await getReports(selectedCatId);
      setReports(data);
    } catch (error) {
      console.error('Failed to load reports:', error);
    }
  };

  const checkApiKey = async () => {
    try {
      const status = await getApiKeyStatus();
      setApiKeyConfigured(status.configured);
    } catch (error) {
      console.error('Failed to check API key:', error);
    }
  };

  useEffect(() => {
    loadReports();
    checkApiKey();
  }, [selectedCatId]);

  const handleUpload = async (files: File[]) => {
    if (!selectedCatId) return;
    setUploading(true);
    try {
      for (const file of files) {
        await uploadReport(selectedCatId, file);
      }
      loadReports();
    } catch (error) {
      console.error('Failed to upload:', error);
      alert('上传失败');
    } finally {
      setUploading(false);
    }
  };

  const handleDelete = async (reportId: string) => {
    if (!confirm('确定要删除这个化验单吗？')) return;
    try {
      await deleteReport(reportId);
      loadReports();
    } catch (error) {
      console.error('Failed to delete:', error);
    }
  };

  const handleAnalyze = async (reportId: string) => {
    if (!apiKeyConfigured) {
      setShowApiKeyInput(true);
      return;
    }
    setAnalyzing(reportId);
    try {
      await analyzeReport(reportId);
      alert('分析完成！结果已保存到健康记录。');
    } catch (error: any) {
      console.error('Failed to analyze:', error);
      if (error.response?.data?.detail?.includes('API Key')) {
        setShowApiKeyInput(true);
      } else {
        alert('分析失败: ' + (error.response?.data?.detail || '未知错误'));
      }
    } finally {
      setAnalyzing(null);
    }
  };

  const handleSetApiKey = async () => {
    if (!apiKey.trim()) return;
    try {
      await setApiKey(apiKey.trim());
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
        <UploadZone onUpload={handleUpload} uploading={uploading} />
      </div>

      {/* Reports List */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {reports.map(report => (
          <div key={report.id} className="bg-white rounded-lg p-4 shadow-sm border">
            <div className="flex items-start gap-3">
              <FileText className="text-gray-400 flex-shrink-0" size={24} />
              <div className="flex-1 min-w-0">
                <p className="font-medium truncate">{report.file_name}</p>
                <p className="text-sm text-gray-500">
                  {new Date(report.created_at).toLocaleDateString('zh-CN')}
                </p>
              </div>
              <button
                onClick={() => handleDelete(report.id)}
                className="p-1.5 text-red-600 hover:bg-red-50 rounded flex-shrink-0"
              >
                <Trash2 size={16} />
              </button>
            </div>
            
            <button
              onClick={() => handleAnalyze(report.id)}
              disabled={analyzing === report.id}
              className="mt-4 w-full flex items-center justify-center gap-2 px-4 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700 disabled:opacity-50 transition-colors"
            >
              {analyzing === report.id ? (
                <Loader2 className="animate-spin" size={16} />
              ) : (
                <Sparkles size={16} />
              )}
              {analyzing === report.id ? '分析中...' : 'AI 解读'}
            </button>
          </div>
        ))}
      </div>

      {reports.length === 0 && (
        <div className="text-center py-12 text-gray-400">
          还没有上传化验单，点击上方区域上传
        </div>
      )}
    </div>
  );
}
