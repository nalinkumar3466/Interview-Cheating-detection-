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
    api.get('/interviews')
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
    <div className="dashboard-root">
      <div className="dashboard-header">
        <h2>Interviews</h2>
        <div className="dashboard-controls">
          <label>Filter:</label>
          <select value={filter} onChange={e=>setFilter(e.target.value)}>
            <option value="all">All</option>
            <option value="analyzed">Analyzed</option>
            <option value="pending">Pending</option>
          </select>
        </div>
      </div>

      {loading && <div className="muted">Loading interviews...</div>}
      {error && <div className="error">{error}</div>}

      {!loading && interviews.length === 0 && (
        <div className="empty-state">
          <div className="empty-title">No runs yet</div>
          <div className="empty-desc">There are no interview runs available. Schedule a new interview to get started.</div>
          <Link to="/schedule" className="btn-primary">Schedule an interview</Link>
        </div>
      )}

      {!loading && interviews.length > 0 && (
        <div className="cards-grid list-mode">
          {interviews.filter(i => {
            if(filter==='all') return true
            const st = statuses[i.id] || 'pending'
            return filter === st
          }).map(i => (
            <div key={i.id} className="interview-card">
              <div className="card-left">
                <div className="card-icon" aria-hidden>
                  <svg width="28" height="28" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg"><path d="M12 2L3 6v6c0 5 3.7 9.7 9 12 5.3-2.3 9-7 9-12V6l-9-4z" fill="#5b6cff"/></svg>
                </div>
                <div>
                  <div className="card-title">{i.title || 'Interview'}</div>
                  <div className="card-meta">{i.scheduled_at ? new Date(i.scheduled_at).toLocaleString() : ''}</div>
                </div>
              </div>
              <div className="card-right">
                <div className={`status-badge ${statuses[i.id] === 'analyzed' ? 'good' : 'pending'}`}>{statuses[i.id] === 'analyzed' ? 'Analyzed' : 'Pending'}</div>
                <div className="card-actions">
                  <Link to={`/details/${i.id}`} className="btn-secondary">Details</Link>
                  <Link to={`/run/${i.id}?start=1`} className="btn-primary">Run</Link>
                  <button className="btn-remove" onClick={() => handleRemove(i.id)}>Remove</button>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
