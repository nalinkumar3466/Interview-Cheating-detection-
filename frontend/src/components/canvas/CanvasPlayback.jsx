/**
 * CanvasPlayback.jsx
 * 
 * Component to replay canvas drawing strokes in sequence.
 * Shows the drawing animation based on stroke timeline data.
 */

import React, { useRef, useEffect, useState } from "react";

export default function CanvasPlayback({ strokes, metadata = {} }) {
  const canvasRef = useRef(null);
  const [isPlaying, setIsPlaying] = useState(false);
  const [currentStrokeIndex, setCurrentStrokeIndex] = useState(0);
  const [playbackSpeed, setPlaybackSpeed] = useState(1);
  const timeoutRef = useRef(null);

  // Initialize canvas
  useEffect(() => {
    const canvas = canvasRef.current;
    const context = canvas.getContext("2d");

    const dpr = window.devicePixelRatio || 1;
    const rect = canvas.parentElement.getBoundingClientRect();

    canvas.width = rect.width * dpr;
    canvas.height = 500 * dpr;

    context.scale(dpr, dpr);
    context.fillStyle = "#ffffff";
    context.fillRect(0, 0, rect.width, 500);
    context.lineCap = "round";
    context.lineJoin = "round";
  }, []);

  // Draw all strokes up to current index
  useEffect(() => {
    const canvas = canvasRef.current;
    const context = canvas.getContext("2d");

    // Clear canvas
    context.fillStyle = "#ffffff";
    context.fillRect(0, 0, canvas.width, canvas.height);

    // Draw strokes
    for (let i = 0; i < currentStrokeIndex && i < strokes.length; i++) {
      const stroke = strokes[i];
      const points = stroke.points || [];
      if (points.length === 0) continue;

      if (stroke.tool === "eraser") {
        context.clearRect(
          points[0].x - stroke.width / 2,
          points[0].y - stroke.width / 2,
          stroke.width,
          stroke.width
        );

        for (let j = 1; j < points.length; j++) {
          context.clearRect(
            points[j].x - stroke.width / 2,
            points[j].y - stroke.width / 2,
            stroke.width,
            stroke.width
          );
        }
      } else {
        context.strokeStyle = stroke.color || "#000000";
        context.lineWidth = stroke.width || 3;
        context.beginPath();
        context.moveTo(points[0].x, points[0].y);

        for (let j = 1; j < points.length; j++) {
          context.lineTo(points[j].x, points[j].y);
        }

        context.stroke();
      }
    }
  }, [currentStrokeIndex, strokes]);

  const play = () => {
    if (!strokes || strokes.length === 0) return;
    setIsPlaying(true);
    playNextStroke(currentStrokeIndex);
  };

  const playNextStroke = (index) => {
    if (index >= strokes.length) {
      setIsPlaying(false);
      return;
    }

    setCurrentStrokeIndex(index + 1);

    // Calculate delay based on time between strokes
    let delay = 100; // Default 100ms
    if (index > 0 && strokes[index - 1].points && strokes[index].points) {
      const lastStroke = strokes[index - 1];
      const currentStroke = strokes[index];
      const lastPoint =
        lastStroke.points[lastStroke.points.length - 1] || {};
      const firstPoint = currentStroke.points[0];

      if (lastPoint.timestamp && firstPoint.timestamp) {
        delay = Math.max(
          50,
          (firstPoint.timestamp - lastPoint.timestamp) / playbackSpeed
        );
      }
    }

    timeoutRef.current = setTimeout(
      () => playNextStroke(index + 1),
      delay
    );
  };

  const pause = () => {
    setIsPlaying(false);
    if (timeoutRef.current) clearTimeout(timeoutRef.current);
  };

  const reset = () => {
    setIsPlaying(false);
    setCurrentStrokeIndex(0);
    if (timeoutRef.current) clearTimeout(timeoutRef.current);
  };

  return (
    <div style={styles.container}>
      <div style={styles.header}>
        <h4 style={styles.title}>Playback View</h4>
        <p style={styles.subtitle}>Replay the drawing to review the candidate's work</p>
      </div>

      <div style={styles.controls}>
        <button
          onClick={isPlaying ? pause : play}
          style={styles.button}
          disabled={currentStrokeIndex >= strokes.length && !isPlaying}
        >
          {isPlaying ? "⏸ Pause" : "▶ Play"}
        </button>
        <button onClick={reset} style={styles.button}>
          🔄 Reset
        </button>

        <div style={styles.speedControl}>
          <label htmlFor="playback-speed" style={styles.label}>
            Speed:
          </label>
          <select
            id="playback-speed"
            value={playbackSpeed}
            onChange={(e) => setPlaybackSpeed(parseFloat(e.target.value))}
            style={styles.select}
          >
            <option value={0.5}>0.5x</option>
            <option value={1}>1x</option>
            <option value={1.5}>1.5x</option>
            <option value={2}>2x</option>
          </select>
        </div>

        <div style={styles.progressInfo}>
          <span style={styles.progressText}>
            {currentStrokeIndex} / {strokes.length} strokes
          </span>
        </div>
      </div>

      <canvas
        ref={canvasRef}
        style={styles.canvas}
      />

      {metadata && (
        <div style={styles.metadata}>
          <span>Duration: {metadata.duration || "N/A"}s</span>
          <span>•</span>
          <span>Strokes: {metadata.strokeCount || strokes.length}</span>
        </div>
      )}
    </div>
  );
}

const styles = {
  container: {
    borderRadius: "8px",
    overflow: "hidden",
    backgroundColor: "#fff",
    boxShadow: "0 2px 8px rgba(0,0,0,0.1)"
  },
  header: {
    padding: "16px",
    backgroundColor: "#f8f9fa",
    borderBottom: "1px solid #dee2e6"
  },
  title: {
    margin: "0 0 4px 0",
    fontSize: "16px",
    fontWeight: "600",
    color: "#333"
  },
  subtitle: {
    margin: "0",
    fontSize: "13px",
    color: "#666"
  },
  controls: {
    display: "flex",
    alignItems: "center",
    gap: "12px",
    padding: "12px",
    backgroundColor: "#f8f9fa",
    borderBottom: "1px solid #dee2e6",
    flexWrap: "wrap"
  },
  button: {
    padding: "8px 12px",
    backgroundColor: "#007bff",
    color: "#fff",
    border: "none",
    borderRadius: "4px",
    cursor: "pointer",
    fontSize: "13px",
    fontWeight: "500",
    transition: "background-color 0.2s"
  },
  speedControl: {
    display: "flex",
    alignItems: "center",
    gap: "8px"
  },
  label: {
    fontSize: "13px",
    fontWeight: "500",
    color: "#333"
  },
  select: {
    padding: "6px 8px",
    border: "1px solid #ddd",
    borderRadius: "4px",
    fontSize: "13px",
    backgroundColor: "#fff",
    cursor: "pointer"
  },
  progressInfo: {
    marginLeft: "auto"
  },
  progressText: {
    fontSize: "13px",
    fontWeight: "500",
    color: "#666"
  },
  canvas: {
    display: "block",
    width: "100%",
    height: "auto",
    backgroundColor: "#fff",
    borderTop: "1px solid #dee2e6"
  },
  metadata: {
    display: "flex",
    gap: "8px",
    alignItems: "center",
    justifyContent: "center",
    padding: "12px",
    backgroundColor: "#f8f9fa",
    fontSize: "13px",
    color: "#666",
    borderTop: "1px solid #dee2e6"
  }
};
