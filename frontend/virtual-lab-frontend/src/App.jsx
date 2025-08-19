import { BrowserRouter as Router, Routes, Route } from 'react-router-dom'
import { Toaster } from 'sonner'
import Navbar from './components/Navbar'
import Dashboard from './pages/Dashboard'
import CreateLab from './pages/CreateLab'
import LabDetails from './pages/LabDetails'
import VMDetails from './pages/VMDetails'
import './App.css'

function App() {
  return (
    <Router>
      <div className="min-h-screen bg-background">
        <Navbar />
        <main className="container mx-auto px-4 py-8">
          <Routes>
            <Route path="/" element={<Dashboard />} />
            <Route path="/create-lab" element={<CreateLab />} />
            <Route path="/labs/:labId" element={<LabDetails />} />
            <Route path="/vms/:vmId" element={<VMDetails />} />
          </Routes>
        </main>
        <Toaster />
      </div>
    </Router>
  )
}

export default App
