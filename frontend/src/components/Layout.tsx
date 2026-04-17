import { useState } from 'react';
import { Outlet } from 'react-router-dom';
import Sidebar from './Sidebar';

export default function Layout() {
  const [selectedCatId, setSelectedCatId] = useState<string | null>(null);

  return (
    <div className="flex min-h-screen bg-gray-50">
      <Sidebar selectedCatId={selectedCatId} onSelectCat={setSelectedCatId} />
      <main className="flex-1 overflow-auto">
        <div className="p-6">
          <Outlet context={{ selectedCatId }} />
        </div>
      </main>
    </div>
  );
}