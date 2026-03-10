/**
 * CanvasDrawingQuestion.jsx
 * 
 * Main canvas drawing component for interview questions.
 * 
 * Features:
 * - HTML5 Canvas API for drawing
 * - Pen and eraser tools with customizable color/width
 * - Autosave to localStorage every 2 seconds
 * - Stroke timeline with timestamps
 * - Export as PNG base64
 * - Performance optimized with requestAnimationFrame throttling
 */

import React, { useRef, useEffect, useState } from "react";
import useCanvasDrawingWithAutosave from "./useCanvasDrawingWithAutosave";
import CanvasDrawingToolbar from "./CanvasDrawingToolbar";

export default function CanvasDrawingQuestion({
  questionId,
  interviewId,
  onSubmit
}) {
  const canvasRef = useRef(null);
  const contextRef = useRef(null);
  const rafRef = useRef(null);
  const [duration, setDuration] = useState(0);

  const {
    tool,
    setTool,
    color,
    setColor,
    width,
    setWidth,
    strokes,
    isDrawing,
    startDrawing,
    draw,
    endDrawing,
    undo,
    clear,
    getDuration
  } = useCanvasDrawingWithAutosave();

  // Initialize canvas
  useEffect(() => {
    const canvas = canvasRef.current;
    const context = canvas.getContext("2d");

    // Set canvas size (responsive but maintain aspect ratio)
    const rect = canvas.parentElement.getBoundingClientRect();
    const dpr = window.devicePixelRatio || 1;

    canvas.width = rect.width * dpr;
    canvas.height = 500 * dpr;

    context.scale(dpr, dpr);
    context.fillStyle = "#ffffff";
    context.fillRect(0, 0, rect.width, 500);
    context.lineCap = "round";
    context.lineJoin = "round";

    contextRef.current = context;
  }, []);

  // Redraw canvas when strokes change
  useEffect(() => {
    const canvas = canvasRef.current;
    const context = contextRef.current;

    if (!context) return;

    // Clear canvas
    context.fillStyle = "#ffffff";
    context.fillRect(0, 0, canvas.width, canvas.height);

    // Redraw all strokes
    strokes.forEach((stroke) => {
      const points = stroke.points;
      if (points.length === 0) return;

      if (stroke.tool === "eraser") {
        context.clearRect(
          points[0].x - stroke.width / 2,
          points[0].y - stroke.width / 2,
          stroke.width,
          stroke.width
        );

        for (let i = 1; i < points.length; i++) {
          context.clearRect(
            points[i].x - stroke.width / 2,
            points[i].y - stroke.width / 2,
            stroke.width,
            stroke.width
          );
        }
      } else {
        context.strokeStyle = stroke.color || "#000000";
        context.lineWidth = stroke.width || 3;
        context.beginPath();
        context.moveTo(points[0].x, points[0].y);

        for (let i = 1; i < points.length; i++) {
          context.lineTo(points[i].x, points[i].y);
        }

        context.stroke();
      }
    });
  }, [strokes]);

  // Update duration timer
  useEffect(() => {
    const interval = setInterval(() => {
      setDuration(getDuration());
    }, 1000);

    return () => clearInterval(interval);
  }, [getDuration]);

  // Handle mouse down
  const handleMouseDown = (e) => {
    const canvas = canvasRef.current;
    const rect = canvas.getBoundingClientRect();
    const x = e.clientX - rect.left;
    const y = e.clientY - rect.top;

    startDrawing(x, y);
  };

  // Handle mouse move with throttling
  const handleMouseMove = (e) => {
    if (!isDrawing) return;

    if (rafRef.current) {
      cancelAnimationFrame(rafRef.current);
    }

    rafRef.current = requestAnimationFrame(() => {
      const canvas = canvasRef.current;
      const rect = canvas.getBoundingClientRect();
      const x = e.clientX - rect.left;
      const y = e.clientY - rect.top;

      draw(x, y);

      // Live drawing preview
      const context = contextRef.current;
      if (context) {
        const currentStroke = {
          tool,
          color,
          width,
          points: []
        };

        context.strokeStyle = color;
        context.lineWidth = width;
        context.lineCap = "round";
        context.lineJoin = "round";
      }
    });
  };

  // Handle mouse up
  const handleMouseUp = () => {
    if (rafRef.current) {
      cancelAnimationFrame(rafRef.current);
    }
    endDrawing();
  };

  // Export canvas as PNG base64
  const exportAsPNG = () => {
    const canvas = canvasRef.current;
    return canvas.toDataURL("image/png");
  };

  // Handle submit
  const handleSubmit = () => {
    const pngData = exportAsPNG();

    if (onSubmit) {
      onSubmit({
        questionId,
        strokes: strokes,
        finalImage: pngData,
        duration: getDuration(),
        strokeCount: strokes.length
      });
    }
  };

  return (
    <div style={styles.container}>
      <div style={styles.header}>
        <h3 style={styles.title}>Draw Your Solution</h3>
        <p style={styles.subtitle}>
          Use the tools below to sketch your answer. Your work is automatically saved.
        </p>
      </div>

      <CanvasDrawingToolbar
        tool={tool}
        setTool={setTool}
        color={color}
        setColor={setColor}
        width={width}
        setWidth={setWidth}
        undo={undo}
        clear={clear}
        onSubmit={handleSubmit}
        strokeCount={strokes.length}
        duration={duration}
      />

      <div style={styles.canvasWrapper}>
        <canvas
          ref={canvasRef}
          onMouseDown={handleMouseDown}
          onMouseMove={handleMouseMove}
          onMouseUp={handleMouseUp}
          onMouseLeave={handleMouseUp}
          style={styles.canvas}
        />
      </div>

      <div style={styles.footer}>
        <p style={styles.footerText}>
          💾 Auto-saving every 2 seconds • 🖱️ Draw smoothly using pen or eraser
        </p>
      </div>
    </div>
  );
}

const styles = {
  container: {
    borderRadius: "8px",
    overflow: "hidden",
    boxShadow: "0 2px 8px rgba(0,0,0,0.1)",
    backgroundColor: "#fff",
    marginBottom: "20px"
  },
  header: {
    padding: "16px",
    backgroundColor: "#f8f9fa",
    borderBottom: "1px solid #dee2e6"
  },
  title: {
    margin: "0 0 8px 0",
    fontSize: "18px",
    fontWeight: "600",
    color: "#333"
  },
  subtitle: {
    margin: "0",
    fontSize: "14px",
    color: "#666"
  },
  canvasWrapper: {
    position: "relative",
    backgroundColor: "#fff",
    overflow: "auto",
    maxHeight: "600px"
  },
  canvas: {
    display: "block",
    width: "100%",
    height: "auto",
    cursor: "crosshair",
    touchAction: "none"
  },
  footer: {
    padding: "12px",
    backgroundColor: "#f8f9fa",
    borderTop: "1px solid #dee2e6",
    textAlign: "center"
  },
  footerText: {
    margin: "0",
    fontSize: "12px",
    color: "#666",
    fontWeight: "500"
  }
};
