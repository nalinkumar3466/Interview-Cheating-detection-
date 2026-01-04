import React from 'react'
import { Routes, Route, Link, useLocation } from 'react-router-dom'
import Dashboard from './pages/Dashboard'
import ScheduleInterview from './pages/Scheduleinter'
import TakeInterview from './pages/Takeinter'
import InterviewDetails from './pages/InterviewDetails'
import RunInterview from './pages/RunInterview'
import CandidateInterview from './pages/CandidateInterview'
import './style.css'

export default function App(){
  const location = useLocation();
  const isCandidate = location.pathname.startsWith('/candidate');

  return (
    <div>
      {!isCandidate && (
        <nav className="app-nav">
          <div className="nav-inner">
            <div className="brand-left">
              <div className="brand-logo-row">
                <img src="/berribot.png" alt="BerriBot" className="brand-logo-img" />
                <div>
                  <div className="brand-title">BerriBot</div>
                  <div className="brand-sub">Cheating Detection Interview System</div>
                </div>
              </div>
            </div>

            <div className="nav-links">
              <Link to="/" className="nav-link">Dashboard</Link>
              <Link to="/schedule" className="nav-link">Schedule Interview</Link>
            </div>
          </div>
        </nav>
      )}

      <main style={{ padding: isCandidate ? '0' : '1rem', maxWidth: isCandidate ? '100%' : 1100, margin: isCandidate ? 0 : '0 auto' }}>
        <Routes>
          <Route path="/" element={<Dashboard />} />
          <Route path="/schedule" element={<ScheduleInterview />} />
          <Route path="/take/:id" element={<TakeInterview />} />
          <Route path="/details/:id" element={<InterviewDetails />} />
          <Route path="/run/:id" element={<RunInterview />} />
          <Route path="/candidate/interview/:token" element={<CandidateInterview />} />
        </Routes>
      </main>
    </div>
  )
}
