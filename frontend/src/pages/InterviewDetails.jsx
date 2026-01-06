import React, { useEffect, useState, useRef } from 'react'
import { useParams } from 'react-router-dom'
import api from '../services/api'

export default function InterviewDetails(){
  const { id } = useParams()
  const [interview, setInterview] = useState(null)
  const [loading, setLoading] = useState(true)
  const [recordings, setRecordings] = useState([])
  const [analysis, setAnalysis] = useState(null)
  const [isAnalyzing, setIsAnalyzing] = useState(false)
  const [statusBadge, setStatusBadge] = useState('')
  const videoRef = useRef(null)

  useEffect(() => {
    setLoading(true)
    api.get(`/interviews/${id}`)
      .then(res => setInterview(res.data))
      .catch(() => setInterview(null))
      .finally(() => setLoading(false))

    api.get(`/interviews/${id}/recordings`).then(res => setRecordings(res.data || [])).catch(() => setRecordings([]))
    api.get(`/interviews/${id}/analysis`).then(res => { setAnalysis(res.data || null); setStatusBadge('Analyzed') }).catch(() => { setAnalysis(null); setStatusBadge('Pending') })
  }, [id])

  const runAnalysis = async () => {
    try{
      setIsAnalyzing(true)
      setStatusBadge('Analyzing...')
      await api.post(`/interviews/${id}/analyze`)
      const res = await api.get(`/interviews/${id}/analysis`)
      setAnalysis(res.data)
      setStatusBadge('Analyzed')
    }catch(e){
      console.error(e)
      setStatusBadge('Error')
      alert('Analysis failed')
    }finally{
      setIsAnalyzing(false)
    }
  }

  const jumpTo = (seconds) => {
    if(videoRef.current){
      videoRef.current.currentTime = seconds
      videoRef.current.play()
    }
  }

  return (
    <div>
      <h2>Interview Details — {id}</h2>
      {loading && <p>Loading...</p>}

      {!loading && interview && (
        <div>
          <div style={{display:'flex', alignItems:'center', gap:12}}>
            <div>
              <p style={{margin:0, fontWeight:600}}>Title: {interview.title}</p>
              <p style={{margin:0, color:'#666'}}>Scheduled: {interview.scheduled_at}</p>
            </div>
            <div style={{marginLeft:'auto'}}>
              <span style={{padding:'4px 10px', borderRadius:8, background: statusBadge==='Analyzed' ? '#d4f8d4' : statusBadge==='Analyzing...' ? '#dbe9ff' : '#ffe6cc'}}>{statusBadge || 'Unknown'}</span>
            </div>
          </div>

          <h3>Recordings</h3>
          {recordings.length === 0 && <p>No recordings uploaded yet.</p>}
          {recordings.length > 0 && (
            <div>
              <div style={{display:'flex', gap:12, alignItems:'center'}}>
                <select onChange={e => { const r = recordings.find(x=>x.id==e.target.value); if(r) { videoRef.current.src = r.file_url; videoRef.current.play() } }}>
                  {recordings.map(r => (
                    <option key={r.id} value={r.id}>{r.created_at} — {r.file_path.split('/').slice(-1)[0]}</option>
                  ))}
                </select>

                <div>
                  <button onClick={() => { if(videoRef.current) videoRef.current.play() }}>Play</button>
                  <button onClick={() => { if(videoRef.current) videoRef.current.pause() }} style={{marginLeft:8}}>Pause</button>
                </div>
              </div>

              <div style={{marginTop:10}}>
                <video ref={videoRef} width="640" controls>
                  {recordings[0] && <source src={recordings[0].file_url} type="video/mp4" />}
                  Your browser does not support the video tag.
                </video>
              </div>
            </div>
          )}

          <div style={{marginTop:20}}>
            <button onClick={runAnalysis} disabled={isAnalyzing}>{isAnalyzing ? 'Running analysis…' : 'Run Analysis'}</button>
          </div>

          <h3>Suspicious Events</h3>
          {!analysis && <p>No analysis available.</p>}
          {analysis && analysis.events && (
            <div>
              <p>Detected events ({analysis.events.length})</p>
              <ul>
                {analysis.events.map((ev, idx) => (
                  <li key={idx} style={{marginBottom:6}}>
                    <button onClick={() => jumpTo(ev.timestamp)} style={{marginRight:8}}>{ev.timestamp}s</button>
                    <strong style={{marginRight:8}}>{ev.label}</strong>
                    <small style={{color:'#666'}}>jump to timestamp</small>
                  </li>
                ))}
              </ul>
            </div>
          )}

        </div>
      )}

      {!loading && !interview && (
        <p>Interview not found</p>
      )}
    </div>
  )
}
