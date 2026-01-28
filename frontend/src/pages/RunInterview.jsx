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
  const [answer, setAnswer] = useState("");
  const [status, setStatus] = useState("");
  const [recording, setRecording] = useState(false);
  const [uploading, setUploading] = useState(false);

  // --- REFS (I added the missing calibration refs here to stop the crash) ---
  const localPreviewRef = useRef(null);
  const previewStreamRef = useRef(null);
  const audioCtxRef = useRef(null);
  const analyserRef = useRef(null);
  const dataArrayRef = useRef(null);
  const vadIntervalRef = useRef(null);
  const lastSpokenRef = useRef(Date.now());
  const speechTriggeredRef = useRef(false);
  const speechStartTimeRef = useRef(null);
  const questionStartTimeRef = useRef(Date.now());
  const recorderRef = useRef(null);
  const segmentStartRef = useRef(null);

  // These were missing and causing your ReferenceError
  const rmsCalibrationDone = useRef(false);
  const rmsSilenceSamplesRef = useRef([]);

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
      if (previewStreamRef.current) {
        previewStreamRef.current.getTracks().forEach((t) => t.stop());
      }
    };
  }, [id]);

  useEffect(() => {
    if (!candidateMode || !autoStart) return;
    if (questions.length && !recording) {
      setTimeout(() => {
        startRecordingFlow().catch(() => {});
      }, 300);
    }
  }, [candidateMode, autoStart, questions, recording]);

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
        console.warn("preview start failed", err);
      }
    }
    startPreview();
    return () => { mounted = false; };
  }, []);

  async function startRecordingFlow() {
    setStatus("Requesting media...");
    try {
      const webcam = await navigator.mediaDevices.getUserMedia({ video: { width: 640 }, audio: true });

      if (previewStreamRef.current) {
        previewStreamRef.current.getTracks().forEach((t) => t.stop());
      }

      previewStreamRef.current = webcam;
      if (localPreviewRef.current) {
        localPreviewRef.current.srcObject = webcam;
        localPreviewRef.current.play().catch(() => {});
      }

      const AudioContext = window.AudioContext || window.webkitAudioContext;
      const audioCtx = new AudioContext();
      audioCtxRef.current = audioCtx;
      const src = audioCtx.createMediaStreamSource(webcam);
      const analyser = audioCtx.createAnalyser();
      analyser.fftSize = 2048;
      analyserRef.current = analyser;
      src.connect(analyser);

      const dataArray = new Float32Array(analyser.fftSize);
      dataArrayRef.current = dataArray;

      // Reset Calibration State
      rmsCalibrationDone.current = false;
      rmsSilenceSamplesRef.current = [];
      speechStartTimeRef.current = null;
      speechTriggeredRef.current = false;
      const startCalTime = Date.now();
      let thresholdDb = -45;

      vadIntervalRef.current = setInterval(() => {
  try {
    if (ttsPlaying) {
      console.log("📢 TTS still playing, skipping VAD check");
      speechStartTimeRef.current = null;
      speechTriggeredRef.current = false;
      return;
    }

    analyser.getFloatTimeDomainData(dataArray);

    let sum = 0;
    for (let i = 0; i < dataArray.length; i++) sum += dataArray[i] * dataArray[i];
    const rms = Math.sqrt(sum / dataArray.length) || 1e-12;
    const db = 20 * Math.log10(rms);

    const now = Date.now();

    // Calibration Logic
    if (!rmsCalibrationDone.current) {
      if (now - startCalTime < 1500) {
        rmsSilenceSamplesRef.current.push(db);
        return;
      } else {
        const avg = rmsSilenceSamplesRef.current.reduce((a, b) => a + b, 0) / rmsSilenceSamplesRef.current.length;
        thresholdDb = Math.min(avg + 10, -42);
        rmsCalibrationDone.current = true;
        console.log("✅ VAD Calibrated. Threshold:", thresholdDb);
      }
    }

    window.dispatchEvent(new CustomEvent("vad-db", { detail: { db } }));

    // ---- SPEECH BASED AUTO SKIP (AFTER 5 SECONDS OF SPEECH ABOVE THRESHOLD) ----

    if (db > thresholdDb) {
      // speech detected above threshold
      if (speechStartTimeRef.current === null) {
        speechStartTimeRef.current = now;
        console.log("🎤 Speech started above threshold");
      }

      const speechDuration = now - speechStartTimeRef.current;
      console.log("⏱️ Speech above threshold:", speechDuration, "ms");

      if (!speechTriggeredRef.current && speechDuration >= 5000) {
        speechTriggeredRef.current = true;
        console.warn("⚡ Speech 5s above threshold -> auto skip - Calling handleSubmitAndNext()");
        handleSubmitAndNext();
      }
    } else {
      // below threshold (silence or low speech)
      speechStartTimeRef.current = null;
      speechTriggeredRef.current = false;
    }

  } catch (err) {
    console.error("VAD sample err", err);
  }
}, 100);

      startContinuousRecorder(webcam);
      setRecording(true);
      setStatus("Recording");
    } catch (err) {
      console.error(err);
      setStatus("Media Error");
    }
  }

  function startContinuousRecorder(stream) {
    segmentStartRef.current = Date.now();
    try {
      const recorder = new MediaRecorder(stream, { mimeType: "video/webm; codecs=vp9" });
      recorderRef.current = recorder;
      recorder.ondataavailable = async (ev) => {
        if (!ev.data || ev.data.size === 0) return;
        setUploading(true);
        const fd = new FormData();
        fd.append("file", ev.data, `rec_${Date.now()}.webm`);
        fd.append("interview_id", id);
        const path = candidateMode ? `/candidate/interviews/${id}/complete` : `/interviews/${id}/complete`;
        const headers = candidateMode ? { 'X-Candidate-Token': candidateToken } : {};
        await api.post(path, fd, { headers }).catch(console.error);
        setUploading(false);
      };
      recorder.start();
    } catch (e) { console.error(e); }
  }

  function stopRecording() {
    if (vadIntervalRef.current) clearInterval(vadIntervalRef.current);
    if (audioCtxRef.current) audioCtxRef.current.close().catch(() => {});
    if (recorderRef.current && recorderRef.current.state === "recording") recorderRef.current.stop();
    setRecording(false);
    setStatus("Stopped");
  }

  function handleSubmitAndNext() {
    if (!questions.length) return;

    console.log(`📤 Submitting answer for question ${index + 1}/${questions.length}`);

    const path = candidateMode ? `/candidate/interviews/${id}/answer` : `/interviews/${id}/answer`;
    const headers = candidateMode ? { 'X-Candidate-Token': candidateToken } : {};
    const q = questions[index];

    // Submit current answer immediately
    if (q) {
      api.post(path, new URLSearchParams({ question_id: q.id, answer }), { headers }).catch(() => {});
    }

    // Clear answer state
    setAnswer("");

    // Reset speech tracking refs
    speechStartTimeRef.current = null;
    speechTriggeredRef.current = false;

    // Check if this is the last question
    if (index >= questions.length - 1) {
      // Last question - finish interview
      console.log("🏁 Last question complete - finishing interview");
      stopRecording();
      const finishPath = candidateMode
        ? `/candidate/interviews/${id}/finish`
        : `/interviews/${id}/finish`;
      api.post(finishPath, null, { headers }).catch(() => {});
      setStatus("Complete");
      setTimeout(() => navigate("/"), 1000);
    } else {
      // Advance to next question immediately
      const nextIndex = index + 1;
      console.log(`✅ ADVANCING: Question ${index + 1} → Question ${nextIndex + 1}`);
      setIndex(nextIndex);
    }
  }

  const [dbValue, setDbValue] = useState(-100);
  const [ttsPlaying, setTtsPlaying] = useState(false);
  const synthRef = useRef(window.speechSynthesis || null);
  const location = useLocation();
  const urlParams = new URLSearchParams(location.search);
  const [preStartActive, setPreStartActive] = useState(urlParams.get('start') === 'true' || urlParams.get('start') === '1');
  const [preStartSeconds, setPreStartSeconds] = useState(preStartActive ? 10 : 0);

  useEffect(() => {
  speechStartTimeRef.current = null;
  speechTriggeredRef.current = false;
}, [index]);

  useEffect(() => {
    const onDb = (e) => setDbValue(e.detail.db);
    window.addEventListener("vad-db", onDb);
    return () => window.removeEventListener("vad-db", onDb);
  }, []);

  useEffect(() => {
    if (questions[index] && recording) speakQuestion(questions[index].text);
  }, [index, questions, recording]);

  // Debug: Monitor index changes
  useEffect(() => {
    if (index > 0) {
      console.log(`✅ QUESTION ADVANCED: Now on question ${index + 1} of ${questions.length}`);
    }
  }, [index]);

  useEffect(() => {
    if (!preStartActive) return;
    const t = setInterval(() => {
      setPreStartSeconds((s) => {
        if (s <= 1) {
          clearInterval(t);
          setPreStartActive(false);
          startRecordingFlow();
          return 0;
        }
        return s - 1;
      });
    }, 1000);
    return () => clearInterval(t);
  }, [preStartActive]);

  function speakQuestion(text) {
    if (!synthRef.current) return;
    synthRef.current.cancel();
    const u = new SpeechSynthesisUtterance(text);
    u.onend = () => setTtsPlaying(false);
    synthRef.current.speak(u);
    setTtsPlaying(true);
  }

  if (!questions.length) return <div className="runner-root">Loading...</div>;

  const q = questions[index];

  return (
    <div className="runner-root">
      {preStartActive && (
        <div className="prestart-overlay">
          <div className="prestart-card">
            <div className="prestart-title">Interview starting in</div>
            <div className="prestart-seconds">{preStartSeconds}</div>
          </div>
        </div>
      )}
      <div className="runner-inner row-layout">
        <div className="question-palette">
          <div className="palette-card">
            <div className="artwork-sphere"><BotSpeaker speaking={recording || ttsPlaying} /></div>
            <div className="palette-text">
              <div className="q-meta">Question {index + 1} of {questions.length}</div>
              <div className="q-body">{q.text}</div>
            </div>
          </div>
        </div>

        <div className="live-column">
          <div className="live-card">
            <div className="live-frame"><video ref={localPreviewRef} className="camera-frame" muted playsInline /></div>
            <div className="decibel-indicator">
              <div className="decibel-bar"><div className="decibel-level" style={{ width: `${Math.min(100, Math.max(0, ((dbValue + 120) / 120) * 100))}%` }} /></div>
              <div className="decibel-value">{dbValue.toFixed(1)} dBFS</div>
            </div>
          </div>
          <div className="controls-row">
            <button className="btn-primary" onClick={() => handleSubmitAndNext()}>Skip</button>
            <button className="btn-secondary" onClick={() => { stopRecording(); navigate('/'); }}>Disconnect</button>
          </div>
        </div>
      </div>
    </div>
  );
}
