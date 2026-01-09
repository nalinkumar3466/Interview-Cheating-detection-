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
  const [videoExists, setVideoExists] = useState(null)
  const videoRef = useRef(null)

  useEffect(() => {
    setLoading(true)
    api.get(`/interviews/${id}`)
      .then(res => setInterview(res.data))
      .catch(() => setInterview(null))
      .finally(() => setLoading(false))

    // Check if video exists
    fetch(`/api/interviews/${id}/video-exists`)
      .then(res => res.json())
      .then(data => setVideoExists(data.exists))
      .catch(() => setVideoExists(false))

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
    <div className="max-w-6xl mx-auto">
      {loading && (
        <div className="flex items-center justify-center py-16">
          <div className="text-center">
            <div className="w-12 h-12 rounded-full border-4 border-emerald-200 border-t-emerald-500 animate-spin mx-auto mb-4"></div>
            <p className="text-slate-600 dark:text-slate-400 font-medium">Loading interview details...</p>
          </div>
        </div>
      )}

      {!loading && interview && (
        <div className="space-y-6">
          {/* Header */}
          <div className="bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-xl p-6 shadow-sm">
            <div className="flex items-start justify-between">
              <div>
                <h1 className="text-4xl font-bold text-black dark:text-white mb-2">{interview.title}</h1>
                <p className="text-slate-600 dark:text-slate-400 text-lg">📅 {interview.scheduled_at ? new Date(interview.scheduled_at).toLocaleString() : 'No date'}</p>
              </div>
              <div className="flex flex-col items-end gap-2">
                <span className={`px-4 py-2 rounded-full text-sm font-semibold whitespace-nowrap ${
                  statusBadge === 'Analyzed' ? 'bg-emerald-100 dark:bg-emerald-900 text-emerald-700 dark:text-emerald-300' :
                  statusBadge === 'Analyzing...' ? 'bg-blue-100 dark:bg-blue-900 text-blue-700 dark:text-blue-300' :
                  'bg-amber-100 dark:bg-amber-900 text-amber-700 dark:text-amber-300'
                }`}>
                  {statusBadge === 'Analyzed' ? '✓ Analyzed' : statusBadge === 'Analyzing...' ? '⏳ Analyzing' : '◐ Pending'}
                </span>
              </div>
            </div>
          </div>

          {/* Video Player */}
          <div className="bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-xl p-6 shadow-sm">
            <h3 className="text-2xl font-bold text-black dark:text-white mb-6 pb-4 border-b border-slate-200 dark:border-slate-700">🎬 Interview Recording</h3>
            {videoExists === null ? (
              <div className="bg-slate-50 dark:bg-slate-700 rounded-lg p-8 text-center">
                <p className="text-slate-600 dark:text-slate-400 font-medium">Checking for recording...</p>
              </div>
            ) : videoExists ? (
              <div className="flex justify-center items-center p-4">
                <video
                  controls
                  preload="metadata"
                  className="w-full max-w-2xl rounded-xl shadow-2xl bg-black"
                  style={{ maxHeight: '480px' }}
                >
                  <source src={`http://localhost:8000/uploads/${id}.mp4`} type="video/mp4" />
                  Your browser does not support video playback.
                </video>
              </div>
            ) : (
              <div className="bg-slate-50 dark:bg-slate-700 rounded-lg p-8 text-center">
                <p className="text-slate-600 dark:text-slate-400 font-medium">No recording uploaded for this interview</p>
              </div>
            )}
          </div>

          {/* Analysis */}
          <div className="bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-xl p-6 shadow-sm">
            <div className="flex items-center justify-between mb-6 pb-4 border-b border-slate-200 dark:border-slate-700">
              <h3 className="text-2xl font-bold text-black dark:text-white">🔍 Analysis</h3>
              <button onClick={runAnalysis} disabled={isAnalyzing} className="px-6 py-2 bg-gradient-to-r from-indigo-500 to-indigo-600 text-white font-semibold rounded-lg hover:from-indigo-600 hover:to-indigo-700 disabled:opacity-60 transition-all shadow-lg hover:shadow-xl">
                {isAnalyzing ? '⏳ Running...' : '▶ Run Analysis'}
              </button>
            </div>

            {!analysis ? (
              <div className="bg-slate-50 dark:bg-slate-700 rounded-lg p-8 text-center">
                <p className="text-slate-600 dark:text-slate-400 font-medium">No analysis available. Run the analysis tool to detect suspicious events.</p>
              </div>
            ) : (
              <div>
                <div className="mb-4 p-4 bg-blue-50 dark:bg-blue-900/30 border border-blue-200 dark:border-blue-700 rounded-lg">
                  <p className="text-slate-900 dark:text-blue-300 font-semibold">Detected {analysis.events?.length || 0} suspicious event{(analysis.events?.length || 0) !== 1 ? 's' : ''}</p>
                </div>
                {analysis.events && analysis.events.length > 0 ? (
                  <div className="space-y-2">
                    {analysis.events.map((ev, idx) => (
                      <div key={idx} className="flex items-center justify-between p-4 bg-slate-50 dark:bg-slate-700 border border-slate-200 dark:border-slate-600 rounded-lg hover:bg-orange-50 dark:hover:bg-orange-900/20 transition-colors group">
                        <div className="flex items-center gap-4 flex-1">
                          <span className="inline-flex items-center justify-center w-8 h-8 rounded-full bg-orange-100 dark:bg-orange-900 text-orange-700 dark:text-orange-300 font-semibold text-sm flex-shrink-0">{idx + 1}</span>
                          <div>
                            <p className="font-semibold text-black dark:text-white">{ev.label}</p>
                            <p className="text-xs text-slate-500 dark:text-slate-400 mt-1">Timestamp: {ev.timestamp}s</p>
                          </div>
                        </div>
                        <button onClick={() => jumpTo(ev.timestamp)} className="px-4 py-2 bg-orange-500 text-white font-medium rounded-lg hover:bg-orange-600 transition-colors shadow-md flex-shrink-0">
                          Jump to {ev.timestamp}s
                        </button>
                      </div>
                    ))}
                  </div>
                ) : (
                  <div className="bg-emerald-50 dark:bg-emerald-900/30 border border-emerald-200 dark:border-emerald-700 rounded-lg p-4 text-center">
                    <p className="text-emerald-700 dark:text-emerald-300 font-semibold">✓ No suspicious events detected</p>
                  </div>
                )}
              </div>
            )}
          </div>
        </div>
      )}

      {!loading && !interview && (
        <div className="bg-red-50 dark:bg-red-900/30 border border-red-200 dark:border-red-700 rounded-lg p-8 text-center">
          <p className="text-red-700 dark:text-red-300 font-semibold text-lg">Interview not found</p>
        </div>
      )}
    </div>
  )
}
