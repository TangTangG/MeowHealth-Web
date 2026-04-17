import { useState, useEffect } from 'react';
import { Plus, Trash2 } from 'lucide-react';
import { getCats, createCat, deleteCat } from '@/lib/api';
import type { Cat, CatCreate } from '@/types';

export default function Cats() {
  const [cats, setCats] = useState<Cat[]>([]);
  const [loading, setLoading] = useState(false);
  const [showAddForm, setShowAddForm] = useState(false);
  const [newCat, setNewCat] = useState<CatCreate>({
    name: '',
    breed: '',
    birthday: '',
    gender: 'male',
    is_neutered: false,
  });

  const loadCats = async () => {
    setLoading(true);
    try {
      const data = await getCats();
      setCats(data);
    } catch (error) {
      console.error('Failed to load cats:', error);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadCats();
  }, []);

  const handleAddCat = async () => {
    if (!newCat.name || !newCat.breed || !newCat.birthday) return;
    try {
      await createCat({
        ...newCat,
        birthday: new Date(newCat.birthday).toISOString(),
      });
      setShowAddForm(false);
      setNewCat({ name: '', breed: '', birthday: '', gender: 'male', is_neutered: false });
      loadCats();
    } catch (error) {
      console.error('Failed to add cat:', error);
    }
  };

  const handleDeleteCat = async (id: string) => {
    if (!confirm('确定要删除这只猫咪吗？所有相关数据也会被删除。')) return;
    try {
      await deleteCat(id);
      loadCats();
    } catch (error) {
      console.error('Failed to delete cat:', error);
    }
  };

  return (
    <div>
      <div className="flex justify-between items-center mb-6">
        <div>
          <h2 className="text-2xl font-bold text-gray-800">猫咪管理</h2>
          <p className="text-gray-500">管理你的猫咪档案</p>
        </div>
        <button
          onClick={() => setShowAddForm(true)}
          className="flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
        >
          <Plus size={20} />
          添加猫咪
        </button>
      </div>

      {showAddForm && (
        <div className="mb-6 p-4 bg-white rounded-lg shadow-sm border">
          <h3 className="font-semibold mb-4">添加新猫咪</h3>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <input
              type="text"
              placeholder="名字 *"
              value={newCat.name}
              onChange={(e) => setNewCat({ ...newCat, name: e.target.value })}
              className="px-3 py-2 border rounded"
            />
            <input
              type="text"
              placeholder="品种 *"
              value={newCat.breed}
              onChange={(e) => setNewCat({ ...newCat, breed: e.target.value })}
              className="px-3 py-2 border rounded"
            />
            <input
              type="date"
              placeholder="生日 *"
              value={newCat.birthday}
              onChange={(e) => setNewCat({ ...newCat, birthday: e.target.value })}
              className="px-3 py-2 border rounded"
            />
            <select
              value={newCat.gender}
              onChange={(e) => setNewCat({ ...newCat, gender: e.target.value })}
              className="px-3 py-2 border rounded"
            >
              <option value="male">公</option>
              <option value="female">母</option>
            </select>
          </div>
          <div className="flex items-center gap-2 mt-4">
            <input
              type="checkbox"
              id="is_neutered"
              checked={newCat.is_neutered}
              onChange={(e) => setNewCat({ ...newCat, is_neutered: e.target.checked })}
            />
            <label htmlFor="is_neutered">已绝育</label>
          </div>
          <div className="flex gap-2 mt-4">
            <button
              onClick={handleAddCat}
              className="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700"
            >
              保存
            </button>
            <button
              onClick={() => setShowAddForm(false)}
              className="px-4 py-2 text-gray-600 hover:bg-gray-100 rounded"
            >
              取消
            </button>
          </div>
        </div>
      )}

      {loading ? (
        <div className="text-center py-8 text-gray-400">加载中...</div>
      ) : cats.length === 0 ? (
        <div className="text-center py-8 text-gray-400">
          还没有猫咪，点击上方按钮添加一只吧！
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {cats.map(cat => (
            <div key={cat.id} className="bg-white rounded-lg p-4 shadow-sm border">
              <div className="flex justify-between items-start">
                <div>
                  <h3 className="font-semibold text-lg">{cat.name}</h3>
                  <p className="text-sm text-gray-500">{cat.breed}</p>
                  <p className="text-sm text-gray-400 mt-1">
                    {new Date(cat.birthday).toLocaleDateString('zh-CN')} 出生
                  </p>
                  <div className="flex gap-2 mt-2">
                    <span className="text-xs px-2 py-1 bg-gray-100 rounded">
                      {cat.gender === 'male' ? '公' : '母'}
                    </span>
                    {cat.is_neutered && (
                      <span className="text-xs px-2 py-1 bg-blue-100 text-blue-600 rounded">
                        已绝育
                      </span>
                    )}
                  </div>
                </div>
                <button
                  onClick={() => handleDeleteCat(cat.id)}
                  className="p-2 text-red-600 hover:bg-red-50 rounded"
                >
                  <Trash2 size={16} />
                </button>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}