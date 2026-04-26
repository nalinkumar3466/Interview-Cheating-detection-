import React, { useEffect, useState, useRef } from 'react'
import { useParams, useNavigate } from 'react-router-dom' // Added useNavigate for disconnect
import api from '../services/api'
import CanvasPlayback from '../components/canvas/CanvasPlayback'
import CanvasGradingPanel from '../components/admin/CanvasGradingPanel'

export default function InterviewDetails(){
  const { id } = useParams()
  const navigate = useNavigate() // For redirecting on disconnect
  const [interview, setInterview] = useState(null)
  const [loading, setLoading] = useState(true)
  const [recordings, setRecordings] = useState([])
  const [analysis, setAnalysis] = useState(null)
  const [isAnalyzing, setIsAnalyzing] = useState(false)
  const [statusBadge, setStatusBadge] = useState('')
  const [videoUrl, setVideoUrl] = useState(null)
  const [canvasResponses, setCanvasResponses] = useState([])
  const [gradingCanvas, setGradingCanvas] = useState(null) // Track which canvas is being graded
  const videoRef = useRef(null)

  // --- AI Transcription & Scoring state ---
  const [transcription, setTranscription] = useState(null)
  const [isTranscribing, setIsTranscribing] = useState(false)
  const [transcriptionError, setTranscriptionError] = useState(null)

  // --- NEW STATE FOR QUESTION SKIPPING ---
  const [currentQuestionIndex, setCurrentQuestionIndex] = useState(0)
  const [unansweredTime, setUnansweredTime] = useState(0)
  const SKIP_THRESHOLD = 5 // 5 seconds threshold

  useEffect(() => {
    setLoading(true)

    api.get(`/interviews/${id}`)
      .then(res => setInterview(res.data))
      .catch(() => setInterview(null))
      .finally(() => setLoading(false))

    api.get(`/interviews/${id}/recordings`).then(res => {
      const recs = res.data || []
      setRecordings(recs)
      if (recs.length > 0) {
        const latestRecording = recs[0]
        setVideoUrl(`http://localhost:8000${latestRecording.file_url}`)
      } else {
        setVideoUrl(null)
      }
    }).catch(() => {
      setRecordings([])
      setVideoUrl(null)
    })
    
    api.get(`/interviews/${id}/canvas-responses`)
      .then(res => setCanvasResponses(res.data || []))
      .catch(() => setCanvasResponses([]))
    
    api.get(`/interviews/${id}/analysis`).then(res => { setAnalysis(res.data || null); setStatusBadge('Analyzed') }).catch(() => { setAnalysis(null); setStatusBadge('Pending') })

    // Auto-fetch existing transcription results
    api.get(`/interviews/${id}/transcription`)
      .then(res => {
        if (res.data && res.data.status === 'completed' && res.data.scored_segments?.length > 0) {
          setTranscription(res.data)
        }
      })
      .catch(() => {})
  }, [id])

  // --- NEW LOGIC: TIMER FOR SKIPPING QUESTIONS ---
  useEffect(() => {
    let timer;
    // Only run if we have an interview and questions to process
    if (interview && interview.questions && interview.questions.length > 0) {
      timer = setInterval(() => {
        setUnansweredTime(prev => {
          if (prev + 1 >= SKIP_THRESHOLD) {
            handleQuestionTimeout();
            return 0; // Reset timer after skip/disconnect
          }
          return prev + 1;
        });
      }, 1000);
    }
    return () => clearInterval(timer);
  }, [interview, currentQuestionIndex]);

  const handleQuestionTimeout = () => {
    if (interview?.questions && currentQuestionIndex < interview.questions.length - 1) {
      // Logic to skip to next question
      console.log("Question unanswered, skipping...");
      setCurrentQuestionIndex(prev => prev + 1);
      setUnansweredTime(0);
    } else {
      // No more questions, disconnect
      console.log("No more questions or threshold reached. Disconnecting...");
      handleDisconnect();
    }
  };

  const handleDisconnect = () => {
    // Navigates away to simulate disconnection
    alert("Session disconnected due to inactivity threshold.");
    navigate('/interviews/'); 
  };
  // ---------------------------------------------

  const runAnalysis = async () => { 
  try {
    setIsAnalyzing(true)
    setStatusBadge('Analyzing...')

    await api.post(
      `/interviews/analyze`,
      { interview_id: id },
      { timeout: 10000 } // 👈 10 seconds
    )

    const res = await api.get(
      `/interviews/${id}/analysis`,
      { timeout: 10000 } // 👈 10 seconds
    )

    setAnalysis(res.data)
    setStatusBadge('Analyzed')

  } catch (e) {
    console.error(e)
    setStatusBadge('Error')
    alert('Analysis failed')

  } finally {
    setIsAnalyzing(false)
  }
}

  // --- AI Transcription & Scoring ---
  const runTranscription = async () => {
    try {
      setIsTranscribing(true)
      setTranscriptionError(null)

      const res = await api.post(
        `/interviews/${id}/transcribe`,
        {},
        { timeout: 120000 } // 2 min timeout for transcription
      )

      setTranscription(res.data)
    } catch (e) {
      console.error('Transcription failed:', e)
      const msg = e?.response?.data?.detail || e.message || 'Transcription failed'
      setTranscriptionError(msg)
    } finally {
      setIsTranscribing(false)
    }
  }

  // --- PDF Download helpers ---
  const [downloadingGaze, setDownloadingGaze] = useState(false)
  const [downloadingTranscript, setDownloadingTranscript] = useState(false)

  const downloadPdf = async (type) => {
    const setLoading = type === 'gaze' ? setDownloadingGaze : setDownloadingTranscript
    try {
      setLoading(true)
      const endpoint = type === 'gaze'
        ? `/interviews/${id}/report/gaze-pdf`
        : `/interviews/${id}/report/transcription-pdf`
      const res = await api.get(endpoint, { responseType: 'blob', timeout: 30000 })
      const blob = new Blob([res.data], { type: 'application/pdf' })
      const url = window.URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = type === 'gaze'
        ? `gaze_report_interview_${id}.pdf`
        : `transcription_report_interview_${id}.pdf`
      document.body.appendChild(a)
      a.click()
      a.remove()
      window.URL.revokeObjectURL(url)
    } catch (e) {
      console.error('PDF download failed:', e)
      alert(e?.response?.data?.detail || 'Failed to download PDF report. Ensure data is available.')
    } finally {
      setLoading(false)
    }
  }

  const getScoreColor = (score) => {
    if (score === null || score === undefined) return 'text-slate-500'
    if (score >= 7) return 'text-emerald-600 dark:text-emerald-400'
    if (score >= 4) return 'text-amber-600 dark:text-amber-400'
    return 'text-red-600 dark:text-red-400'
  }

  const getScoreBg = (score) => {
    if (score === null || score === undefined) return 'bg-slate-100 dark:bg-slate-700'
    if (score >= 7) return 'bg-emerald-50 dark:bg-emerald-900/30'
    if (score >= 4) return 'bg-amber-50 dark:bg-amber-900/30'
    return 'bg-red-50 dark:bg-red-900/30'
  }

    const jumpTo = (seconds) => {
    if(videoRef.current){
      videoRef.current.currentTime = seconds
      videoRef.current.play()
    }
  }

  // Base URL for serving static uploads (mounted at /uploads on backend)
  const BASE_URL = api?.defaults?.baseURL || ''
  const canvasSketches = recordings.filter(r => (r?.answer_text || '').includes('canvas-sketch'))


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
                
                {/* Visual feedback for the skip timer */}
                {interview.questions && (
                   <p className="mt-2 text-sm text-amber-600 font-medium">
                     Question {currentQuestionIndex + 1} of {interview.questions.length} | Auto-skip in: {SKIP_THRESHOLD - unansweredTime}s
                   </p>
                )}
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
            {videoUrl === null ? (
              <div className="bg-slate-50 dark:bg-slate-700 rounded-lg p-8 text-center">
                <p className="text-slate-600 dark:text-slate-400 font-medium">No recording available for this interview</p>
              </div>
            ) : (
              <div className="flex justify-center items-center p-4">
                <video
                  ref={videoRef}
                  controls
                  preload="metadata"
                  className="w-full max-w-2xl rounded-xl shadow-2xl bg-black"
                  style={{ maxHeight: '480px' }}
                >
                  <source src={videoUrl} type="video/webm" />
                  <source src={videoUrl} type="video/mp4" />
                  Your browser does not support video playback.
                </video>
              </div>
            )}
          </div>

          {/* AI Transcription & Scoring */}
          <div className="bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-xl p-6 shadow-sm">
            <div className="flex items-center justify-between mb-6 pb-4 border-b border-slate-200 dark:border-slate-700">
              <h3 className="text-2xl font-bold text-black dark:text-white">🎙️ AI Transcription & Scoring</h3>
              <div className="flex items-center gap-3">
                {transcription && transcription.scored_segments && transcription.scored_segments.length > 0 && (
                  <button
                    id="download-transcription-pdf-btn"
                    onClick={() => downloadPdf('transcription')}
                    disabled={downloadingTranscript}
                    className="px-5 py-2 bg-gradient-to-r from-teal-500 to-cyan-600 text-white font-semibold rounded-lg hover:from-teal-600 hover:to-cyan-700 disabled:opacity-60 disabled:cursor-not-allowed transition-all shadow-lg hover:shadow-xl flex items-center gap-2"
                  >
                    {downloadingTranscript ? (
                      <>
                        <span className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin"></span>
                        Generating...
                      </>
                    ) : '📥 Download Transcription PDF'}
                  </button>
                )}
                <button
                  id="run-transcription-btn"
                  onClick={runTranscription}
                  disabled={isTranscribing || !videoUrl}
                  className="px-6 py-2 bg-gradient-to-r from-purple-500 to-violet-600 text-white font-semibold rounded-lg hover:from-purple-600 hover:to-violet-700 disabled:opacity-60 disabled:cursor-not-allowed transition-all shadow-lg hover:shadow-xl"
                >
                  {isTranscribing ? (
                    <span className="flex items-center gap-2">
                      <span className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin"></span>
                      Processing...
                    </span>
                  ) : '▶ Run Transcription'}
                </button>
              </div>
            </div>

            {/* Error message */}
            {transcriptionError && (
              <div className="mb-4 p-4 bg-red-50 dark:bg-red-900/30 border border-red-200 dark:border-red-700 rounded-lg">
                <p className="text-red-700 dark:text-red-300 font-medium">❌ {transcriptionError}</p>
              </div>
            )}

            {/* No video warning */}
            {!videoUrl && !isTranscribing && (
              <div className="bg-slate-50 dark:bg-slate-700 rounded-lg p-8 text-center">
                <p className="text-slate-600 dark:text-slate-400 font-medium">No recording available. Upload a video recording first to run transcription.</p>
              </div>
            )}

            {/* Loading state */}
            {isTranscribing && (
              <div className="flex flex-col items-center justify-center py-12">
                <div className="w-16 h-16 rounded-full border-4 border-purple-200 border-t-purple-500 animate-spin mb-4"></div>
                <p className="text-slate-600 dark:text-slate-400 font-medium text-lg">Extracting audio & transcribing...</p>
                <p className="text-slate-500 dark:text-slate-500 text-sm mt-2">This may take a minute or two</p>
              </div>
            )}

            {/* Results */}
            {!isTranscribing && transcription && transcription.scored_segments && transcription.scored_segments.length > 0 && (
              <div className="space-y-6">
                {/* Full transcription text */}
                {transcription.full_text && (
                  <details className="border border-slate-200 dark:border-slate-600 rounded-lg p-4 bg-slate-50 dark:bg-slate-700">
                    <summary className="cursor-pointer font-semibold text-slate-700 dark:text-slate-300">
                      📄 Full Transcription Text
                    </summary>
                    <p className="mt-3 text-slate-700 dark:text-slate-300 whitespace-pre-wrap leading-relaxed text-sm">
                      {transcription.full_text}
                    </p>
                  </details>
                )}

                {/* Scored Segments */}
                <div>
                  <h4 className="font-semibold text-lg text-slate-900 dark:text-white mb-4">Scored Q&A Segments</h4>
                  <div className="space-y-4">
                    {transcription.scored_segments.map((seg, idx) => (
                      <div
                        key={seg.id || idx}
                        className={`border border-slate-200 dark:border-slate-600 rounded-lg p-5 ${getScoreBg(seg.final_score)} transition-all hover:shadow-md`}
                      >
                        <div className="flex items-start justify-between mb-3">
                          <div className="flex items-center gap-3">
                            <span className="inline-flex items-center justify-center w-8 h-8 rounded-full bg-purple-100 dark:bg-purple-900 text-purple-700 dark:text-purple-300 font-bold text-sm flex-shrink-0">
                              {idx + 1}
                            </span>
                            <span className="text-xs font-semibold px-2 py-1 bg-purple-100 dark:bg-purple-900 text-purple-700 dark:text-purple-300 rounded-full">
                              Segment
                            </span>
                          </div>
                          {seg.final_score !== null && seg.final_score !== undefined && (
                            <div className="text-right">
                              <p className="text-xs text-slate-500 dark:text-slate-400">Score</p>
                              <p className={`text-2xl font-bold ${getScoreColor(seg.final_score)}`}>
                                {typeof seg.final_score === 'number' ? seg.final_score.toFixed(1) : seg.final_score}
                              </p>
                              <p className="text-xs text-slate-500 dark:text-slate-400">/10</p>
                            </div>
                          )}
                        </div>

                        {seg.question && (
                          <div className="mb-3">
                            <p className="text-xs font-semibold text-slate-500 dark:text-slate-400 uppercase tracking-wider mb-1">Question</p>
                            <p className="text-slate-800 dark:text-slate-200 font-medium">{seg.question}</p>
                          </div>
                        )}

                        {seg.answer && (
                          <div>
                            <p className="text-xs font-semibold text-slate-500 dark:text-slate-400 uppercase tracking-wider mb-1">Answer</p>
                            <p className="text-slate-700 dark:text-slate-300">{seg.answer}</p>
                          </div>
                        )}

                        {/* Score breakdown if available */}
                        {(seg.llm_score !== undefined || seg.rule_score !== undefined) && (
                          <div className="mt-3 pt-3 border-t border-slate-200 dark:border-slate-600 flex gap-6 text-sm">
                            {seg.llm_score !== undefined && seg.llm_score !== null && (
                              <div>
                                <span className="text-slate-500 dark:text-slate-400">LLM: </span>
                                <span className={`font-semibold ${getScoreColor(seg.llm_score)}`}>{typeof seg.llm_score === 'number' ? seg.llm_score.toFixed(1) : seg.llm_score}</span>
                              </div>
                            )}
                            {seg.rule_score !== undefined && seg.rule_score !== null && (
                              <div>
                                <span className="text-slate-500 dark:text-slate-400">Rule: </span>
                                <span className={`font-semibold ${getScoreColor(seg.rule_score)}`}>{typeof seg.rule_score === 'number' ? seg.rule_score.toFixed(1) : seg.rule_score}</span>
                              </div>
                            )}
                          </div>
                        )}
                      </div>
                    ))}
                  </div>
                </div>
              </div>
            )}

            {/* No results yet state */}
            {!isTranscribing && !transcriptionError && videoUrl && (!transcription || !transcription.scored_segments?.length) && (
              <div className="bg-slate-50 dark:bg-slate-700 rounded-lg p-8 text-center">
                <p className="text-slate-600 dark:text-slate-400 font-medium">No transcription available yet. Click "Run Transcription" to start the AI pipeline.</p>
              </div>
            )}
          </div>

          {/* Canvas Responses - Separated from Gaze Analysis */}
          {canvasResponses && canvasResponses.length > 0 && (
            <div className="bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-xl p-6 shadow-sm">
              <div className="flex items-center justify-between mb-6 pb-4 border-b border-slate-200 dark:border-slate-700">
                <h3 className="text-2xl font-bold text-black dark:text-white">🎨 Canvas Drawing Assessment</h3>
                <span className="text-xs font-semibold px-3 py-1 bg-blue-100 dark:bg-blue-900 text-blue-700 dark:text-blue-300 rounded-full">
                  {canvasResponses.length} submission{canvasResponses.length !== 1 ? 's' : ''}
                </span>
              </div>
              
              <div className="space-y-8">
                {canvasResponses.map((response, idx) => {
                  const questionText = interview?.questions?.find(q => q.id === response.question_id)?.text || `Question ${response.question_id}`;
                  const metadata = response.session_metadata || response.metadata || {};
                  const isGraded = response.structure_score !== null && response.clarity_score !== null && response.completeness_score !== null;
                  
                  return (
                  <div key={response.id} className="border-2 border-blue-200 dark:border-blue-700 rounded-lg p-6 bg-gradient-to-br from-blue-50 to-slate-50 dark:from-slate-700 dark:to-slate-800">
                    {/* Header with question and submission info */}
                    <div className="mb-4">
                      <h4 className="text-lg font-semibold text-slate-900 dark:text-white mb-2">
                        📋 {questionText}
                      </h4>
                      <p className="text-xs text-slate-500 dark:text-slate-400">
                        Submitted: {new Date(response.created_at).toLocaleString()}
                      </p>
                                        </div>
                    {/* Metadata Bar */}

                    <div className="flex gap-6 mb-6 p-3 bg-white dark:bg-slate-600 rounded-lg border border-slate-200 dark:border-slate-500">
                      {metadata.strokeCount !== undefined && (
                        <div>
                          <p className="text-xs text-slate-500 dark:text-slate-400">Strokes</p>
                          <p className="text-lg font-bold text-slate-900 dark:text-white">{metadata.strokeCount}</p>
                        </div>
                      )}
                      {metadata.duration !== undefined && (
                        <div>
                          <p className="text-xs text-slate-500 dark:text-slate-400">Duration</p>
                          <p className="text-lg font-bold text-slate-900 dark:text-white">{metadata.duration}s</p>
                        </div>
                      )}
                      {isGraded && (
                        <div className="ml-auto">
                          <p className="text-xs text-slate-500 dark:text-slate-400">Overall Score</p>
                          <p className="text-2xl font-bold text-green-600 dark:text-green-400">{response.overall_score?.toFixed(1)}/5</p>
                        </div>
                      )}
                      {!isGraded && (
                        <div className="ml-auto">
                          <span className="text-xs font-semibold px-3 py-1 bg-amber-100 dark:bg-amber-900 text-amber-700 dark:text-amber-300 rounded">
                            ⏳ Pending Grade
                          </span>
                        </div>
                      )}
                    </div>

                    {/* Final Drawing Image */}
                    {response.final_image_base64 && (
                      <div className="mb-6">
                        <h5 className="text-sm font-semibold text-slate-800 dark:text-slate-200 mb-3">Final Drawing Submission</h5>
                        <div className="border border-slate-300 dark:border-slate-500 rounded-lg overflow-hidden bg-white">
                          <img 
                            src={response.final_image_base64} 
                            alt="Canvas drawing submission" 
                            className="w-full rounded"
                            style={{ maxHeight: '500px', objectFit: 'contain', backgroundColor: '#fff' }}
                          />
                        </div>
                      </div>
                    )}

                    {/* Drawing Replay */}
                    {response.strokes_json && response.strokes_json.length > 0 && (
                      <div className="mb-6">
                        <h5 className="text-sm font-semibold text-slate-800 dark:text-slate-200 mb-3">Drawing Replay (Optional)</h5>
                        <details className="border border-slate-300 dark:border-slate-500 rounded-lg p-3 bg-white dark:bg-slate-700">
                          <summary className="cursor-pointer font-medium text-slate-700 dark:text-slate-300">
                            ▶️ Click to view step-by-step replay
                          </summary>
                          <div className="mt-4">
                            <CanvasPlayback 
                              strokes={response.strokes_json} 
                              metadata={metadata}
                            />
                          </div>
                        </details>
                      </div>
                    )}

                    {/* Grading Section */}
                    {isGraded ? (
                      /* Show Completed Rubric */
                      <div className="bg-gradient-to-br from-green-50 to-emerald-50 dark:from-green-900/30 dark:to-emerald-900/30 border-2 border-green-300 dark:border-green-700 rounded-lg p-6 mb-6">
                        <div className="flex items-center mb-4">
                          <h5 className="text-lg font-semibold text-green-900 dark:text-green-300">✅ Assessment Complete</h5>
                        </div>
                        
                        <div className="grid grid-cols-4 gap-4 mb-4">
                          <div className="text-center p-3 bg-white dark:bg-slate-700 rounded-lg border border-green-200 dark:border-green-600">
                            <p className="text-xs text-slate-600 dark:text-slate-400 mb-1">Structure</p>
                            <p className="text-2xl font-bold text-green-700 dark:text-green-400">
                              {response.structure_score.toFixed(1)}
                            </p>
                            <p className="text-xs text-slate-500 dark:text-slate-400">/5</p>
                          </div>
                          <div className="text-center p-3 bg-white dark:bg-slate-700 rounded-lg border border-green-200 dark:border-green-600">
                            <p className="text-xs text-slate-600 dark:text-slate-400 mb-1">Clarity</p>
                            <p className="text-2xl font-bold text-green-700 dark:text-green-400">
                              {response.clarity_score.toFixed(1)}
                            </p>
                            <p className="text-xs text-slate-500 dark:text-slate-400">/5</p>
                          </div>
                          <div className="text-center p-3 bg-white dark:bg-slate-700 rounded-lg border border-green-200 dark:border-green-600">
                            <p className="text-xs text-slate-600 dark:text-slate-400 mb-1">Completeness</p>
                            <p className="text-2xl font-bold text-green-700 dark:text-green-400">
                              {response.completeness_score.toFixed(1)}
                            </p>
                            <p className="text-xs text-slate-500 dark:text-slate-400">/5</p>
                          </div>
                          <div className="text-center p-3 bg-gradient-to-br from-green-100 to-emerald-100 dark:from-green-800 dark:to-emerald-800 rounded-lg border-2 border-green-400 dark:border-green-600">
                            <p className="text-xs text-green-700 dark:text-green-300 font-semibold mb-1">OVERALL</p>
                            <p className="text-3xl font-bold text-green-700 dark:text-green-400">
                              {response.overall_score.toFixed(1)}
                            </p>
                            <p className="text-xs text-green-700 dark:text-green-300 font-semibold">/5</p>
                          </div>
                        </div>
                        
                        {response.rubric_feedback && (
                          <div className="p-3 bg-white dark:bg-slate-700 border border-green-200 dark:border-green-600 rounded">
                            <p className="text-xs font-semibold text-slate-700 dark:text-slate-300 mb-2">Grader Comments:</p>
                            <p className="text-sm text-slate-700 dark:text-slate-300 whitespace-pre-wrap">
                              {response.rubric_feedback}
                            </p>
                          </div>
                        )}
                      </div>
                    ) : (
                      /* Show Grading Panel for ungraded submissions */
                      <div className="mb-6">
                        <CanvasGradingPanel 
                          response={response} 
                          interview_id={id}
                          onUpdateGrade={(updatedResponse) => {
                            setCanvasResponses(prev =>
                              prev.map(r =>
                                r.id === updatedResponse.id ? updatedResponse : r
                              )
                            );
                          }}
                        />
                      </div>
                    )}
                  </div>
                  );
                })}
              </div>
            </div>
          )}

                    {/* Canvas Sketches saved to uploads (fallback) */}
          {canvasSketches.length > 0 && (
            <div className="bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-xl p-6 shadow-sm">
              <div className="flex items-center justify-between mb-6 pb-4 border-b border-slate-200 dark:border-slate-700">
                <h3 className="text-2xl font-bold text-black dark:text-white">🖼️ Canvas Sketch Submissions</h3>
                <span className="text-xs font-semibold px-3 py-1 bg-emerald-100 dark:bg-emerald-900 text-emerald-700 dark:text-emerald-300 rounded-full">
                  {canvasSketches.length}
                </span>
              </div>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                {canvasSketches.map((s) => (
                  <div key={s.id} className="border border-slate-200 dark:border-slate-600 rounded-lg overflow-hidden bg-white dark:bg-slate-700">
                    <div className="p-3 text-xs text-slate-600 dark:text-slate-300 flex items-center justify-between">
                      <span>Sketch</span>
                      <span>{s.created_at ? new Date(s.created_at).toLocaleString() : ''}</span>
                    </div>
                    <img
                      src={`${BASE_URL || ''}${s.file_url || ''}`}
                      alt="Canvas sketch"
                      className="w-full"
                      style={{ maxHeight: '520px', objectFit: 'contain', backgroundColor: '#fff' }}
                      loading="lazy"
                    />
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Analysis */}
          <div className="bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-xl p-6 shadow-sm">

            <div className="flex items-center justify-between mb-6 pb-4 border-b border-slate-200 dark:border-slate-700">
              <h3 className="text-2xl font-bold text-black dark:text-white">🔍 Analysis</h3>
              <div className="flex items-center gap-3">
                {analysis && (
                  <button
                    id="download-gaze-pdf-btn"
                    onClick={() => downloadPdf('gaze')}
                    disabled={downloadingGaze}
                    className="px-5 py-2 bg-gradient-to-r from-teal-500 to-cyan-600 text-white font-semibold rounded-lg hover:from-teal-600 hover:to-cyan-700 disabled:opacity-60 disabled:cursor-not-allowed transition-all shadow-lg hover:shadow-xl flex items-center gap-2"
                  >
                    {downloadingGaze ? (
                      <>
                        <span className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin"></span>
                        Generating...
                      </>
                    ) : '📥 Download Gaze Report PDF'}
                  </button>
                )}
                <button onClick={runAnalysis} disabled={isAnalyzing} className="px-6 py-2 bg-gradient-to-r from-indigo-500 to-indigo-600 text-white font-semibold rounded-lg hover:from-indigo-600 hover:to-indigo-700 disabled:opacity-60 transition-all shadow-lg hover:shadow-xl">
                  {isAnalyzing ? '⏳ Running...' : '▶ Run Analysis'}
                </button>
              </div>
            </div>

            {!analysis ? (
              <div className="bg-slate-50 dark:bg-slate-700 rounded-lg p-8 text-center">
                <p className="text-slate-600 dark:text-slate-400 font-medium">No analysis available. Run the analysis tool to detect suspicious events.</p>
              </div>
            ) : (
              <div className="space-y-6">
                {/* Risk Level */}
                {analysis.risk_level && (
                  <div className="p-4 bg-red-50 dark:bg-red-900/30 border border-red-200 dark:border-red-700 rounded-lg">
                    <p className="text-red-700 dark:text-red-300 font-semibold">Risk Level: {analysis.risk_level}</p>
                  </div>
                )}

                {/* Event Percentages */}
                {analysis.event_percentages && (
                  <div className="p-4 bg-blue-50 dark:bg-blue-900/30 border border-blue-200 dark:border-blue-700 rounded-lg">
                    <h4 className="font-semibold text-slate-900 dark:text-blue-300 mb-2">Gaze Distribution</h4>
                    <div className="grid grid-cols-2 md:grid-cols-4 gap-2 text-sm">
                      {analysis.event_percentages.map((item) => (
                        <div key={item.event_name} className="text-center">
                          <p className="font-medium">{item.event_name}</p>
                          <p>{item.percentage_in_video}%</p>
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                {/* LLM Analysis Report */}
                {analysis.analysis_report && (
                  <div className="p-4 bg-green-50 dark:bg-green-900/30 border border-green-200 dark:border-green-700 rounded-lg">
                    <h4 className="font-semibold text-slate-900 dark:text-green-300 mb-2">AI Analysis Report</h4>
                    <p className="text-slate-700 dark:text-green-200 whitespace-pre-line">{analysis.analysis_report}</p>
                  </div>
                )}

                {/* Suspicious Events */}
                <div className="p-4 bg-yellow-50 dark:bg-yellow-900/30 border border-yellow-200 dark:border-yellow-700 rounded-lg">
                  <p className="text-slate-900 dark:text-yellow-300 font-semibold">Detected {analysis.events?.length || 0} suspicious event{(analysis.events?.length || 0) !== 1 ? 's' : ''}</p>
                  {analysis.events && analysis.events.length > 0 ? (
                    <div className="space-y-2 mt-4">
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
                    <div className="mt-4 bg-emerald-50 dark:bg-emerald-900/30 border border-emerald-200 dark:border-emerald-700 rounded-lg p-4 text-center">
                      <p className="text-emerald-700 dark:text-emerald-300 font-semibold">✓ No suspicious events detected</p>
                    </div>
                  )}
                </div>
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
