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

  // --- Live-state refs (avoid stale closures inside setInterval/VAD callbacks) ---
  const questionsRef = useRef([]);
  const indexRef = useRef(0);
  const answerRef = useRef("");
  const recordingRef = useRef(false);
  const ttsPlayingRef = useRef(false);
  const submitInProgressRef = useRef(false);

  // --- REFS ---
  const localPreviewRef = useRef(null);
  const previewStreamRef = useRef(null);
  const audioCtxRef = useRef(null);
  const analyserRef = useRef(null);
  const dataArrayRef = useRef(null);
  const vadIntervalRef = useRef(null);
  const recorderRef = useRef(null);
  const segmentStartRef = useRef(null);

  // VAD & Skip Detection Refs
  const skipTriggeredRef = useRef(false);
  const idleStateRef = useRef({ type: null, startTime: null });
  // Detect “flatline” input: db stays ~same for 5s continuously
  const stableDbStateRef = useRef({ startTime: null, lastDb: null, lastLoggedSecond: -1 });
  const rmsCalibrationDone = useRef(false);
  const rmsSilenceSamplesRef = useRef([]);
  const currentDbRef = useRef(-90);

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

  // Keep refs in sync with state
  useEffect(() => { questionsRef.current = questions; }, [questions]);
  useEffect(() => { indexRef.current = index; }, [index]);
  useEffect(() => { answerRef.current = answer; }, [answer]);
  useEffect(() => { recordingRef.current = recording; }, [recording]);

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

      // Reset Calibration & Skip State
      rmsCalibrationDone.current = false;
      rmsSilenceSamplesRef.current = [];
      skipTriggeredRef.current = false;
      idleStateRef.current = { type: null, startTime: null };
      stableDbStateRef.current = { startTime: null, lastDb: null, lastLoggedSecond: -1 };
      const startCalTime = Date.now();
      let thresholdDb = -45;
      let baselineDb = null;
      let calibrationDone = false;
      let silenceStart = null;

      vadIntervalRef.current = setInterval(() => {
        try {
    analyser.getFloatTimeDomainData(dataArray);

    let sum = 0;
    for (let i = 0; i < dataArray.length; i++) {
      sum += dataArray[i] * dataArray[i];
    }

    const rms = Math.sqrt(sum / dataArray.length) || 1e-12;
    const db = 20 * Math.log10(rms);

    currentDbRef.current = db;

    window.dispatchEvent(
      new CustomEvent("vad-db", { detail: { db } })
    );

    const now = Date.now();

    /* ----------------------------------
       STEP 1: WAIT UNTIL TTS FINISHES
    -----------------------------------*/
    if (ttsPlayingRef.current) {
      calibrationDone = false;
      baselineDb = null;
      silenceStart = null;
      return;
    }

    /* ----------------------------------
       STEP 2: CALIBRATE ROOM (2s)
    -----------------------------------*/
    if (!calibrationDone) {
      if (!baselineDb) {
        baselineDb = {
          sum: 0,
          count: 0,
          start: now,
        };
      }

      baselineDb.sum += db;
      baselineDb.count++;

      if (now - baselineDb.start < 2000) {
        return; // still calibrating
      }

      const avg = baselineDb.sum / baselineDb.count;

      // Lock silence threshold
      baselineDb.value = avg + 6; // margin
      calibrationDone = true;

      console.log("✅ Room calibrated:", baselineDb.value.toFixed(1));

      return;
    }

    /* ----------------------------------
       STEP 3: SILENCE DETECTION
    -----------------------------------*/

    const SILENCE_THRESHOLD = baselineDb.value;
    const SPEECH_THRESHOLD = SILENCE_THRESHOLD + 8;

    const isSilent = db <= SILENCE_THRESHOLD;
    const isSpeech = db >= SPEECH_THRESHOLD;

    if (isSilent) {
      if (!silenceStart) {
        silenceStart = now;
        console.log("🔇 Silence started");
      }

      const duration = now - silenceStart;

      if (duration >= 5000 && !skipTriggeredRef.current) {
        skipTriggeredRef.current = true;

        console.warn("⚡ 5s silence → AUTO SKIP");

        handleSubmitAndNext();
      }

    } else if (isSpeech) {
      silenceStart = null;
    }

  } catch (e) {
    console.error("VAD error:", e);
  }
}, 120);
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
    // Prevent multiple concurrent submissions/skips
    if (submitInProgressRef.current) {
      console.log("⏳ Submission already in progress, ignoring duplicate skip/submit");
      return;
    }
    submitInProgressRef.current = true;

    const qs = questionsRef.current || [];
    const idx = indexRef.current || 0;
    const ans = answerRef.current || "";

    if (!qs.length) {
      submitInProgressRef.current = false;
      return;
    }

    console.log(`📤 Submitting answer for question ${idx + 1}/${qs.length}`);

    const path = candidateMode ? `/candidate/interviews/${id}/answer` : `/interviews/${id}/answer`;
    const headers = candidateMode ? { 'X-Candidate-Token': candidateToken } : {};
    const q = qs[idx];

    // Submit current answer immediately
    if (q) {
      const form = new FormData();
      form.append("question_id", q.id);
      form.append("answer", ans);
      api.post(path, form, { headers })
        .catch((err) => {
          console.error("Answer submission failed:", err?.response?.status, err?.message);
        });
    }

    // Clear answer state
    setAnswer("");

    // NOTE: we do NOT reset skipTriggeredRef here because it can allow re-trigger
    // before the UI advances to the next question.

    // Check if this is the last question
    if (idx >= qs.length - 1) {
      // Last question - finish interview
      console.log("🏁 Last question complete - finishing interview");
      stopRecording();
      const finishPath = candidateMode
        ? `/candidate/interviews/${id}/finish`
        : `/interviews/${id}/finish`;
      api.post(finishPath, null, { headers })
        .catch((err) => {
          console.error("Finish failed:", err?.response?.status, err?.message);
        });
      setStatus("Complete");
      setTimeout(() => navigate("/"), 1000);
    } else {
      // Advance to next question immediately
      const nextIndex = idx + 1;
      console.log(`✅ ADVANCING: Question ${idx + 1} → Question ${nextIndex + 1}`);
      setIndex(nextIndex);
    }

    // release submission lock shortly after state updates
    setTimeout(() => {
      submitInProgressRef.current = false;
    }, 250);
  }

  const [dbValue, setDbValue] = useState(-90);
  const [ttsPlaying, setTtsPlaying] = useState(false);
  const synthRef = useRef(window.speechSynthesis || null);
  const location = useLocation();
  const urlParams = new URLSearchParams(location.search);
  const [preStartActive, setPreStartActive] = useState(urlParams.get('start') === 'true' || urlParams.get('start') === '1');
  const [preStartSeconds, setPreStartSeconds] = useState(preStartActive ? 10 : 0);

  // Convert dBFS to UI scale (0-100)
  // -90 dBFS → 0, -5 dBFS → 100
  function convertDbfsToUiScale(db) {
    const MIN_DB = -90;
    const MAX_DB = -5;
    if (db <= MIN_DB) return 0;
    if (db >= MAX_DB) return 100;
    return ((db - MIN_DB) / (MAX_DB - MIN_DB)) * 100;
  }

  useEffect(() => {
    const onDb = (e) => setDbValue(e.detail.db);
    window.addEventListener("vad-db", onDb);
    return () => window.removeEventListener("vad-db", onDb);
  }, []);

  useEffect(() => { ttsPlayingRef.current = ttsPlaying; }, [ttsPlaying]);

  // When question advances, reset skip-related state so next question can be auto-skipped again
  useEffect(() => {
    skipTriggeredRef.current = false;
    idleStateRef.current = { type: null, startTime: null };
    stableDbStateRef.current = { startTime: null, lastDb: null, lastLoggedSecond: -1 };
    submitInProgressRef.current = false;
  }, [index]);

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
              <div className="decibel-bar"><div className="decibel-level" style={{ width: `${convertDbfsToUiScale(dbValue)}%` }} /></div>
              <div className="decibel-value">Level: {convertDbfsToUiScale(dbValue).toFixed(0)}</div>
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