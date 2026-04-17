import { Routes, Route } from 'react-router-dom'
import Dashboard from './pages/Dashboard'
import Cats from './pages/Cats'

function App() {
  return (
    <div className="min-h-screen bg-gray-50">
      <Routes>
        <Route path="/" element={<Dashboard />} />
        <Route path="/cats" element={<Cats />} />
      </Routes>
    </div>
  )
}

export default App