// frontend/src/components/admin/CanvasReplay.jsx
import React, { useRef, useEffect, useState, useCallback } from "react";
import { Stage, Layer, Line } from "react-konva";

/**
 * CanvasReplay - Replays a canvas drawing with animations
 * 
 * Props:
 * - strokes: Array of stroke objects with {tool, color, strokeWidth, startedAt, points: [{x,y,t}]}
 * - metadata: {duration, strokeCount, submittedAt}
 * - onMetadataCompute: Callback with computed {duration, strokeCount}
 */
export default function CanvasReplay({ strokes = [], metadata = null, onMetadataCompute = null }) {
  const stageRef = useRef(null);
  const containerRef = useRef(null);
  const [stageSize, setStageSize] = useState({ width: 800, height: 550 });
  
  // Replay state
  const [isPlaying, setIsPlaying] = useState(false);
  const [currentTime, setCurrentTime] = useState(0);
  const [displayedStrokes, setDisplayedStrokes] = useState([]);
  const [isPaused, setIsPaused] = useState(false);
  
  // Computed metadata
  const [computedDuration, setComputedDuration] = useState(0);
  const [strokeCount, setStrokeCount] = useState(0);
  
  // Replay engine refs
  const animationRef = useRef(null);
  const startTimeRef = useRef(null);
  const pausedTimeRef = useRef(null);
  const totalDurationRef = useRef(0);

  /**
   * Compute metadata: duration and stroke count
   */
  useEffect(() => {
    if (!strokes || strokes.length === 0) {
      setStrokeCount(0);
      setComputedDuration(0);
      totalDurationRef.current = 0;
      return;
    }

    let minTimestamp = Infinity;
    let maxTimestamp = 0;
    
    for (const stroke of strokes) {
      if (stroke.points && stroke.points.length > 0) {
        const points = stroke.points;
        const firstTime = points[0].t;
        const lastTime = points[points.length - 1].t;
        
        if (firstTime < minTimestamp) minTimestamp = firstTime;
        if (lastTime > maxTimestamp) maxTimestamp = lastTime;
      }
    }

    // Duration in seconds
    const duration = minTimestamp === Infinity ? 0 : (maxTimestamp - minTimestamp) / 1000;
    
    setStrokeCount(strokes.length);
    setComputedDuration(duration);
    totalDurationRef.current = duration;

    // Notify parent of computed metadata
    if (onMetadataCompute) {
      onMetadataCompute({
        strokeCount: strokes.length,
        duration: Math.ceil(duration),
        minTimestamp,
        maxTimestamp
      });
    }
  }, [strokes, onMetadataCompute]);

  /**
   * Update stage size on resize
   */
  useEffect(() => {
    function updateSize() {
      if (!containerRef.current) return;
      const width = containerRef.current.offsetWidth || 800;
      setStageSize({
        width: Math.max(width, 400),
        height: 550
      });
    }

    updateSize();
    window.addEventListener("resize", updateSize);
    return () => window.removeEventListener("resize", updateSize);
  }, []);

  /**
   * Render strokes up to a given timestamp
   */
  const renderStrokesAtTime = useCallback((targetTime) => {
    if (!strokes || strokes.length === 0) {
      setDisplayedStrokes([]);
      return;
    }

    // Get min timestamp to normalize
    let minTimestamp = Infinity;
    for (const stroke of strokes) {
      if (stroke.points && stroke.points.length > 0) {
        const firstTime = stroke.points[0].t;
        if (firstTime < minTimestamp) minTimestamp = firstTime;
      }
    }

    const normalizedTargetTime = (minTimestamp === Infinity ? 0 : minTimestamp) + targetTime * 1000;
    const rendered = [];

    for (const stroke of strokes) {
      if (!stroke.points || stroke.points.length === 0) continue;

      const visiblePoints = [];
      
      for (const point of stroke.points) {
        if (point.t <= normalizedTargetTime) {
          visiblePoints.push(point);
        }
      }

      if (visiblePoints.length > 0) {
        rendered.push({
          ...stroke,
          points: visiblePoints,
          isPartial: visiblePoints.length < stroke.points.length
        });
      }
    }

    setDisplayedStrokes(rendered);
  }, [strokes]);

  /**
   * Play/Pause/Restart handlers
   */
  const handlePlay = useCallback(() => {
    if (isPlaying) {
      setIsPaused(true);
      pausedTimeRef.current = currentTime;
      if (animationRef.current) {
        cancelAnimationFrame(animationRef.current);
      }
      return;
    }

    if (isPaused) {
      // Resume from paused state
      setIsPaused(false);
      // Animation will resume in the animation loop
      return;
    }

    // Start playing
    setIsPlaying(true);
    setIsPaused(false);
    setCurrentTime(0);
    startTimeRef.current = null;
    pausedTimeRef.current = null;
  }, [isPlaying, isPaused, currentTime]);

  const handlePause = useCallback(() => {
    setIsPlaying(false);
    setIsPaused(true);
    pausedTimeRef.current = currentTime;
    if (animationRef.current) {
      cancelAnimationFrame(animationRef.current);
    }
  }, [currentTime]);

  const handleRestart = useCallback(() => {
    setIsPlaying(false);
    setIsPaused(false);
    setCurrentTime(0);
    setDisplayedStrokes([]);
    startTimeRef.current = null;
    pausedTimeRef.current = null;
    if (animationRef.current) {
      cancelAnimationFrame(animationRef.current);
    }
  }, []);

  /**
   * Animation loop
   */
  useEffect(() => {
    if (!isPlaying) return;

    const animate = () => {
      const now = Date.now();

      if (startTimeRef.current === null) {
        // Initialize start time, accounting for paused time
        if (pausedTimeRef.current === null) {
          startTimeRef.current = now - (currentTime * 1000);
        } else {
          startTimeRef.current = now - (pausedTimeRef.current * 1000);
          pausedTimeRef.current = null;
        }
      }

      const elapsedSeconds = (now - startTimeRef.current) / 1000;
      
      if (elapsedSeconds >= totalDurationRef.current) {
        // Replay finished
        setCurrentTime(totalDurationRef.current);
        renderStrokesAtTime(totalDurationRef.current);
        setIsPlaying(false);
      } else {
        setCurrentTime(elapsedSeconds);
        renderStrokesAtTime(elapsedSeconds);
        animationRef.current = requestAnimationFrame(animate);
      }
    };

    animationRef.current = requestAnimationFrame(animate);

    return () => {
      if (animationRef.current) {
        cancelAnimationFrame(animationRef.current);
      }
    };
  }, [isPlaying, renderStrokesAtTime]);

  /**
   * Render progress percentage
   */
  const progressPercent = totalDurationRef.current > 0 
    ? (currentTime / totalDurationRef.current) * 100 
    : 0;

  return (
    <div className="canvas-replay-container" style={{ marginBottom: "20px" }}>
      {/* Stage */}
      <div ref={containerRef} style={{ marginBottom: "15px" }}>
        <Stage
          ref={stageRef}
          width={stageSize.width}
          height={stageSize.height}
          style={{
            border: "1px solid #ddd",
            background: "#fff",
            borderRadius: "4px"
          }}
        >
          <Layer>
            {displayedStrokes.map((stroke, idx) => (
              <Line
                key={idx}
                points={stroke.points.flatMap(p => [p.x, p.y])}
                stroke={stroke.color || "#000000"}
                strokeWidth={stroke.strokeWidth || 3}
                tension={0.5}
                lineCap="round"
                globalCompositeOperation={
                  stroke.tool === "eraser" ? "destination-out" : "source-over"
                }
              />
            ))}
          </Layer>
        </Stage>
      </div>

      {/* Metadata Info */}
      <div style={{
        display: "flex",
        gap: "20px",
        marginBottom: "15px",
        fontSize: "14px",
        color: "#666"
      }}>
        <div>
          <strong>Strokes:</strong> {strokeCount}
        </div>
        <div>
          <strong>Duration:</strong> {computedDuration.toFixed(1)}s
        </div>
      </div>

      {/* Progress Bar */}
      <div style={{
        display: "flex",
        gap: "10px",
        alignItems: "center",
        marginBottom: "15px"
      }}>
        <div style={{
          flex: 1,
          height: "6px",
          background: "#eee",
          borderRadius: "3px",
          position: "relative",
          overflow: "hidden"
        }}>
          <div style={{
            height: "100%",
            width: `${progressPercent}%`,
            background: "#4CAF50",
            borderRadius: "3px",
            transition: "width 0.05s linear"
          }} />
        </div>
        <div style={{
          fontSize: "12px",
          color: "#999",
          minWidth: "50px",
          textAlign: "right"
        }}>
          {currentTime.toFixed(1)}s / {computedDuration.toFixed(1)}s
        </div>
      </div>

      {/* Controls */}
      <div style={{
        display: "flex",
        gap: "10px",
        justifyContent: "center"
      }}>
        <button
          onClick={handlePlay}
          style={{
            padding: "8px 16px",
            background: !isPlaying ? "#4CAF50" : "#2196F3",
            color: "white",
            border: "none",
            borderRadius: "4px",
            cursor: "pointer",
            fontSize: "14px",
            fontWeight: "600"
          }}
        >
          {!isPlaying ? "Play" : "Pause"}
        </button>
        
        <button
          onClick={handleRestart}
          style={{
            padding: "8px 16px",
            background: "#FF9800",
            color: "white",
            border: "none",
            borderRadius: "4px",
            cursor: "pointer",
            fontSize: "14px",
            fontWeight: "600"
          }}
        >
          Restart
        </button>
      </div>

      {/* State info (optional debug) */}
      {isPaused && (
        <div style={{
          marginTop: "10px",
          fontSize: "12px",
          color: "#FF9800",
          fontWeight: "600",
          textAlign: "center"
        }}>
          ⏸ Paused
        </div>
      )}
    </div>
  );
}
