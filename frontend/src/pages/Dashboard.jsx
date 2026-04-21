// Dashboard.jsx
import React, { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import api from '../services/api'
import '../styles/dashboard.css'

export default function Dashboard(){
  const [interviews, setInterviews] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [filter, setFilter] = useState('all') // all | analyzed | pending
  const [statuses, setStatuses] = useState({})

  useEffect(() => {
    setLoading(true)
    api.get('/interviews/')
      .then(res => setInterviews(res.data || []))
      .catch(err => setError(err.message || 'Error'))
      .finally(() => setLoading(false))
  }, [])

  async function handleRemove(id) {
    if (!window.confirm('Remove this interview run? This cannot be undone.')) return;
    try {
      await api.delete(`/interviews/${id}`)
      setInterviews(prev => prev.filter(p => p.id !== id))
      setStatuses(prev => {
        const c = { ...prev };
        delete c[id];
        return c;
      })
    } catch (e) {
      console.error('remove failed', e)
      alert('Unable to remove interview')
    }
  }

  useEffect(() => {
    // fetch analysis status for each interview (non-blocking)
    if (!interviews || interviews.length === 0) return
    const s = {}
    interviews.forEach(i => {
      api.get(`/interviews/${i.id}/analysis`).then(() => { s[i.id] = 'analyzed'; setStatuses(prev => ({...prev, [i.id]: 'analyzed'})) }).catch(()=> { s[i.id] = 'pending'; setStatuses(prev => ({...prev, [i.id]: 'pending'})) })
    })
  }, [interviews])

  return (
    <div>
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-6 mb-8">
        <div>
          <h1 className="text-4xl font-bold text-slate-900 dark:text-white mb-1">Interviews</h1>
          <p className="text-slate-600 dark:text-slate-300">Manage and review all interview assessments</p>
        </div>
        <div className="flex items-center gap-3">
          <label className="text-sm font-semibold text-slate-700 dark:text-slate-300">Filter:</label>
          <select
            value={filter}
            onChange={e=>setFilter(e.target.value)}
            className="px-4 py-2 bg-white dark:bg-slate-700 border border-slate-200 dark:border-slate-600 rounded-lg text-slate-900 dark:text-white font-medium hover:border-slate-300 dark:hover:border-slate-500 focus:outline-none focus:ring-2 focus:ring-emerald-500 focus:border-transparent shadow-sm"
          >
            <option value="all">All</option>
            <option value="analyzed">Analyzed</option>
            <option value="pending">Pending</option>
          </select>
        </div>
      </div>

      {loading && <div className="text-center py-12"><p className="text-slate-500 dark:text-slate-400 text-lg">Loading interviews...</p></div>}
      {error && <div className="bg-red-50 dark:bg-red-900/30 border border-red-200 dark:border-red-700 text-red-700 dark:text-red-300 px-6 py-4 rounded-lg font-medium">{error}</div>}

      {!loading && interviews.length === 0 && (
        <div className="bg-gradient-to-br from-blue-50 dark:from-blue-900/20 to-indigo-50 dark:to-indigo-900/20 border border-blue-200 dark:border-blue-700 rounded-2xl p-12 text-center shadow-lg">
          <div className="inline-flex items-center justify-center w-16 h-16 bg-blue-100 dark:bg-blue-900/50 rounded-full mb-4">
            <svg className="w-8 h-8 text-blue-600 dark:text-blue-400" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" /></svg>
          </div>
          <h3 className="text-2xl font-bold text-slate-900 dark:text-white mb-2">No interviews yet</h3>
          <p className="text-slate-600 dark:text-slate-300 mb-6 max-w-md mx-auto">Create your first interview to begin assessing candidates with our advanced cheating detection system.</p>
          <Link to="/schedule" className="inline-flex items-center justify-center bg-gradient-to-r from-emerald-500 to-emerald-600 text-white font-semibold px-8 py-3 rounded-lg hover:from-emerald-600 hover:to-emerald-700 transition-all duration-200 shadow-lg hover:shadow-xl">
            Schedule First Interview
          </Link>
        </div>
      )}

      {!loading && interviews.length > 0 && (
        <div className="space-y-3">
          {interviews.filter(i => {
            if(filter==='all') return true
            const st = statuses[i.id] || 'pending'
            return filter === st
          }).map(i => (
            <div key={i.id} className="bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-xl p-5 flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 hover:border-slate-300 dark:hover:border-slate-600 hover:shadow-lg transition-all duration-200">
              <div className="flex items-center gap-4 flex-1 min-w-0">
                <div className="w-12 h-12 rounded-lg bg-gradient-to-br from-blue-100 dark:from-blue-900/50 to-indigo-100 dark:to-indigo-900/50 flex items-center justify-center flex-shrink-0">
                  <svg width="24" height="24" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg"><path d="M12 2L3 6v6c0 5 3.7 9.7 9 12 5.3-2.3 9-7 9-12V6l-9-4z" fill="#4f46e5"/></svg>
                </div>
                <div className="flex-1 min-w-0">
                  <h3 className="font-semibold text-slate-900 dark:text-white truncate text-lg">{i.title || 'Interview'}</h3>
                  <p className="text-sm text-slate-500 dark:text-slate-400 truncate">{i.scheduled_at ? new Date(i.scheduled_at).toLocaleString() : 'No date'}</p>
                </div>
              </div>
              <div className="flex flex-col sm:flex-row sm:items-center gap-3 sm:gap-4 w-full sm:w-auto">
                <div className={`px-4 py-2 rounded-full text-sm font-semibold whitespace-nowrap ${
                  statuses[i.id] === 'analyzed' 
                    ? 'bg-emerald-100 dark:bg-emerald-900/50 text-emerald-700 dark:text-emerald-300' 
                    : 'bg-amber-100 dark:bg-amber-900/50 text-amber-700 dark:text-amber-300'
                }`}>
                  {statuses[i.id] === 'analyzed' ? '✓ Analyzed' : '◐ Pending'}
                </div>
                <div className="flex gap-2 flex-wrap">
                  <Link to={`/details/${i.id}`} className="px-4 py-2 bg-slate-100 dark:bg-slate-700 text-slate-700 dark:text-slate-200 font-medium rounded-lg hover:bg-slate-200 dark:hover:bg-slate-600 transition-colors duration-150 text-sm">
                    Details
                  </Link>
                  <Link to={`/run/${i.id}?start=1`} className="px-4 py-2 bg-emerald-500 text-white font-medium rounded-lg hover:bg-emerald-600 transition-colors duration-150 text-sm shadow-md hover:shadow-lg">
                    Run
                  </Link>
                  <button onClick={() => handleRemove(i.id)} className="px-4 py-2 bg-red-50 dark:bg-red-900/30 text-red-600 dark:text-red-400 font-medium rounded-lg hover:bg-red-100 dark:hover:bg-red-900/50 transition-colors duration-150 text-sm">
                    Remove
                  </button>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}