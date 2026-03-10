/**
 * useCanvasDrawingWithAutosave.js
 * 
 * Custom hook for canvas drawing with autosave functionality.
 * Manages:
 * - Stroke timeline with pen and eraser tools
 * - Color picker and stroke width
 * - LocalStorage autosave every 2 seconds
 * - Undo/redo operations
 * - Performance optimization with throttling
 */

import { useState, useCallback, useRef, useEffect } from "react";

const AUTOSAVE_INTERVAL = 2000; // 2 seconds
const STORAGE_KEY = "canvas_drawing_autosave";

export default function useCanvasDrawingWithAutosave() {
  const [tool, setTool] = useState("pen");
  const [color, setColor] = useState("#000000");
  const [width, setWidth] = useState(3);
  const [strokes, setStrokes] = useState([]);
  const [isDrawing, setIsDrawing] = useState(false);
  const [startTime] = useState(Date.now());

  const isDrawingRef = useRef(false);
  const autosaveTimeoutRef = useRef(null);
  const currentStrokeRef = useRef(null);

  // Load from localStorage on mount
  useEffect(() => {
    try {
      const saved = localStorage.getItem(STORAGE_KEY);
      if (saved) {
        const data = JSON.parse(saved);
        setStrokes(data.strokes || []);
      }
    } catch (e) {
      console.warn("Failed to load autosaved canvas data:", e);
    }
  }, []);

  // Autosave to localStorage
  useEffect(() => {
    if (autosaveTimeoutRef.current) {
      clearTimeout(autosaveTimeoutRef.current);
    }

    autosaveTimeoutRef.current = setTimeout(() => {
      try {
        localStorage.setItem(STORAGE_KEY, JSON.stringify({ strokes }));
      } catch (e) {
        console.warn("Failed to autosave canvas:", e);
      }
    }, AUTOSAVE_INTERVAL);

    return () => {
      if (autosaveTimeoutRef.current) {
        clearTimeout(autosaveTimeoutRef.current);
      }
    };
  }, [strokes]);

  const startDrawing = useCallback((x, y) => {
    isDrawingRef.current = true;
    setIsDrawing(true);

    currentStrokeRef.current = {
      tool,
      color,
      width,
      points: [{ x, y, timestamp: Date.now() - startTime }]
    };
  }, [tool, color, width, startTime]);

  const draw = useCallback((x, y) => {
    if (!isDrawingRef.current || !currentStrokeRef.current) return;

    currentStrokeRef.current.points.push({
      x,
      y,
      timestamp: Date.now() - startTime
    });
  }, [startTime]);

  const endDrawing = useCallback(() => {
    if (!isDrawingRef.current || !currentStrokeRef.current) return;

    isDrawingRef.current = false;
    setIsDrawing(false);

    setStrokes((prev) => [...prev, currentStrokeRef.current]);
    currentStrokeRef.current = null;
  }, []);

  const undo = useCallback(() => {
    setStrokes((prev) => {
      if (prev.length === 0) return prev;
      return prev.slice(0, -1);
    });
  }, []);

  const clear = useCallback(() => {
    setStrokes([]);
    try {
      localStorage.removeItem(STORAGE_KEY);
    } catch (e) {
      console.warn("Failed to clear autosave:", e);
    }
  }, []);

  const getDuration = useCallback(() => {
    return Math.floor((Date.now() - startTime) / 1000);
  }, [startTime]);

  return {
    // State
    tool,
    color,
    width,
    strokes,
    isDrawing,

    // Setters
    setTool,
    setColor,
    setWidth,

    // Drawing methods
    startDrawing,
    draw,
    endDrawing,
    undo,
    clear,

    // Utility
    getDuration
  };
}
