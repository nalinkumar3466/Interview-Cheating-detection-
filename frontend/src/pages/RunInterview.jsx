// frontend/src/pages/RunInterview.jsx
import React, { useEffect, useRef, useState } from "react";
import api from "../services/api";
import { useParams, useNavigate } from "react-router-dom";
import "../style.css";
import "../styles/interview.css";
import BotSpeaker from '../components/BotSpeaker'
import { useLocation } from 'react-router-dom'

export default function RunInterview({ candidateMode = false, candidateToken = null, interviewIdProp = null, autoStart = false }) {
  const { id: idParam } = useParams();
  const id = interviewIdProp || idParam;
  const navigate = useNavigate();

  const [questions, setQuestions] = useState([]);
  const [index, setIndex] = useState(0);
  // answers are not collected via text box in this flow
  const [answer, setAnswer] = useState("");
  const [status, setStatus] = useState("");
  const [recording, setRecording] = useState(false);
  const [uploading, setUploading] = useState(false);

  const localPreviewRef = useRef(null);
  const previewStreamRef = useRef(null);
  const audioCtxRef = useRef(null);
  const analyserRef = useRef(null);
  const dataArrayRef = useRef(null);
  const vadIntervalRef = useRef(null);
  const rmsHistoryRef = useRef([]);
  const lastSpokenRef = useRef(Date.now());
  const silenceTriggeredRef = useRef(false);
  const recorderRef = useRef(null);
  const segmentTimerRef = useRef(null);
  const chunksRef = useRef([]);
  const tsOffsetRef = useRef(0);
  const segmentStartRef = useRef(null);

  useEffect(() => {
    let mounted = true;
    async function loadQuestions() {
      try {
        const path = candidateMode ? `/candidate/interviews/${id}/questions` : `/interviews/${id}/questions`;
        const res = await api.get(path, { headers: candidateMode ? { 'X-Candidate-Token': candidateToken } : {} });
        if (!mounted) return;
        setQuestions(res.data || []);
      } catch (e) {
        console.error(e);
        setStatus("Unable to load questions");
      }
    }
    loadQuestions();

    return () => {
      mounted = false;
      stopRecording();
      try {
        if (previewStreamRef.current) {
          previewStreamRef.current.getTracks().forEach((t) => t.stop());
          previewStreamRef.current = null;
        }
      } catch (e) {}
    };
  }, [id]);

  // If opened via candidate link, optionally auto-start the recording when ready
  useEffect(() => {
    if (!candidateMode || !autoStart) return;
    // wait until questions are loaded and not already recording
    if (questions.length && !recording) {
      // small timeout to allow UI to settle before prompting for media
      setTimeout(() => {
        startRecordingFlow().catch(() => {});
      }, 300);
    }
  }, [candidateMode, autoStart, questions, recording]);

  // show preview (video only) on mount so user sees camera prior to clicking Start
  useEffect(() => {
    let mounted = true;
    async function startPreview() {
      try {
        const s = await navigator.mediaDevices.getUserMedia({ video: { width: 640 }, audio: false });
        if (!mounted) {
          s.getTracks().forEach((t) => t.stop());
          return;
        }
        previewStreamRef.current = s;
        if (localPreviewRef.current) {
          localPreviewRef.current.srcObject = s;
          localPreviewRef.current.play().catch(() => {});
        }
      } catch (err) {
        // preview is optional; ignore failures
        console.warn("preview start failed", err);
      }
    }
    startPreview();
    return () => {
      mounted = false;
    };
  }, []);

  async function startRecordingFlow() {
    setStatus("Requesting media...");
    try {
      const webcam = await navigator.mediaDevices.getUserMedia({ video: { width: 640 }, audio: true });

      // replace the preview with the webcam+audio stream
      try {
        if (previewStreamRef.current) {
          previewStreamRef.current.getTracks().forEach((t) => t.stop());
          previewStreamRef.current = null;
        }
      } catch (e) {}

      previewStreamRef.current = webcam;
      if (localPreviewRef.current) {
        localPreviewRef.current.srcObject = webcam;
        localPreviewRef.current.play().catch(() => {});
      }

      // set up AudioContext + analyser for RMS/VAD
      try {
        if (audioCtxRef.current) {
          try {
            audioCtxRef.current.close();
          } catch (e) {}
          audioCtxRef.current = null;
        }

        const AudioContext = window.AudioContext || window.webkitAudioContext;
        const audioCtx = new AudioContext();
        audioCtxRef.current = audioCtx;

        const src = audioCtx.createMediaStreamSource(webcam);
        const analyser = audioCtx.createAnalyser();
        analyser.fftSize = 2048;
        analyser.smoothingTimeConstant = 0.0;
        analyserRef.current = analyser;
        src.connect(analyser);

        const bufferLength = analyser.fftSize;
        const dataArray = new Float32Array(bufferLength);
        dataArrayRef.current = dataArray;

        // sampling + smoothing parameters
        const smoothingWindowMs = 300; // choose 200-500ms; default 300ms
        const sampleIntervalMs = 100; // sample every 100ms
        const thresholdDb = -45; // default threshold in dBFS
        const silenceWindowMs = 5000; // 5s

        // clear history
        rmsHistoryRef.current = [];
        lastSpokenRef.current = Date.now();
        silenceTriggeredRef.current = false;

        // sample loop
        vadIntervalRef.current = setInterval(() => {
          try {
            analyser.getFloatTimeDomainData(dataArray);
            // compute instantaneous RMS
            let sum = 0;
            for (let i = 0; i < dataArray.length; i++) {
              const v = dataArray[i];
              sum += v * v;
            }
            const mean = sum / dataArray.length;
            const rms = Math.sqrt(mean) || 1e-12;
            const now = Date.now();

            // push into history and trim to smoothing window
            const h = rmsHistoryRef.current;
            h.push({ t: now, rms });
            while (h.length && now - h[0].t > smoothingWindowMs) h.shift();

            // compute mean RMS over history
            let accum = 0;
            for (let i = 0; i < h.length; i++) accum += h[i].rms * h[i].rms;
            const avgRms = Math.sqrt(accum / Math.max(1, h.length));
            const db = 20 * Math.log10(avgRms);
            // update UI (use custom event on window so we can set local state below)
            const evt = new CustomEvent("vad-db", { detail: { db, rms: avgRms, thresholdDb } });
            window.dispatchEvent(evt);

            // silence detection logic
            if (db >= thresholdDb) {
              lastSpokenRef.current = now;
              // reset trigger so future silence can trigger again
              silenceTriggeredRef.current = false;
            } else {
              // log decibel values while silent to help identify threshold
              console.debug(new Date().toISOString(), "silent-dB", db.toFixed(1));
              if (!silenceTriggeredRef.current && now - lastSpokenRef.current >= silenceWindowMs) {
                silenceTriggeredRef.current = true;
                // advance to next question (auto submit)
                console.info(new Date().toISOString(), "silence detected -> advancing question");
                handleSubmitAndNext().catch(() => {});
              }
            }
          } catch (e) {
            console.warn("VAD sample err", e);
          }
        }, sampleIntervalMs);
      } catch (e) {
        console.warn("audio ctx setup failed", e);
      }

      // record only the webcam stream (no screen)
      startContinuousRecorder(webcam);
      setRecording(true);
      setStatus("Recording");
    } catch (err) {
      console.error("media error", err);
      setStatus("Media permission denied or error");
      setRecording(false);
    }
  }

  function startSegmentedRecorder(stream) {
    // legacy segmented recorder — not used
    return;
  }

  // Continuous recorder: upload each dataavailable chunk while keeping recorder running.
  function startContinuousRecorder(stream) {
    tsOffsetRef.current = 0;
    segmentStartRef.current = Date.now();
    const options = { mimeType: "video/webm; codecs=vp9" };
    try {
      const recorder = new MediaRecorder(stream, options);
      recorderRef.current = recorder;

      recorder.ondataavailable = async (ev) => {
        try {
          if (!ev.data || ev.data.size === 0) return;
          setUploading(true);
          const now = Date.now();
          const durSec = Math.round((now - segmentStartRef.current) / 1000);
          const ts_start = tsOffsetRef.current;
          const ts_end = ts_start + durSec;

          const fd = new FormData();
          fd.append("file", ev.data, `segment_${Date.now()}.webm`);
          fd.append("ts_start", String(ts_start));
          fd.append("ts_end", String(ts_end));
          fd.append("interview_id", id);
          try {
            const path = candidateMode ? `/candidate/interviews/${id}/complete` : `/interviews/${id}/complete`;
            const headers = { "Content-Type": "multipart/form-data" };
            if (candidateMode) headers['X-Candidate-Token'] = candidateToken;
            await api.post(path, fd, { headers });
          } catch (err) {
            console.error("upload failed", err);
          }

          // advance offset and reset segment timer
          tsOffsetRef.current = ts_end;
          segmentStartRef.current = Date.now();
        } catch (e) {
          console.warn('ondataavailable upload err', e);
        } finally {
          setUploading(false);
        }
      };

      recorder.onerror = (e) => console.warn('recorder error', e);
      // request periodic dataavailable events every 12s while keeping the recorder running
      recorder.start(12_000);
    } catch (e) {
      console.warn('continuous recorder start failed', e);
    }
  }

  function stopRecording() {
    try {
      if (segmentTimerRef.current) {
        clearInterval(segmentTimerRef.current);
        segmentTimerRef.current = null;
      }
      if (vadIntervalRef.current) {
        clearInterval(vadIntervalRef.current);
        vadIntervalRef.current = null;
      }
      try {
        if (audioCtxRef.current) {
          audioCtxRef.current.close();
          audioCtxRef.current = null;
        }
      } catch (e) {}
      if (recorderRef.current && recorderRef.current.state === "recording") {
        recorderRef.current.stop();
      }
      if (previewStreamRef.current) {
        previewStreamRef.current.getTracks().forEach((t) => t.stop());
        previewStreamRef.current = null;
      }
    } catch (e) {
      console.warn(e);
    } finally {
      setRecording(false);
      setStatus("Stopped");
    }
  }

  // answers are handled at submit; no autosave UI required

  async function handleSubmitAndNext() {
    if (!questions.length) return;
    const q = questions[index];
    const path = candidateMode ? `/candidate/interviews/${id}/answer` : `/interviews/${id}/answer`;
    const headers = candidateMode ? { 'X-Candidate-Token': candidateToken } : {};
    await api.post(path, new URLSearchParams({ question_id: q.id, answer }), { headers }).catch(() => {});
    setAnswer("");
    if (index < questions.length - 1) {
      setIndex(index + 1);
      // reset VAD timing so next question doesn't immediately auto-advance
      lastSpokenRef.current = Date.now();
      silenceTriggeredRef.current = false;
    } else {
      stopRecording();
      const finishPath = candidateMode ? `/candidate/interviews/${id}/finish` : `/interviews/${id}/finish`;
      const finishHeaders = candidateMode ? { 'X-Candidate-Token': candidateToken } : {};
      await api.post(finishPath, null, { headers: finishHeaders }).catch(() => {});
      setStatus("Interview complete");
      setTimeout(() => navigate("/"), 1000);
    }
  }

  // local UI state for dB value
  const [dbValue, setDbValue] = useState(-100);
  const [secondsLeft, setSecondsLeft] = useState(10);
  // TTS state
  const [ttsPlaying, setTtsPlaying] = useState(false);
  const synthRef = useRef(window.speechSynthesis ? window.speechSynthesis : null);
  const utterRef = useRef(null);
  const location = useLocation();
  const urlParams = new URLSearchParams(location.search);
  const startFromQuery = urlParams.get('start') === '1' || urlParams.get('start') === 'true';
  const [preStartActive, setPreStartActive] = useState(startFromQuery);
  const [preStartSeconds, setPreStartSeconds] = useState(startFromQuery ? 10 : 0);
  useEffect(() => {
    function onDb(e) {
      const { db } = e.detail || {};
      if (typeof db === "number" && !Number.isNaN(db) && Number.isFinite(db)) setDbValue(db);
    }
    window.addEventListener("vad-db", onDb);
    return () => window.removeEventListener("vad-db", onDb);
  }, []);

  // speak current question when it becomes active — only when recording is active
  useEffect(() => {
    if (!questions || !questions.length) return;
    if (!recording) return;
    const cur = questions[index];
    if (cur && cur.text) speakQuestion(cur.text);
  }, [index, questions, recording]);

  // handle pre-start countdown (when navigated with ?start=1)
  useEffect(() => {
    if (!preStartActive) return;
    setPreStartSeconds(10);
    const t = setInterval(() => {
      setPreStartSeconds((s) => {
        if (s <= 1) {
          clearInterval(t);
          setPreStartActive(false);
          // start actual recording flow
          startRecordingFlow().catch(() => {});
          return 0;
        }
        return s - 1;
      });
    }, 1000);
    return () => clearInterval(t);
  }, [preStartActive]);

  function speakQuestion(text) {
    if (!synthRef.current) return;
    stopSpeech();
    try {
      const u = new SpeechSynthesisUtterance(text);
      u.rate = 1.0;
      u.onend = () => {
        setTtsPlaying(false);
      };
      utterRef.current = u;
      synthRef.current.speak(u);
      setTtsPlaying(true);
    } catch (e) {
      console.warn('TTS error', e);
      setTtsPlaying(false);
    }
  }

  function stopSpeech() {
    try {
      if (synthRef.current && synthRef.current.speaking) {
        synthRef.current.cancel();
      }
    } catch (e) {}
    utterRef.current = null;
    setTtsPlaying(false);
  }

  // per-question 10s timer (starts when recording and questions loaded)
  useEffect(() => {
    if (!questions.length || !recording) return;
    setSecondsLeft(10);
    const t = setInterval(() => {
      setSecondsLeft((s) => {
        if (s <= 1) {
          clearInterval(t);
          // auto submit and next
          handleSubmitAndNext().catch(() => {});
          return 0;
        }
        return s - 1;
      });
    }, 1000);
    return () => clearInterval(t);
    // reset timer when index changes or recording toggles
  }, [index, questions.length, recording]);

  if (!questions.length) {
    return (
      <div className="runner-root">
        <div className="runner-inner">
          <div className="runner-center">
            <h2>Interview Runner</h2>
            <div className="muted">Loading questions...</div>
            <div className="status">{status}</div>
          </div>
        </div>
      </div>
    );
  }

  const q = questions[index];

  return (
    <div className="runner-root">
      {preStartActive && (
        <div className="prestart-overlay">
          <div className="prestart-card">
            <div className="prestart-title">Interview starting in</div>
            <div className="prestart-seconds">{preStartSeconds}</div>
            <div className="prestart-sub">Please allow camera & microphone permissions</div>
          </div>
        </div>
      )}
      <div className="runner-inner row-layout">

        {/* LEFT — Question Palette (bot) */}
        <div className="question-palette">
          <div className="palette-card">
            <div className="artwork-sphere" aria-hidden="true">
              <BotSpeaker speaking={recording || ttsPlaying} />
            </div>
            <div className="palette-text">
              <div className="q-meta-row">
                <div className="q-meta">Question {index + 1} of {questions.length}</div>
                <div className="tts-controls">
                  {!ttsPlaying ? (
                    <button className="icon-btn" title="Play question" onClick={() => speakQuestion(q.text)}>
                      <svg width="16" height="16" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg"><path d="M5 3v18l15-9L5 3z" fill="currentColor"/></svg>
                    </button>
                  ) : (
                    <button className="icon-btn" title="Stop" onClick={() => stopSpeech()}>
                      <svg width="16" height="16" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg"><rect x="6" y="6" width="12" height="12" fill="currentColor"/></svg>
                    </button>
                  )}
                </div>
              </div>
              <div className="q-body">{q.text}</div>
            </div>
          </div>
        </div>

        {/* RIGHT — Live camera + answer block */}
        <div className="live-column">
          <div className="live-card">
            <div className="live-title">Live Camera</div>
            <div className="live-frame">
              <video ref={localPreviewRef} className="camera-frame" muted playsInline />
            </div>
            <div className="status-pill-row">
              <div className={`status-pill ${uploading ? 'uploading' : recording ? 'recording' : 'idle'}`}>
                {uploading ? 'Uploading' : recording ? 'Recording' : 'Idle'}
              </div>
            </div>
            <div className="decibel-indicator">
              <div className="decibel-bar" aria-hidden>
                <div className="decibel-level" style={{ width: `${Math.max(0, Math.min(100, (dbValue + 80) * (100/80)))}%` }} />
              </div>
              <div className="decibel-value">{Number.isFinite(dbValue) ? `${dbValue.toFixed(1)} dBFS` : "— dB"}</div>
            </div>
          </div>

          <div className="answer-block">
            <div className="answer-label">Answer (recorded)</div>
            <div className="answer-note muted">Responses are recorded via your camera and microphone.</div>
          </div>

          <div className="controls-row">
            <div style={{ display: 'flex', gap: 8 }}>
              <button
                className="btn-primary"
                onClick={() => {
                  // Skip: submit current answer and go to next
                  handleSubmitAndNext().catch(() => {});
                  setSecondsLeft(10);
                }}
              >
                Skip
              </button>

              <button
                className="btn-secondary"
                onClick={() => {
                  stopRecording();
                  navigate('/');
                }}
              >
                Disconnect
              </button>
            </div>
          </div>
        </div>

      </div>
    </div>
  );
}

