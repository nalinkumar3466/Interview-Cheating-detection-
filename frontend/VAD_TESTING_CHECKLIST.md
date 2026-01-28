# VAD Implementation Testing Checklist

## Pre-Testing Setup
- [ ] Clear browser cache (Ctrl+Shift+Delete)
- [ ] Open browser DevTools (F12)
- [ ] Navigate to interview recording page
- [ ] Grant microphone permissions

---

## Test 1: Calibration Detection ✓

### Steps:
1. Click "Start Recording"
2. Immediately stay silent for 1.5 seconds
3. Open Console tab in DevTools

### Expected Output:
```
VAD: Starting calibration phase (1.5s)...
VAD calibration complete:
  - Noise floor: -XX.X dBFS
  - Threshold: -XX.X dBFS (floor + 10dB margin)
  - Expected behavior: Quiet room ~-XX.X dBFS, Medium office ~-XX.X dBFS
```

### Pass/Fail:
- [ ] Calibration message appears within 2 seconds
- [ ] Noise floor value is between -80 and -40 dBFS
- [ ] Threshold = Noise floor + 10 (within 0.1 dB)

---

## Test 2: Decibel Bar Display (Blue Gradient) ✓

### Steps:
1. During recording, look at the decibel bar next to "Recording"
2. Speak into the microphone at normal volume

### Expected Visual:
```
Recording │ 🔵🔵🔵🔵░░░░░░ │ -35.2 dBFS
```

### Pass/Fail:
- [ ] Bar is BLUE (not purple/indigo)
- [ ] Bar fills from left to right
- [ ] Bar shrinks when you stop speaking
- [ ] dB value updates smoothly
- [ ] Blue color is visible (not faded/transparent)

---

## Test 3: RMS-Based Detection (Smooth, Not Peaky) ✓

### Steps:
1. Start recording
2. Wait for calibration
3. Make a sharp "click" sound (dry audio event)
4. Watch the decibel bar and console logs

### Expected Behavior:
```
Quick click:     │ 🔵░░░░░░░░░░░░ │ -52 dBFS
                 │ (short spike, not sustained)

Normal speech:   │ 🔵🔵🔵🔵░░░░░░ │ -38 dBFS
                 │ (sustained, smooth)
```

### Pass/Fail:
- [ ] Click doesn't cause false auto-advance
- [ ] Speech is clearly detected
- [ ] Bar changes smoothly (not jittery)
- [ ] Console shows "silent-dB" values (not "peak-dB")

---

## Test 4: Silence Detection (5-Second Window) ✓

### Steps:
1. Start recording
2. Wait for calibration (1.5s)
3. Say a short sentence: "Test one two three"
4. Stop talking and observe

### Expected Timeline:
```
Time  Event
─────────────────────────────────────
0s    Calibration starts
1.5s  Calibration ends, VAD active
2s    You speak → Detection ✓
4s    You stop speaking
4-9s  Silence window... (console shows "silent-dB")
9s    5 seconds elapsed → Auto-advance to next question ✓
```

### Pass/Fail:
- [ ] Auto-advance happens **between 9-10 seconds** (not earlier)
- [ ] Console shows "silence detected -> advancing question"
- [ ] Next question loads automatically
- [ ] No manual button click needed

---

## Test 5: Adaptive Threshold (Different Environments) ✓

### Test 5A: Quiet Room
### Steps:
1. Go to a quiet room (no A/C, no traffic)
2. Start recording
3. Wait for calibration
4. Note the threshold value

### Expected:
```
Noise floor: -65 to -75 dBFS
Threshold: -55 to -65 dBFS
```

### Pass/Fail:
- [ ] Threshold is between -55 and -65 dBFS
- [ ] Speech easily detected (well above threshold)
- [ ] Keyboard/mouse doesn't trigger false positives

### Test 5B: Medium Office
### Steps:
1. Go to an office with some background noise
2. Start recording
3. Wait for calibration
4. Note the threshold value

### Expected:
```
Noise floor: -50 to -60 dBFS
Threshold: -40 to -50 dBFS
```

### Pass/Fail:
- [ ] Threshold is between -40 and -50 dBFS
- [ ] Speech clearly detected
- [ ] Background noise ignored (doesn't trigger auto-advance)

### Test 5C: Loud Environment (Optional)
### Steps:
1. Go to a café or busy area
2. Start recording
3. Wait for calibration
4. Note the threshold value

### Expected:
```
Noise floor: -40 to -50 dBFS
Threshold: -30 to -40 dBFS
```

### Pass/Fail:
- [ ] Threshold is high (between -30 and -40 dBFS)
- [ ] Loud speech is required to trigger
- [ ] May have false positives (acceptable in loud environments)

---

## Test 6: Console Logging (Debugging) ✓

### Steps:
1. Start recording
2. Keep Console tab open and visible
3. Speak, pause, speak again
4. Watch console output

### Expected Log Pattern:
```
[14:30:00] VAD: Starting calibration phase (1.5s)...
[14:30:01] (no logs during calibration)
[14:30:01] VAD calibration complete: ...
[14:30:02] (speaking - no logs, just bar updates)
[14:30:04] 2025-01-13T14:30:04.123Z silent-dB: -65.3 (threshold: -55.2)
[14:30:05] 2025-01-13T14:30:05.456Z silent-dB: -64.8 (threshold: -55.2)
[14:30:06] 2025-01-13T14:30:06.789Z silent-dB: -65.1 (threshold: -55.2)
[14:30:07] 2025-01-13T14:30:07.012Z silence detected -> advancing question
```

### Pass/Fail:
- [ ] "Starting calibration" message appears first
- [ ] "VAD calibration complete" appears after 1.5-2 seconds
- [ ] "silent-dB" messages appear when silent
- [ ] "silence detected" appears after 5 seconds of silence
- [ ] No error messages in console

---

## Test 7: Edge Cases ✓

### Test 7A: Very Loud Calibration
### Steps:
1. Start recording with loud background noise (music, people talking)
2. Don't stop it during calibration

### Expected:
```
Noise floor: -20 to -30 dBFS
Threshold: -10 to -20 dBFS
Speech should still be detected
```

### Pass/Fail:
- [ ] System adapts to loud environment
- [ ] Doesn't crash
- [ ] Threshold is still above speech

### Test 7B: Interrupted Silence
### Steps:
1. Start recording, wait for calibration
2. Say something
3. Pause for 3 seconds
4. Say "hello" (break silence)
5. Wait another 5 seconds

### Expected:
```
[speaking] → [pause 3s] → [speaking] → [pause 5s] → advance
             ↓ silence counter resets
```

### Pass/Fail:
- [ ] Brief silence doesn't trigger auto-advance
- [ ] Only 5 consecutive seconds triggers it
- [ ] Speaking again resets the counter

### Test 7C: Continuous Background Noise
### Steps:
1. Start recording during calibration with white noise/fan
2. Run calibration with constant noise
3. Speak normally

### Expected:
```
Noise floor: -45 dBFS
Threshold: -35 dBFS
Speech should still trigger (higher dB than threshold)
```

### Pass/Fail:
- [ ] Speech detected despite constant noise
- [ ] No false auto-advance on just noise
- [ ] dB values show clear separation

---

## Test 8: UI Responsiveness ✓

### Steps:
1. Start recording
2. Minimize window, switch apps, come back
3. Speak during recording

### Expected:
- [ ] Bar continues updating
- [ ] Console logs continue
- [ ] No freezing or lag
- [ ] dB values show real-time data

---

## Test 9: Mobile / Different Devices (Optional)

### Steps:
1. Test on phone (if applicable)
2. Test in browser (if different from desktop)
3. Compare console output

### Expected:
```
Desktop:
  Noise floor: -70 dBFS, Threshold: -60 dBFS

Phone:
  Noise floor: -65 dBFS, Threshold: -55 dBFS
  
(Different but both work!)
```

### Pass/Fail:
- [ ] Each device auto-calibrates independently
- [ ] Same code works on all devices
- [ ] No hard-coded values override calibration

---

## Summary Checklist

- [ ] All 7 main tests pass
- [ ] Decibel bar is BLUE and visible
- [ ] Calibration completes in ~1.5-2 seconds
- [ ] Silence auto-advance triggers at 5+ seconds
- [ ] Console logs show expected output
- [ ] Works in different environments
- [ ] No JavaScript errors in console
- [ ] No CSS warnings about decibel-level

---

## Known Limitations (Acceptable)

- [ ] Very loud environments may have false positives
- [ ] Thick accents or very quiet speakers may need threshold adjustment
- [ ] Network lag doesn't affect VAD (runs locally)
- [ ] Chrome/Firefox/Safari should all work (standard Web Audio API)

---

## Rollback Instructions (If Needed)

If tests fail, revert these files:
1. `frontend/src/pages/RunInterview.jsx` — VAD logic
2. `frontend/src/styles/interview.css` — Blue gradient

Check git history or contact the dev team for previous versions.

---

**Testing Date:** _______________  
**Tested By:** _______________  
**Result:** PASS ☑ / FAIL ☐  
**Notes:** _______________________________________________

---

**Version:** 1.0  
**Last Updated:** January 13, 2025
