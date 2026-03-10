// frontend/src/components/admin/CanvasGradingPanel.jsx
import React, { useState } from "react";
import CanvasReplay from "./CanvasReplay";
import api from "../../services/api";

/**
 * CanvasGradingPanel - Admin grading interface for canvas submissions
 * 
 * Props:
 * - response: Canvas response object with strokes, metadata, and existing scores
 * - interview_id: Interview ID for API calls
 * - onUpdateGrade: Callback when grading is saved
 */
export default function CanvasGradingPanel({ 
  response, 
  interview_id, 
  onUpdateGrade = null 
}) {
  const [structureScore, setStructureScore] = useState(
    response?.structure_score ?? 0
  );
  const [clarityScore, setClarityScore] = useState(
    response?.clarity_score ?? 0
  );
  const [completenessScore, setCompletenessScore] = useState(
    response?.completeness_score ?? 0
  );
  const [feedback, setFeedback] = useState(response?.rubric_feedback ?? "");
  
  const [isSaving, setIsSaving] = useState(false);
  const [saveStatus, setSaveStatus] = useState("");
  const [computedMetadata, setComputedMetadata] = useState({
  strokeCount: response?.stroke_count,
  duration: response?.duration_ms
    ? Math.round(response.duration_ms / 1000)
    : undefined
});

  /**
   * Calculate overall score from component scores
   */
  const calculateOverallScore = () => {
    const scores = [
      parseFloat(structureScore),
      parseFloat(clarityScore),
      parseFloat(completenessScore)
    ].filter(s => !isNaN(s));
    
    if (scores.length === 0) return 0;
    return (scores.reduce((a, b) => a + b, 0) / scores.length).toFixed(2);
  };

  const overallScore = calculateOverallScore();

  /**
   * Save grading rubric to backend
   */
  const handleSaveGrade = async (e) => {
    e.preventDefault();
    
    setIsSaving(true);
    setSaveStatus("");
    
    try {
      const rubricData = {
        structure_score: parseFloat(structureScore),
        clarity_score: parseFloat(clarityScore),
        completeness_score: parseFloat(completenessScore),
        feedback: feedback || null
      };

      const response_result = await api.post(
        `/interviews/${interview_id}/canvas-responses/${response.id}/grade`,
        rubricData
      );

      setSaveStatus("✓ Grading saved successfully!");
      
      if (onUpdateGrade) {
        onUpdateGrade({
          ...response,
          structure_score: rubricData.structure_score,
          clarity_score: rubricData.clarity_score,
          completeness_score: rubricData.completeness_score,
          overall_score: parseFloat(overallScore),
          rubric_feedback: feedback
        });
      }

      // Clear status after 3 seconds
      setTimeout(() => setSaveStatus(""), 3000);
    } catch (err) {
      console.error("Failed to save grading:", err);
      setSaveStatus("✗ Failed to save grading. Please try again.");
    } finally {
      setIsSaving(false);
    }
  };

  return (
    <div style={{
      border: "1px solid #ddd",
      borderRadius: "8px",
      padding: "20px",
      background: "#f9f9f9",
      marginBottom: "20px"
    }}>
      <h3 style={{
        marginTop: 0,
        marginBottom: "20px",
        fontSize: "18px",
        fontWeight: "700",
        color: "#333"
      }}>
        🎨 Canvas Grading
      </h3>

      {/* Replay Section */}
      <div style={{ marginBottom: "25px" }}>
        <h4 style={{
          fontSize: "14px",
          fontWeight: "600",
          color: "#555",
          marginBottom: "12px"
        }}>
          Drawing Replay
        </h4>
        {response?.strokes_json && response.strokes_json.length > 0 ? (
          <CanvasReplay 
            strokes={response.strokes_json}
            metadata={{
            strokeCount: response?.stroke_count,
            duration: response?.duration_ms
              ? Math.round(response.duration_ms / 1000)
              : undefined
            }}  
            onMetadataCompute={setComputedMetadata}
          />
        ) : (
          <div style={{
            padding: "20px",
            background: "#fff",
            border: "1px solid #ddd",
            borderRadius: "4px",
            textAlign: "center",
            color: "#999"
          }}>
            No strokes data available for replay
          </div>
        )}
      </div>

      {/* Drawing Info */}
      <div style={{
        display: "flex",
        gap: "20px",
        marginBottom: "25px",
        padding: "12px",
        background: "#fff",
        borderRadius: "4px",
        border: "1px solid #eee",
        fontSize: "13px",
        color: "#666"
      }}>
        {computedMetadata?.strokeCount !== undefined && (
          <div>
            <strong>Strokes:</strong> {computedMetadata.strokeCount}
          </div>
        )}
        {computedMetadata?.duration !== undefined && (
          <div>
            <strong>Duration:</strong> {computedMetadata.duration}s
          </div>
        )}
        {response?.created_at && (
          <div>
            <strong>Submitted:</strong> {new Date(response.created_at).toLocaleString()}
          </div>
        )}
      </div>

      {/* Grading Form */}
      <form onSubmit={handleSaveGrade} style={{
        background: "#fff",
        padding: "20px",
        borderRadius: "8px",
        border: "1px solid #eee"
      }}>
        <h4 style={{
          fontSize: "14px",
          fontWeight: "600",
          color: "#333",
          marginBottom: "15px",
          marginTop: 0
        }}>
          Rubric Scores (0-5)
        </h4>

        {/* Score Inputs */}
        <div style={{
          display: "grid",
          gridTemplateColumns: "1fr 1fr 1fr",
          gap: "15px",
          marginBottom: "20px"
        }}>
          {/* Structure Score */}
          <div>
            <label style={{
              display: "block",
              fontSize: "12px",
              fontWeight: "600",
              color: "#555",
              marginBottom: "6px"
            }}>
              Structure
            </label>
            <input
              type="number"
              min="0"
              max="5"
              step="0.5"
              value={structureScore}
              onChange={(e) => setStructureScore(e.target.value)}
              style={{
                width: "100%",
                padding: "8px 10px",
                border: "1px solid #ddd",
                borderRadius: "4px",
                fontSize: "14px",
                boxSizing: "border-box"
              }}
            />
            <div style={{
              fontSize: "11px",
              color: "#999",
              marginTop: "4px"
            }}>
              Architectural/structural correctness
            </div>
          </div>

          {/* Clarity Score */}
          <div>
            <label style={{
              display: "block",
              fontSize: "12px",
              fontWeight: "600",
              color: "#555",
              marginBottom: "6px"
            }}>
              Clarity
            </label>
            <input
              type="number"
              min="0"
              max="5"
              step="0.5"
              value={clarityScore}
              onChange={(e) => setClarityScore(e.target.value)}
              style={{
                width: "100%",
                padding: "8px 10px",
                border: "1px solid #ddd",
                borderRadius: "4px",
                fontSize: "14px",
                boxSizing: "border-box"
              }}
            />
            <div style={{
              fontSize: "11px",
              color: "#999",
              marginTop: "4px"
            }}>
              Clarity and readability
            </div>
          </div>

          {/* Completeness Score */}
          <div>
            <label style={{
              display: "block",
              fontSize: "12px",
              fontWeight: "600",
              color: "#555",
              marginBottom: "6px"
            }}>
              Completeness
            </label>
            <input
              type="number"
              min="0"
              max="5"
              step="0.5"
              value={completenessScore}
              onChange={(e) => setCompletenessScore(e.target.value)}
              style={{
                width: "100%",
                padding: "8px 10px",
                border: "1px solid #ddd",
                borderRadius: "4px",
                fontSize: "14px",
                boxSizing: "border-box"
              }}
            />
            <div style={{
              fontSize: "11px",
              color: "#999",
              marginTop: "4px"
            }}>
              Completeness of solution
            </div>
          </div>
        </div>

        {/* Overall Score Display */}
        <div style={{
          padding: "12px",
          background: "#f0f5ff",
          borderRadius: "4px",
          marginBottom: "20px",
          textAlign: "center",
          borderLeft: "4px solid #4CAF50"
        }}>
          <div style={{
            fontSize: "12px",
            fontWeight: "600",
            color: "#666",
            marginBottom: "4px"
          }}>
            OVERALL SCORE
          </div>
          <div style={{
            fontSize: "24px",
            fontWeight: "700",
            color: "#4CAF50"
          }}>
            {overallScore}/5
          </div>
        </div>

        {/* Feedback Textarea */}
        <div style={{ marginBottom: "20px" }}>
          <label style={{
            display: "block",
            fontSize: "12px",
            fontWeight: "600",
            color: "#555",
            marginBottom: "8px"
          }}>
            Grader Feedback (Optional)
          </label>
          <textarea
            value={feedback}
            onChange={(e) => setFeedback(e.target.value)}
            placeholder="Provide constructive feedback for the candidate..."
            style={{
              width: "100%",
              padding: "10px",
              border: "1px solid #ddd",
              borderRadius: "4px",
              fontSize: "14px",
              fontFamily: "inherit",
              minHeight: "100px",
              boxSizing: "border-box",
              resize: "vertical"
            }}
          />
        </div>

        {/* Save Status */}
        {saveStatus && (
          <div style={{
            padding: "10px",
            marginBottom: "15px",
            borderRadius: "4px",
            fontSize: "13px",
            fontWeight: "600",
            textAlign: "center",
            background: saveStatus.startsWith("✓") ? "#d4edda" : "#f8d7da",
            color: saveStatus.startsWith("✓") ? "#155724" : "#721c24",
            border: saveStatus.startsWith("✓") ? "1px solid #c3e6cb" : "1px solid #f5c6cb"
          }}>
            {saveStatus}
          </div>
        )}

        {/* Submit Button */}
        <button
          type="submit"
          disabled={isSaving}
          style={{
            width: "100%",
            padding: "12px",
            background: isSaving ? "#ccc" : "#4CAF50",
            color: "white",
            border: "none",
            borderRadius: "4px",
            fontSize: "14px",
            fontWeight: "600",
            cursor: isSaving ? "not-allowed" : "pointer",
            transition: "background-color 0.2s"
          }}
          onMouseEnter={(e) => {
            if (!isSaving) e.target.style.background = "#45a049";
          }}
          onMouseLeave={(e) => {
            if (!isSaving) e.target.style.background = "#4CAF50";
          }}
        >
          {isSaving ? "Saving..." : "Save Grading"}
        </button>
      </form>
    </div>
  );
}
