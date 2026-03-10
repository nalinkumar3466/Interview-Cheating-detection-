/**
 * CanvasDrawingToolbar.jsx
 * 
 * Toolbar for canvas drawing controls:
 * - Pen/Eraser tool selection
 * - Color picker (pen only)
 * - Stroke width selector
 * - Undo/Clear buttons
 * - Submit button
 */

import React from "react";

export default function CanvasDrawingToolbar({
  tool,
  setTool,
  color,
  setColor,
  width,
  setWidth,
  undo,
  clear,
  onSubmit,
  strokeCount = 0,
  duration = 0
}) {
  return (
    <div className="canvas-toolbar" style={styles.toolbar}>
      {/* Tool Selection */}
      <div style={styles.toolGroup}>
        <button
          onClick={() => setTool("pen")}
          style={{
            ...styles.toolButton,
            ...(tool === "pen" ? styles.toolButtonActive : {})
          }}
          title="Pen tool"
        >
          ✏️ Pen
        </button>
        <button
          onClick={() => setTool("eraser")}
          style={{
            ...styles.toolButton,
            ...(tool === "eraser" ? styles.toolButtonActive : {})
          }}
          title="Eraser tool"
        >
          🧹 Eraser
        </button>
      </div>

      {/* Color Picker (only for pen) */}
      {tool === "pen" && (
        <div style={styles.colorGroup}>
          <label htmlFor="color-picker" style={styles.label}>
            Color:
          </label>
          <input
            id="color-picker"
            type="color"
            value={color}
            onChange={(e) => setColor(e.target.value)}
            style={styles.colorInput}
            title="Pick color"
          />
        </div>
      )}

      {/* Stroke Width */}
      <div style={styles.widthGroup}>
        <label htmlFor="width-slider" style={styles.label}>
          Width:
        </label>
        <input
          id="width-slider"
          type="range"
          min="1"
          max="20"
          value={width}
          onChange={(e) => setWidth(parseInt(e.target.value))}
          style={styles.widthSlider}
          title="Adjust stroke width"
        />
        <span style={styles.widthValue}>{width}px</span>
      </div>

      {/* Action Buttons */}
      <div style={styles.actionGroup}>
        <button
          onClick={undo}
          style={styles.actionButton}
          title="Undo last stroke"
        >
          ↩️ Undo
        </button>
        <button
          onClick={clear}
          style={styles.actionButton}
          title="Clear all strokes"
        >
          🗑️ Clear
        </button>
      </div>

      {/* Metadata Display */}
      <div style={styles.metadataGroup}>
        <span style={styles.metadata}>
          Strokes: {strokeCount}
        </span>
        <span style={styles.metadata}>
          Duration: {duration}s
        </span>
      </div>

      {/* Submit Button */}
      <button
        onClick={onSubmit}
        style={styles.submitButton}
        title="Submit drawing"
      >
        ✅ Submit Drawing
      </button>
    </div>
  );
}

const styles = {
  toolbar: {
    display: "flex",
    alignItems: "center",
    gap: "16px",
    padding: "12px",
    backgroundColor: "#f8f9fa",
    borderBottom: "1px solid #ddd",
    borderRadius: "4px 4px 0 0",
    flexWrap: "wrap"
  },
  toolGroup: {
    display: "flex",
    gap: "8px"
  },
  toolButton: {
    padding: "8px 12px",
    backgroundColor: "#fff",
    border: "1px solid #ddd",
    borderRadius: "4px",
    cursor: "pointer",
    fontSize: "14px",
    fontWeight: "500",
    transition: "all 0.2s"
  },
  toolButtonActive: {
    backgroundColor: "#007bff",
    color: "#fff",
    borderColor: "#0056b3"
  },
  colorGroup: {
    display: "flex",
    alignItems: "center",
    gap: "8px"
  },
  label: {
    fontSize: "14px",
    fontWeight: "500",
    color: "#333"
  },
  colorInput: {
    width: "100px",
    height: "600px",
    border: "1px solid #ddd",
    borderRadius: "4px",
    cursor: "pointer"
  },
  widthGroup: {
    display: "flex",
    alignItems: "center",
    gap: "8px"
  },
  widthSlider: {
    width: "100px",
    cursor: "pointer"
  },
  widthValue: {
    fontSize: "12px",
    color: "#666",
    minWidth: "35px"
  },
  actionGroup: {
    display: "flex",
    gap: "8px"
  },
  actionButton: {
    padding: "8px 12px",
    backgroundColor: "#fff",
    border: "1px solid #ddd",
    borderRadius: "4px",
    cursor: "pointer",
    fontSize: "14px",
    transition: "background-color 0.2s",
    "&:hover": {
      backgroundColor: "#f0f0f0"
    }
  },
  metadataGroup: {
    display: "flex",
    gap: "12px",
    marginLeft: "auto"
  },
  metadata: {
    fontSize: "13px",
    color: "#666",
    fontWeight: "500"
  },
  submitButton: {
    padding: "10px 16px",
    backgroundColor: "#28a745",
    color: "#fff",
    border: "none",
    borderRadius: "4px",
    cursor: "pointer",
    fontSize: "14px",
    fontWeight: "600",
    transition: "background-color 0.2s",
    "&:hover": {
      backgroundColor: "#218838"
    }
  }
};
