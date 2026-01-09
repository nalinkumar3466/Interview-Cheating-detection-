import React from 'react'
import { Routes, Route, Link, useLocation } from 'react-router-dom'
import Dashboard from './pages/Dashboard'
import ScheduleInterview from './pages/Scheduleinter'
import TakeInterview from './pages/Takeinter'
import InterviewDetails from './pages/InterviewDetails'
import RunInterview from './pages/RunInterview'
import CandidateInterview from './pages/CandidateInterview'
import ThemeToggle from './components/ThemeToggle'
import './style.css'

export default function App(){
  const location = useLocation();
  const isCandidate = location.pathname.startsWith('/candidate');

  return (
    <div className="min-h-screen bg-white dark:bg-[#05070a] text-black dark:text-white transition-colors duration-200">
      {!isCandidate && (
        <nav className="sticky top-0 z-50 bg-white dark:bg-slate-900 border-b border-slate-200 dark:border-slate-700 shadow-lg">
          <div className="max-w-7xl mx-auto px-6 py-4 flex items-center justify-between">
            <div className="flex items-center gap-4">
              <div className="w-14 h-14 rounded-full bg-gradient-to-br from-teal-400 to-emerald-500 shadow-lg flex items-center justify-center p-1">
                <img src="/berribot.png" alt="BerriBot" className="w-full h-full rounded-full object-cover" />
              </div>
              <div>
                <div className="text-2xl font-bold text-slate-900 dark:text-white tracking-tight">BerriBot</div>
                <div className="text-xs text-slate-600 dark:text-slate-300 font-medium">Interview Assessment Platform</div>
              </div>
            </div>

            <div className="flex items-center gap-8">
              <Link to="/" className="text-slate-700 dark:text-slate-300 hover:text-emerald-600 dark:hover:text-emerald-400 font-medium transition-colors duration-200 px-4 py-2 rounded-lg hover:bg-slate-100 dark:hover:bg-slate-700/50">
                Dashboard
              </Link>
              <Link to="/schedule" className="bg-gradient-to-r from-emerald-500 to-teal-500 text-white font-semibold px-6 py-2 rounded-lg hover:from-emerald-600 hover:to-teal-600 transition-all duration-200 shadow-lg hover:shadow-xl">
                Schedule Interview
              </Link>
              <ThemeToggle />
            </div>
          </div>
        </nav>
      )}

      <main className={isCandidate ? "" : "max-w-7xl mx-auto px-6 py-8"}>
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
