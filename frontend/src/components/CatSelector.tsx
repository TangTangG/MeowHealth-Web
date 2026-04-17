import { useState, useEffect } from 'react';
import { getCats } from '@/lib/api';
import type { Cat } from '@/types';

interface CatSelectorProps {
  selectedCatId: string | null;
  onSelect: (catId: string) => void;
}

export default function CatSelector({ selectedCatId, onSelect }: CatSelectorProps) {
  const [cats, setCats] = useState<Cat[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    getCats()
      .then(setCats)
      .finally(() => setLoading(false));
  }, []);

  if (loading) {
    return <div className="text-sm text-gray-500">加载中...</div>;
  }

  return (
    <div className="flex items-center gap-2 p-3 bg-white rounded-lg shadow-sm border">
      <span className="text-sm text-gray-500">当前猫咪:</span>
      <select
        value={selectedCatId || ''}
        onChange={(e) => onSelect(e.target.value)}
        className="px-3 py-1 border rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
      >
        <option value="">请选择</option>
        {cats.map(cat => (
          <option key={cat.id} value={cat.id}>{cat.name}</option>
        ))}
      </select>
    </div>
  );
}