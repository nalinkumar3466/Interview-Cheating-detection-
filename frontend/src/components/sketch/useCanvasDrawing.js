// frontend/src/components/sketch/useCanvasDrawing.js
import { useState } from "react";

export default function useCanvasDrawing() {
  const [tool, setTool] = useState("pen");
  const [lines, setLines] = useState([]);
  const [isDrawing, setIsDrawing] = useState(false);
  const [brushSize, setBrushSize] = useState(3);
  const [currentLineId, setCurrentLineId] = useState(null);

  function startDrawing(pos) {
    const now = Date.now();

    const newLine = {
      id: crypto.randomUUID(),
      tool,
      strokeWidth: brushSize,
      color: "#000000",
      startedAt: now,
      points: [
        { x: pos.x, y: pos.y, t: now }
      ]
    };

    setIsDrawing(true);
    setCurrentLineId(newLine.id);
    setLines(prev => [...prev, newLine]);
  }

  function draw(pos) {
    if (!isDrawing || !currentLineId) return;

    const now = Date.now();

    setLines(prev =>
      prev.map(line => {
        if (line.id !== currentLineId) return line;

        return {
          ...line,
          points: [
            ...line.points,
            { x: pos.x, y: pos.y, t: now }
          ]
        };
      })
    );
  }

  function endDrawing() {
    setIsDrawing(false);
    setCurrentLineId(null);
  }

  function undo() {
    setLines(prev => prev.slice(0, -1));
  }

  function clear() {
    setLines([]);
  }

  return {
    tool,
    setTool,
    lines,
    setLines,
    startDrawing,
    draw,
    endDrawing,
    undo,
    clear,
    brushSize,
    setBrushSize
  };
}