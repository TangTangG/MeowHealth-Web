import Reports from './pages/Reports';
import Consultation from './pages/Consultation';
import { Routes, Route } from 'react-router-dom';
import Layout from './components/Layout';
import Dashboard from './pages/Dashboard';
import Cats from './pages/Cats';

function App() {
  return (
    <Routes>
      <Route path="/" element={<Layout />}>
        <Route index element={<Dashboard />} />
        <Route path="cats" element={<Cats />} />
        <Route path="reports" element={<Reports />} />
        <Route path="consultation" element={<Consultation />} />
        <Route path="settings" element={<div className="p-4">Settings (Coming Soon)</div>} />
      </Route>
    </Routes>
  );
}

export default App;