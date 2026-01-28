// React Native Audio VAD Implementation (Expo Audio)
// Correct implementation with calibration and auto-advance

import { Audio } from 'expo-av';
import { useCallback, useRef, useEffect } from 'react';

const CALIBRATION_DURATION = 1500; // 1.5 seconds
const SILENCE_TRIGGER_TIME = 5000; // 5 seconds
const SMOOTHING_WINDOW = 300; // ms
const SAMPLE_INTERVAL = 100; // ms

export function useVoiceActivityDetection({ onSilenceDetected, onThresholdReady }) {
  const recordingRef = useRef(null);
  const calibrationStartRef = useRef(null);
  const calibrationSamplesRef = useRef([]);
  const noiseFloorRef = useRef(-60); // fallback default
  const thresholdRef = useRef(-45); // fallback default
  const calibratedRef = useRef(false);
  const rmsHistoryRef = useRef([]);
  const silenceStartRef = useRef(null);
  const lastSpeechRef = useRef(Date.now());
  const monitorIntervalRef = useRef(null);

  // Start monitoring audio levels
  const startMonitoring = useCallback(async () => {
    if (!recordingRef.current) return;

    calibrationStartRef.current = Date.now();
    calibrationSamplesRef.current = [];
    calibratedRef.current = false;
    rmsHistoryRef.current = [];
    silenceStartRef.current = null;
    lastSpeechRef.current = Date.now();

    console.log('VAD: Starting calibration phase (1.5s)...');

    monitorIntervalRef.current = setInterval(async () => {
      try {
        const status = await recordingRef.current?.getStatusAsync();
        if (!status?.canRecord || status.metering === undefined) return;

        const level = status.metering; // already in dBFS from Expo Audio
        const now = Date.now();

        // ========== CALIBRATION PHASE ==========
        if (!calibratedRef.current && now - calibrationStartRef.current < CALIBRATION_DURATION) {
          // Collect RMS samples during first 1.5 seconds
          calibrationSamplesRef.current.push(level);
          console.debug(`[Calibration] Sample ${calibrationSamplesRef.current.length}: ${level.toFixed(1)} dBFS`);
          return; // Skip VAD during calibration
        }

        // ========== END CALIBRATION: COMPUTE THRESHOLD ==========
        if (!calibratedRef.current) {
          calibratedRef.current = true;

          if (calibrationSamplesRef.current.length > 0) {
            // Calculate average noise floor from samples
            const sum = calibrationSamplesRef.current.reduce((a, b) => a + b, 0);
            noiseFloorRef.current = sum / calibrationSamplesRef.current.length;
            
            // Adaptive threshold: noise floor + 10 dB margin
            const marginDb = 10;
            thresholdRef.current = noiseFloorRef.current + marginDb;

            console.info(`VAD calibration complete:
  - Noise floor: ${noiseFloorRef.current.toFixed(1)} dBFS
  - Threshold: ${thresholdRef.current.toFixed(1)} dBFS (floor + ${marginDb}dB margin)`);

            // Notify parent component that calibration is ready
            onThresholdReady?.(thresholdRef.current, noiseFloorRef.current);
          }

          // Clear samples to free memory
          calibrationSamplesRef.current = [];
        }

        // ========== VAD PHASE: MONITOR WITH SMOOTHING WINDOW ==========
        rmsHistoryRef.current.push({ t: now, level });
        // Trim history to smoothing window
        while (rmsHistoryRef.current.length && now - rmsHistoryRef.current[0].t > SMOOTHING_WINDOW) {
          rmsHistoryRef.current.shift();
        }

        // Calculate average level over smoothing window
        const avgLevel = rmsHistoryRef.current.length > 0
          ? rmsHistoryRef.current.reduce((sum, s) => sum + s.level, 0) / rmsHistoryRef.current.length
          : level;

        const isSilent = avgLevel < thresholdRef.current;

        // Speech detected: reset silence counter
        if (!isSilent) {
          lastSpeechRef.current = now;
          silenceStartRef.current = null;
          console.debug(`[Speaking] Level: ${avgLevel.toFixed(1)} dBFS (threshold: ${thresholdRef.current.toFixed(1)})`);
        } else {
          // Silence detected: start/continue silence timer
          if (!silenceStartRef.current) {
            silenceStartRef.current = now;
          }

          const silenceDuration = now - lastSpeechRef.current;
          console.debug(`[Silent] Level: ${avgLevel.toFixed(1)} dBFS, Duration: ${(silenceDuration / 1000).toFixed(1)}s`);

          // Trigger after 5 seconds of silence
          if (silenceDuration >= SILENCE_TRIGGER_TIME) {
            console.info(`${new Date().toISOString()} Silence detected (${(silenceDuration / 1000).toFixed(1)}s) -> Auto-advance`);
            
            // Call callback to advance question
            onSilenceDetected?.();
            
            // Reset for next question
            lastSpeechRef.current = now;
            silenceStartRef.current = null;
          }
        }
      } catch (err) {
        console.warn('VAD monitoring error:', err);
      }
    }, SAMPLE_INTERVAL);
  }, [onSilenceDetected, onThresholdReady]);

  // Stop monitoring
  const stopMonitoring = useCallback(() => {
    if (monitorIntervalRef.current) {
      clearInterval(monitorIntervalRef.current);
      monitorIntervalRef.current = null;
    }
  }, []);

  return {
    startMonitoring,
    stopMonitoring,
    setRecordingRef: (ref) => {
      recordingRef.current = ref;
    },
    getThreshold: () => thresholdRef.current,
    getNoiseFloor: () => noiseFloorRef.current,
    isCalibrated: () => calibratedRef.current,
  };
}

// ============================================================================
// USAGE EXAMPLE IN YOUR INTERVIEW COMPONENT
// ============================================================================

import React, { useRef, useState, useCallback } from 'react';
import { View, Text, Button, Alert } from 'react-native';
import { Audio } from 'expo-av';
import { useVoiceActivityDetection } from './useVoiceActivityDetection';

export function InterviewRecorder({ questions, currentQuestionIndex, onAdvanceQuestion }) {
  const recordingRef = useRef(null);
  const [currentIndex, setCurrentIndex] = useState(currentQuestionIndex || 0);
  const [threshold, setThreshold] = useState(-45);
  const [noiseFloor, setNoiseFloor] = useState(-60);
  const [isCalibrating, setIsCalibrating] = useState(true);

  const vad = useVoiceActivityDetection({
    onSilenceDetected: () => {
      console.log('🚀 Auto-advancing to next question');
      advanceQuestion();
    },
    onThresholdReady: (t, nf) => {
      setThreshold(t);
      setNoiseFloor(nf);
      setIsCalibrating(false);
    },
  });

  const startRecording = useCallback(async () => {
    try {
      // Request permissions
      const { granted } = await Audio.requestPermissionsAsync();
      if (!granted) {
        Alert.alert('Permission denied', 'Microphone access required');
        return;
      }

      // Configure audio session
      await Audio.setAudioModeAsync({
        allowsRecordingIOS: true,
        playsInSilentModeIOS: true,
        shouldDuckAndroid: true,
        playThroughEarpieceAndroid: false,
      });

      // Create recording
      const recording = new Audio.Recording();
      await recording.prepareToRecordAsync(
        Audio.RECORDING_OPTIONS_PRESET_HIGH_QUALITY
      );
      
      recordingRef.current = recording;
      vad.setRecordingRef(recording);

      // Start recording
      await recording.startAsync();
      console.log('Recording started');

      // Start VAD monitoring (includes calibration)
      setIsCalibrating(true);
      vad.startMonitoring();
    } catch (err) {
      console.error('Failed to start recording:', err);
      Alert.alert('Error', 'Failed to start recording');
    }
  }, [vad]);

  const stopRecording = useCallback(async () => {
    try {
      vad.stopMonitoring();

      if (recordingRef.current) {
        await recordingRef.current.stopAndUnloadAsync();
        const uri = recordingRef.current.getURI();
        console.log('Recording saved:', uri);
        recordingRef.current = null;
      }
    } catch (err) {
      console.error('Failed to stop recording:', err);
    }
  }, [vad]);

  const advanceQuestion = useCallback(async () => {
    await stopRecording();

    if (currentIndex < questions.length - 1) {
      setCurrentIndex(currentIndex + 1);
      setIsCalibrating(true);
      
      // Small delay before starting next question
      setTimeout(() => {
        startRecording();
      }, 500);
    } else {
      Alert.alert('Complete', 'Interview finished!');
      onAdvanceQuestion?.(currentIndex + 1);
    }
  }, [currentIndex, questions.length, stopRecording, startRecording, onAdvanceQuestion]);

  const currentQuestion = questions[currentIndex];

  return (
    <View style={{ flex: 1, padding: 20 }}>
      <Text style={{ fontSize: 18, fontWeight: 'bold', marginBottom: 10 }}>
        Question {currentIndex + 1} of {questions.length}
      </Text>
      <Text style={{ fontSize: 16, marginBottom: 20, color: '#555' }}>
        {currentQuestion?.text || 'Loading...'}
      </Text>

      {/* VAD Status */}
      <View style={{ backgroundColor: '#f0f0f0', padding: 10, borderRadius: 8, marginBottom: 20 }}>
        <Text style={{ fontSize: 12, color: '#666' }}>
          {isCalibrating ? (
            'Calibrating microphone... (1.5s)'
          ) : (
            <>
              ✓ Calibrated | Threshold: {threshold.toFixed(1)} dBFS | Floor: {noiseFloor.toFixed(1)} dBFS
            </>
          )}
        </Text>
      </View>

      {/* Controls */}
      <Button title="Start Recording" onPress={startRecording} />
      <Button title="Stop Recording" onPress={stopRecording} />
      <Button title="Skip Question" onPress={advanceQuestion} color="#ff6666" />
    </View>
  );
}
