import React, { useEffect, useState } from 'react'
import { useParams } from 'react-router-dom'
import api from '../services/api'
import RunInterview from './RunInterview'
import AccessDenied from './AccessDenied'
import useAntiCheat from '../hooks/useAntiCheat'

// CandidateInterview: validates a token with backend and, if valid,
// renders the interview UI in an isolated candidate-only mode.
export default function CandidateInterview(){
  const { token } = useParams()
  const [status, setStatus] = useState('Validating token...')
  const [valid, setValid] = useState(false)
  const [interviewId, setInterviewId] = useState(null)

  useEffect(() => {
    let mounted = true
    async function validate(){
      try {
        // backend should validate token and return only minimal info
        const res = await api.get(`/candidate/validate/${encodeURIComponent(token)}`)
        if (!mounted) return
        const data = res.data || {}
        if (data && data.valid && data.interview_id) {
          setInterviewId(String(data.interview_id))
          setValid(true)
          setStatus('Token valid — loading interview')
        } else {
          setValid(false)
          setStatus('Access denied')
        }
      } catch (err) {
        console.warn('token validation failed', err)
        setValid(false)
        setStatus('Access denied')
      }
    }
    validate()
    return () => { mounted = false }
  }, [token])

  // start anti-cheat hook only when valid
  useAntiCheat({ token, interviewId, enabled: valid })

  if (!valid) {
    return <AccessDenied message={status} />
  }

  // Render RunInterview in isolated mode. This mounts only the interview
  // UI and passes the token so back-end endpoints can further authorize.
  return (
    <div style={{ height: '100vh', background: '#f6fbfb' }}>
      <RunInterview candidateMode={true} candidateToken={token} interviewIdProp={interviewId} autoStart={true} />
    </div>
  )
}
