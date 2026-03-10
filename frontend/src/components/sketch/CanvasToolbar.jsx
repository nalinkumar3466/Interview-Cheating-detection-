// frontend/src/components/sketch/CanvasToolbar.jsx
import React from "react";

export default function CanvasToolbar({ tool, setTool, undo, clear, brushSize, setBrushSize }) {
  return (
    <div style={{ marginBottom: 10, display: "flex", gap: 10 }}>
      <button onClick={() => setTool("pen")}>
        {tool === "pen" ? "✏️ Pen (Active)" : "Pen"}
      </button>

      <button onClick={() => setTool("eraser")}>
        {tool === "eraser" ? "🧽 Eraser (Active)" : "Eraser"}
      </button>

      <button onClick={undo}>↩ Undo</button>
      <button onClick={clear}>🗑 Clear</button>
      
      {/* Brush Size Slider */}
      <div style={{ display: "flex", alignItems: "center", gap: 5 }}>
        <span>Size</span>
        <input
          type="range"
          min="1"
          max="30"
          value={brushSize}
          onChange={(e) => setBrushSize(Number(e.target.value))}
        />
        <span>{brushSize}</span>
      </div>
      
    </div>
    
  );
}