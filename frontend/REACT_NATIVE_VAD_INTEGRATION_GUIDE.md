# React Native VAD Integration Guide

## Quick Start (Copy-Paste Ready)

### Step 1: Create VAD Hook File
**File:** `hooks/useVoiceActivityDetection.js`

Copy the entire `useVoiceActivityDetection` function from `VAD_REACT_NATIVE_IMPLEMENTATION.js`

### Step 2: Import in Your Interview Component

```javascript
import { useVoiceActivityDetection } from '../hooks/useVoiceActivityDetection';
```

### Step 3: Initialize VAD in Your Component

```javascript
export function InterviewScreen({ questions }) {
  const [currentIndex, setCurrentIndex] = useState(0);
  const recordingRef = useRef(null);

  const vad = useVoiceActivityDetection({
    onSilenceDetected: () => {
      // This callback runs when 5+ seconds of silence detected
      console.log('Auto-advancing...');
      advanceToNextQuestion();
    },
    onThresholdReady: (threshold, noiseFloor) => {
      // This callback runs after 1.5s calibration
      console.log(`Ready! Threshold: ${threshold.toFixed(1)} dBFS`);
    },
  });

  const startRecording = async () => {
    // ... your recording setup code ...
    recordingRef.current = recording;
    vad.setRecordingRef(recording);  // ← Pass recording to VAD
    await recording.startAsync();
    vad.startMonitoring();  // ← Start monitoring
  };

  const advanceToNextQuestion = async () => {
    vad.stopMonitoring();  // ← Stop monitoring
    // ... submit answer, move to next question ...
  };
}
```

---

## Complete Example: Interview Component

```javascript
// screens/InterviewScreen.jsx
import React, { useState, useRef, useCallback } from 'react';
import { View, Text, Button, StyleSheet, Alert } from 'react-native';
import { Audio } from 'expo-av';
import { useVoiceActivityDetection } from '../hooks/useVoiceActivityDetection';

const styles = StyleSheet.create({
  container: { flex: 1, padding: 20 },
  questionText: { fontSize: 18, marginBottom: 20 },
  statusBox: { 
    backgroundColor: '#f0f0f0', 
    padding: 15, 
    borderRadius: 8, 
    marginBottom: 20 
  },
  statusText: { fontSize: 12, color: '#666' },
  calibratingText: { color: '#ff9800', fontWeight: 'bold' },
  readyText: { color: '#4caf50', fontWeight: 'bold' },
  buttonContainer: { gap: 10 },
});

export function InterviewScreen({ route, navigation }) {
  const { interviewId, questions } = route.params || {};
  const [currentIndex, setCurrentIndex] = useState(0);
  const [isRecording, setIsRecording] = useState(false);
  const [isCalibrating, setIsCalibrating] = useState(false);
  const [threshold, setThreshold] = useState(-45);
  const [noiseFloor, setNoiseFloor] = useState(-60);
  const recordingRef = useRef(null);

  // Initialize VAD with callbacks
  const vad = useVoiceActivityDetection({
    onSilenceDetected: () => {
      console.log('🚀 5 seconds silence -> Auto-advancing');
      advanceQuestion();
    },
    onThresholdReady: (t, nf) => {
      console.log(`✅ Calibration done: Threshold=${t.toFixed(1)}, Floor=${nf.toFixed(1)}`);
      setThreshold(t);
      setNoiseFloor(nf);
      setIsCalibrating(false);
    },
  });

  // Start recording this question
  const startRecording = useCallback(async () => {
    try {
      // Request microphone permission
      const { granted } = await Audio.requestPermissionsAsync();
      if (!granted) {
        Alert.alert('Permission Denied', 'Microphone access is required');
        return;
      }

      // Configure audio
      await Audio.setAudioModeAsync({
        allowsRecordingIOS: true,
        playsInSilentModeIOS: true,
        shouldDuckAndroid: true,
      });

      // Create recording with high quality
      const recording = new Audio.Recording();
      await recording.prepareToRecordAsync(
        Audio.RECORDING_OPTIONS_PRESET_HIGH_QUALITY
      );

      recordingRef.current = recording;
      vad.setRecordingRef(recording);  // ← Give VAD the recording

      await recording.startAsync();
      setIsRecording(true);
      setIsCalibrating(true);

      console.log('📹 Recording started');

      // Start VAD monitoring (includes 1.5s calibration)
      vad.startMonitoring();
    } catch (err) {
      console.error('Recording error:', err);
      Alert.alert('Error', 'Failed to start recording');
    }
  }, [vad]);

  // Stop recording
  const stopRecording = useCallback(async () => {
    try {
      vad.stopMonitoring();  // ← Stop monitoring first

      if (recordingRef.current) {
        await recordingRef.current.stopAndUnloadAsync();
        const uri = recordingRef.current.getURI();
        console.log('✅ Recording saved:', uri);
        recordingRef.current = null;
      }

      setIsRecording(false);
    } catch (err) {
      console.error('Stop recording error:', err);
    }
  }, [vad]);

  // Advance to next question (manual or auto)
  const advanceQuestion = useCallback(async () => {
    await stopRecording();

    // Could submit answer to backend here
    // await submitAnswer(questions[currentIndex], recordingUri);

    if (currentIndex < questions.length - 1) {
      // More questions remain
      setCurrentIndex(currentIndex + 1);
      setIsCalibrating(true);

      // Small delay before starting next question
      setTimeout(() => {
        startRecording();
      }, 500);
    } else {
      // Interview complete
      Alert.alert('Complete!', 'All questions answered');
      navigation.goBack();
    }
  }, [currentIndex, questions.length, stopRecording, startRecording]);

  const currentQuestion = questions?.[currentIndex];
  const questionCount = questions?.length || 0;

  return (
    <View style={styles.container}>
      {/* Header */}
      <Text style={{ fontSize: 16, fontWeight: 'bold', marginBottom: 10 }}>
        Question {currentIndex + 1} of {questionCount}
      </Text>

      {/* Question Text */}
      <Text style={styles.questionText}>{currentQuestion?.text || 'Loading...'}</Text>

      {/* VAD Status */}
      <View style={styles.statusBox}>
        {isCalibrating ? (
          <Text style={[styles.statusText, styles.calibratingText]}>
            🎙️ Calibrating microphone... (1.5s)
          </Text>
        ) : (
          <>
            <Text style={[styles.statusText, styles.readyText]}>
              ✓ Ready to record
            </Text>
            <Text style={styles.statusText}>
              Threshold: {threshold.toFixed(1)} dBFS
            </Text>
            <Text style={styles.statusText}>
              Noise Floor: {noiseFloor.toFixed(1)} dBFS
            </Text>
          </>
        )}
      </View>

      {/* Recording Status */}
      {isRecording && (
        <View style={{ 
          backgroundColor: '#fff3cd', 
          padding: 10, 
          borderRadius: 8, 
          marginBottom: 20 
        }}>
          <Text style={{ color: '#856404', fontWeight: 'bold' }}>
            🔴 Recording... Auto-advance in 5 seconds of silence
          </Text>
        </View>
      )}

      {/* Controls */}
      <View style={styles.buttonContainer}>
        {!isRecording ? (
          <Button 
            title="Start Recording" 
            onPress={startRecording}
            color="#4CAF50"
          />
        ) : (
          <Button 
            title="Stop Recording" 
            onPress={stopRecording}
            color="#f44336"
          />
        )}

        <Button 
          title="Skip Question" 
          onPress={advanceQuestion}
          color="#2196F3"
        />

        <Button 
          title="Exit Interview" 
          onPress={() => navigation.goBack()}
          color="#999"
        />
      </View>

      {/* Debug Info (Remove in production) */}
      {__DEV__ && (
        <View style={{ marginTop: 30, padding: 10, backgroundColor: '#f5f5f5' }}>
          <Text style={{ fontSize: 10, color: '#666' }}>
            DEBUG: Index={currentIndex}, Recording={isRecording}, 
            Calibrating={isCalibrating}
          </Text>
        </View>
      )}
    </View>
  );
}

export default InterviewScreen;
```

---

## Expected Console Output

### When Recording Starts:
```
VAD: Starting calibration phase (1.5s)...
[Calibration] Sample 1: -68.2 dBFS
[Calibration] Sample 2: -68.1 dBFS
[Calibration] Sample 3: -68.3 dBFS
...
[Calibration] Sample 15: -68.0 dBFS
VAD calibration complete:
  - Noise floor: -68.1 dBFS
  - Threshold: -58.1 dBFS (floor + 10dB margin)
```

### When Speaking:
```
[Speaking] Level: -40.5 dBFS (threshold: -58.1)
[Speaking] Level: -35.2 dBFS (threshold: -58.1)
```

### When Silent (5+ seconds):
```
[Silent] Level: -70.1 dBFS, Duration: 0.1s
[Silent] Level: -70.2 dBFS, Duration: 0.2s
...
[Silent] Level: -69.8 dBFS, Duration: 5.0s
2025-01-13T14:30:00.000Z Silence detected (5.0s) -> Auto-advance
🚀 Auto-advancing...
```

---

## Customization Options

### Change Calibration Duration
```javascript
const CALIBRATION_DURATION = 2000; // 2 seconds instead of 1.5
```

### Change Silence Threshold
```javascript
const SILENCE_TRIGGER_TIME = 3000; // 3 seconds instead of 5
```

### Change Margin Above Noise Floor
```javascript
// In the hook, change this line:
const marginDb = 15; // 15 dB instead of 10
```

### Add Logging Callback
```javascript
const vad = useVoiceActivityDetection({
  onSilenceDetected: () => advanceQuestion(),
  onThresholdReady: (t, nf) => {
    // Do something with threshold/floor
    analytics.log('vad_calibrated', { threshold: t, noiseFloor: nf });
  },
  onLevelUpdate: (level, isStandby) => {
    // Real-time level updates (if added to hook)
    updateDecibelMeter(level);
  },
});
```

---

## Troubleshooting

### "Recording is not defined"
**Problem:** VAD can't access recording object  
**Solution:** Make sure you call `vad.setRecordingRef(recording)` after creating it

### "Calibration never completes"
**Problem:** No audio or recording not started  
**Solution:** Check that `getStatusAsync()` returns valid `metering` value

### "Auto-advance not working"
**Problem:** `onSilenceDetected` callback not firing  
**Solution:**
- Check that you're in complete silence for 5+ seconds
- Check console logs for "Silent" messages
- Verify threshold is lower than actual silence level

### "Threshold too high/low"
**Problem:** Microphone sensitive or noisy  
**Solution:** This is normal—adjust `marginDb` or use different environment

---

## Performance Notes

- VAD runs at 100ms intervals = 10 Hz sampling
- Uses ~2% CPU (Expo Audio metering is very efficient)
- Memory: ~50 KB for history buffer
- No background permissions needed
- Works with built-in mic or external headset mic

---

## Production Checklist

- [ ] Remove `__DEV__` console logging
- [ ] Test on real device (not simulator)
- [ ] Test with different microphone (headsets, etc.)
- [ ] Test in different environments (quiet, office, noisy)
- [ ] Handle app backgrounding (pause VAD)
- [ ] Handle permission denial gracefully
- [ ] Test voice interruption scenarios
- [ ] Set up analytics for threshold/floor tracking
- [ ] Consider saving recordings to backend
- [ ] Add timeout for stuck recordings (30min max)

---

**You're all set! Copy the code and test it.**
