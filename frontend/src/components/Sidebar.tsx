import { Home, Cat, FileText, Settings, Stethoscope, ClipboardList, Bell, Syringe, BarChart3 } from 'lucide-react';
import { Link, useLocation } from 'react-router-dom';
import CatSelector from './CatSelector';

interface SidebarProps {
  selectedCatId: string | null;
  onSelectCat: (id: string) => void;
}

const navItems = [
  { path: '/', icon: Home, label: 'Dashboard' },
  { path: '/cats', icon: Cat, label: '猫咪管理' },
  { path: '/reports', icon: FileText, label: '化验报告' },
  { path: '/consultation', icon: Stethoscope, label: '症状咨询' },
  { path: '/health-profile', icon: ClipboardList, label: '健康档案' },
  { path: '/follow-up', icon: Bell, label: '随访提醒' },
  { path: '/preventive-care', icon: Syringe, label: '疫苗驱虫' },
  { path: '/analytics', icon: BarChart3, label: '数据洞察' },
  { path: '/settings', icon: Settings, label: '设置' },
];

export default function Sidebar({ selectedCatId, onSelectCat }: SidebarProps) {
  const location = useLocation();

  return (
    <aside className="w-64 bg-white border-r h-screen sticky top-0 flex flex-col">
      <div className="p-4 border-b">
        <h1 className="text-xl font-bold text-gray-800">MeowHealth</h1>
        <p className="text-xs text-gray-500 mt-1">猫咪健康守护</p>
      </div>
      
      <div className="p-4 border-b">
        <CatSelector selectedCatId={selectedCatId} onSelect={onSelectCat} />
      </div>

      <nav className="flex-1 px-2 py-4">
        {navItems.map(item => {
          const Icon = item.icon;
          const isActive = location.pathname === item.path;
          return (
            <Link
              key={item.path}
              to={item.path}
              className={`flex items-center gap-3 px-3 py-2.5 rounded-lg mb-1 ${
                isActive ? 'bg-blue-50 text-blue-600' : 'text-gray-600 hover:bg-gray-50'
              }`}
            >
              <Icon size={20} />
              <span className="font-medium">{item.label}</span>
            </Link>
          );
        })}
      </nav>

      <div className="p-4 border-t text-xs text-gray-400 text-center">
        MeowHealth Web v1.0
      </div>
    </aside>
  );
}