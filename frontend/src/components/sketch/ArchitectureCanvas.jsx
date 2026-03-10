// frontend/src/components/sketch/ArchitectureCanvas.jsx
import React, { useRef, useEffect, useState, useImperativeHandle, forwardRef } from "react";
import { Stage, Layer, Line } from "react-konva";
import useCanvasDrawing from "./useCanvasDrawing";
import CanvasToolbar from "./CanvasToolbar";

const ArchitectureCanvas = forwardRef(function ArchitectureCanvas({
  interviewId,
  questionId,
  onSubmit
}, ref) {
  const stageRef = useRef(null);
  const containerRef = useRef(null);

  const {
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
  } = useCanvasDrawing();


  const [stageSize, setStageSize] = useState({
    width: 800,
    height: 550
  });
// resize effect
  useEffect(() => {
    function updateSize() {
      if (!containerRef.current) return;

      const width = containerRef.current.offsetWidth;

      setStageSize({
        width: width,
        height: 550
      });
    }

    updateSize();
    window.addEventListener("resize", updateSize);
    return () => window.removeEventListener("resize", updateSize);
  }, []);
//autosave
  useEffect(() => {
  if (!interviewId || !questionId) return;

  const interval = setInterval(() => {
    localStorage.setItem(
      `sketch-${interviewId}-${questionId}`,
      JSON.stringify(lines)
    );
  }, 2000);

  return () => clearInterval(interval);
}, [lines, interviewId, questionId]);
//load saved sketch
useEffect(() => {
  if (!interviewId || !questionId) return;

  const saved = localStorage.getItem(
    `sketch-${interviewId}-${questionId}`
  );

  if (saved) {
    try {
      setLines(JSON.parse(saved));
    } catch (e) {
      console.error("Failed to load saved sketch");
    }
  }
}, [interviewId, questionId]);

  
  function handleMouseDown(e) {
    const pos = e.target.getStage().getPointerPosition();
    startDrawing(pos);
  }

  function handleMouseMove(e) {
    const pos = e.target.getStage().getPointerPosition();
    draw(pos);
  }

  function handleMouseUp() {
    endDrawing();
  }

  function handleSubmit() {
    const stage = stageRef.current;
    const dataURL = stage.toDataURL({ pixelRatio: 2 });

     localStorage.removeItem(
    `sketch-${interviewId}-${questionId}`
  );


    onSubmit({
      strokes: lines,
      pngData: dataURL
    });
  }

  // Expose submit method via ref so parent can trigger submission
  useImperativeHandle(ref, () => ({
    submit: handleSubmit
  }));

  return (
    <div ref={containerRef}>
      <CanvasToolbar
        tool={tool}
        setTool={setTool}
        undo={undo}
        clear={clear}
        brushSize={brushSize}
        setBrushSize={setBrushSize}
      />

      <Stage
        width={stageSize.width}
        height={stageSize.height}
        onMouseDown={handleMouseDown}
        onMouseMove={handleMouseMove}   
        onMouseUp={handleMouseUp}       
        ref={stageRef}
        style={{
          border: "1px solid #ccc",
          background: "#fff",
          cursor: tool === "eraser" ? "not-allowed" : "crosshair"
        }}
      >
        <Layer>
          {lines.map((line, i) => (
            <Line
              key={i}
              points={line.points.flatMap(p => [p.x, p.y])}
              stroke="black"
              strokeWidth={line.strokeWidth}
              tension={0.5}
              lineCap="round"
              globalCompositeOperation={
                line.tool === "eraser"
                  ? "destination-out"
                  : "source-over"
              }
            />
          ))}
        </Layer>
      </Stage>
    </div>
  );
});

export default ArchitectureCanvas;