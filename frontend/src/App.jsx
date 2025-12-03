import React from 'react'
import { Routes, Route, Link } from 'react-router-dom'
import Dashboard from './pages/Dashboard'
import ScheduleInterview from './pages/Scheduleinter'
import TakeInterview from './pages/Takeinter'
import InterviewDetails from './pages/InterviewDetails'

export default function App(){
  return (
    <div>
      <nav style={{ padding: '8px', background: '#2d3748', color: 'white' }}>
        <div style={{ display: 'flex', alignItems: 'center', maxWidth: 1000, margin: '0 auto' }}>
          <div style={{ flex: 1 }}><strong>Berribot</strong></div>
          <div>
            <Link to="/" style={{ color: 'white', marginRight: 12 }}>Dashboard</Link>
            <Link to="/schedule" style={{ color: 'white' }}>Schedule Interview</Link>
          </div>
        </div>
      </nav>
      <main style={{ padding: '1rem', maxWidth: 1000, margin: '0 auto' }}>
        <Routes>
          <Route path="/" element={<Dashboard />} />
          <Route path="/schedule" element={<ScheduleInterview />} />
          <Route path="/take/:id" element={<TakeInterview />} />
          <Route path="/details/:id" element={<InterviewDetails />} />
        </Routes>
      </main>
    </div>
  )
}
