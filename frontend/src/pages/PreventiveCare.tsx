import { useState, useEffect } from 'react';
import { useOutletContext } from 'react-router-dom';
import { Plus, Syringe, Bug, AlertTriangle, Trash2 } from 'lucide-react';
import {
  getVaccinations, deleteVaccination,
  getDeworming, deleteDeworming,
  getPreventiveSummary,
} from '@/lib/api';
import type { VaccinationRecord, DewormingRecord, PreventiveCareSummary } from '@/types';

interface OutletContext {
  selectedCatId: string | null;
}

export default function PreventiveCare() {
  const { selectedCatId } = useOutletContext<OutletContext>();
  const [activeTab, setActiveTab] = useState<'vaccination' | 'deworming'>('vaccination');
  const [vaccinations, setVaccinations] = useState<VaccinationRecord[]>([]);
  const [deworming, setDeworming] = useState<DewormingRecord[]>([]);
  const [summary, setSummary] = useState<PreventiveCareSummary | null>(null);
  const [loading, setLoading] = useState(false);

  const loadData = async () => {
    if (!selectedCatId) return;
    setLoading(true);
    try {
      const [vaxData, dewData, sumData] = await Promise.all([
        getVaccinations(selectedCatId),
        getDeworming(selectedCatId),
        getPreventiveSummary(selectedCatId),
      ]);
      setVaccinations(vaxData);
      setDeworming(dewData);
      setSummary(sumData);
    } catch (err) {
      console.error('Failed to load preventive care data:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, [selectedCatId]);

  const isOverdue = (dateStr?: string) => {
    if (!dateStr) return false;
    return new Date(dateStr) < new Date();
  };

  const formatDate = (dateStr?: string) => {
    if (!dateStr) return '—';
    return new Date(dateStr).toLocaleDateString('zh-CN');
  };

  const handleDeleteVaccination = async (id: string) => {
    if (!confirm('确定删除该疫苗记录？')) return;
    await deleteVaccination(id);
    loadData();
  };

  const handleDeleteDeworming = async (id: string) => {
    if (!confirm('确定删除该驱虫记录？')) return;
    await deleteDeworming(id);
    loadData();
  };

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold text-gray-800">疫苗与驱虫</h1>

      {summary && (
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <div className="bg-white rounded-lg shadow p-4">
            <div className="flex items-center gap-2 text-blue-600 mb-1">
              <Syringe size={18} />
              <span className="text-sm font-medium">疫苗记录</span>
            </div>
            <div className="text-2xl font-bold">{summary.vaccination_count}</div>
          </div>
          <div className="bg-white rounded-lg shadow p-4">
            <div className="flex items-center gap-2 text-green-600 mb-1">
              <Bug size={18} />
              <span className="text-sm font-medium">驱虫记录</span>
            </div>
            <div className="text-2xl font-bold">{summary.deworming_count}</div>
          </div>
          <div className={`rounded-lg shadow p-4 ${summary.overdue_vaccinations > 0 ? 'bg-red-50' : 'bg-white'}`}>
            <div className={`flex items-center gap-2 mb-1 ${summary.overdue_vaccinations > 0 ? 'text-red-600' : 'text-gray-500'}`}>
              <AlertTriangle size={18} />
              <span className="text-sm font-medium">疫苗到期</span>
            </div>
            <div className={`text-2xl font-bold ${summary.overdue_vaccinations > 0 ? 'text-red-600' : ''}`}>
              {summary.overdue_vaccinations}
            </div>
          </div>
          <div className={`rounded-lg shadow p-4 ${summary.overdue_deworming > 0 ? 'bg-red-50' : 'bg-white'}`}>
            <div className={`flex items-center gap-2 mb-1 ${summary.overdue_deworming > 0 ? 'text-red-600' : 'text-gray-500'}`}>
              <AlertTriangle size={18} />
              <span className="text-sm font-medium">驱虫到期</span>
            </div>
            <div className={`text-2xl font-bold ${summary.overdue_deworming > 0 ? 'text-red-600' : ''}`}>
              {summary.overdue_deworming}
            </div>
          </div>
        </div>
      )}

      <div className="flex gap-2 border-b border-gray-200">
        <button
          onClick={() => setActiveTab('vaccination')}
          className={`px-4 py-2 font-medium ${activeTab === 'vaccination' ? 'text-blue-600 border-b-2 border-blue-600' : 'text-gray-500'}`}
        >
          <Syringe size={16} className="inline mr-1" />
          疫苗接种
        </button>
        <button
          onClick={() => setActiveTab('deworming')}
          className={`px-4 py-2 font-medium ${activeTab === 'deworming' ? 'text-blue-600 border-b-2 border-blue-600' : 'text-gray-500'}`}
        >
          <Bug size={16} className="inline mr-1" />
          驱虫记录
        </button>
      </div>

      {loading && (
        <div className="text-center text-gray-400 py-8">加载中...</div>
      )}

      {activeTab === 'vaccination' && (
        <div className="space-y-4">
          <div className="flex justify-between items-center">
            <h2 className="text-lg font-semibold">接种记录</h2>
            <button
              onClick={() => alert('添加功能待实现')}
              className="flex items-center gap-1 bg-blue-600 text-white px-3 py-1.5 rounded-lg hover:bg-blue-700"
            >
              <Plus size={16} /> 添加记录
            </button>
          </div>
          {vaccinations.length === 0 ? (
            <div className="text-center text-gray-400 py-12">暂无疫苗记录</div>
          ) : (
            <div className="space-y-3">
              {vaccinations.map((v) => (
                <div key={v.id} className="bg-white rounded-lg shadow p-4 flex justify-between items-start">
                  <div className="space-y-1">
                    <div className="flex items-center gap-2">
                      <span className="font-semibold">{v.vaccine_name}</span>
                      <span className="text-xs bg-blue-100 text-blue-700 px-2 py-0.5 rounded">{v.vaccine_type}</span>
                      {isOverdue(v.next_due_at) && (
                        <span className="text-xs bg-red-100 text-red-700 px-2 py-0.5 rounded flex items-center gap-1">
                          <AlertTriangle size={12} /> 已到期
                        </span>
                      )}
                    </div>
                    <div className="text-sm text-gray-500">
                      接种日期: {formatDate(v.administered_at)}
                      {v.next_due_at && ` · 下次到期: ${formatDate(v.next_due_at)}`}
                    </div>
                    {v.batch_number && <div className="text-sm text-gray-400">批号: {v.batch_number}</div>}
                    {v.administered_by && <div className="text-sm text-gray-400">接种机构: {v.administered_by}</div>}
                    {v.note && <div className="text-sm text-gray-400">备注: {v.note}</div>}
                  </div>
                  <button
                    onClick={() => handleDeleteVaccination(v.id)}
                    className="text-gray-400 hover:text-red-500 p-1"
                  >
                    <Trash2 size={16} />
                  </button>
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {activeTab === 'deworming' && (
        <div className="space-y-4">
          <div className="flex justify-between items-center">
            <h2 className="text-lg font-semibold">驱虫记录</h2>
            <button
              onClick={() => alert('添加功能待实现')}
              className="flex items-center gap-1 bg-green-600 text-white px-3 py-1.5 rounded-lg hover:bg-green-700"
            >
              <Plus size={16} /> 添加记录
            </button>
          </div>
          {deworming.length === 0 ? (
            <div className="text-center text-gray-400 py-12">暂无驱虫记录</div>
          ) : (
            <div className="space-y-3">
              {deworming.map((d) => (
                <div key={d.id} className="bg-white rounded-lg shadow p-4 flex justify-between items-start">
                  <div className="space-y-1">
                    <div className="flex items-center gap-2">
                      <span className="font-semibold">{d.product_name}</span>
                      <span className="text-xs bg-green-100 text-green-700 px-2 py-0.5 rounded">{d.deworm_type}</span>
                      {isOverdue(d.next_due_at) && (
                        <span className="text-xs bg-red-100 text-red-700 px-2 py-0.5 rounded flex items-center gap-1">
                          <AlertTriangle size={12} /> 已到期
                        </span>
                      )}
                    </div>
                    <div className="text-sm text-gray-500">
                      用药日期: {formatDate(d.administered_at)}
                      {d.next_due_at && ` · 下次到期: ${formatDate(d.next_due_at)}`}
                    </div>
                    {d.dosage && <div className="text-sm text-gray-400">剂量: {d.dosage}</div>}
                    {d.note && <div className="text-sm text-gray-400">备注: {d.note}</div>}
                  </div>
                  <button
                    onClick={() => handleDeleteDeworming(d.id)}
                    className="text-gray-400 hover:text-red-500 p-1"
                  >
                    <Trash2 size={16} />
                  </button>
                </div>
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  );
}
