import React, { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import api from '../services/api'

export default function Dashboard(){
  const [interviews, setInterviews] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  useEffect(() => {
    setLoading(true)
    api.get('/interviews')
      .then(res => setInterviews(res.data || []))
      .catch(err => setError(err.message || 'Error'))
      .finally(() => setLoading(false))
  }, [])

  return (
    <div>
      <h2>Dashboard</h2>
      {loading && <p>Loading interviews...</p>}
      {error && <p style={{ color: 'red' }}>{error}</p>}
      {!loading && interviews.length === 0 && (
        <div>
          <p>No interviews scheduled yet.</p>
          <Link to="/schedule">Schedule an interview</Link>
        </div>
      )}
      {!loading && interviews.length > 0 && (
        <ul>
          {interviews.map(i => (
            <li key={i.id}>
              <Link to={`/details/${i.id}`}>{i.title || 'Interview'} — {i.scheduled_at}</Link>
              <Link to={`/take/${i.id}`} style={{ marginLeft: 8 }}>Take</Link>
            </li>
          ))}
        </ul>
      )}
    </div>
  )
}
