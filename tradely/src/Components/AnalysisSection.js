import React, { useState, useEffect } from "react";
import "../Styles/analysisSection.css";
import {
  saveAsTXT,
  saveAsJSON,
  saveAsCSV,
  saveAsPDF,
} from "../Utils/fileUtils";

const AnalysisSection = ({ analysis, isLoading, error }) => {
  const [visibleLines, setVisibleLines] = useState([]);
  const [timeouts, setTimeouts] = useState([]);

  // Animate the display of analysis lines
  useEffect(() => {
    if (analysis && analysis.deepthinking_response) {
      console.log("Animating Analysis:", analysis.deepthinking_response);
      const lines = analysis.deepthinking_response.split(". ");
      setVisibleLines([]); // Reset visible lines
      const newTimeouts = [];

      lines.forEach((line, index) => {
        const timeout = setTimeout(() => {
          setVisibleLines((prev) => [...prev, line]);
          console.log("Debug: Adding line:", line);
        }, index * 600); // Adjust delay as needed
        newTimeouts.push(timeout);
      });

      setTimeouts(newTimeouts);

      return () => {
        newTimeouts.forEach((timeout) => clearTimeout(timeout));
      };
    }
  }, [analysis]);

  // Stop/Reset the animation
  const handleStop = () => {
    timeouts.forEach((timeout) => clearTimeout(timeout)); // Clear all timeouts
    setTimeouts([]); // Reset timeouts array
    setVisibleLines([]); // Clear visible lines
  };

  // Save the analysis as a TXT file
  const handleSaveAsTXT = () => {
    if (analysis && analysis.deepthinking_response) {
      saveAsTXT(
        analysis.deepthinking_response,
        `${analysis.symbol || "analysis"}_deepthinking.txt`,
      );
    }
  };

  // Save the entire analysis as a JSON file
  const handleSaveAsJSON = () => {
    if (analysis) {
      saveAsJSON(analysis, `${analysis.symbol || "analysis"}_data.json`);
    }
  };

  // Save the analysis as a PDF file
  const handleSaveAsPDF = () => {
    if (analysis && analysis.deepthinking_response) {
      saveAsPDF(
        analysis.deepthinking_response,
        `${analysis.symbol || "analysis"}_deepthinking.pdf`,
      );
    }
  };

  // Save the analysis as a CSV file
  const handleSaveAsCSV = () => {
    if (analysis && analysis.deepthinking_response) {
      saveAsCSV(
        analysis.deepthinking_response,
        `${analysis.symbol || "analysis"}_deepthinking.csv`,
      );
    }
  };

  return (
    <div className="analysis-section">
      <h3>Stock Analysis</h3>
      {isLoading && <div className="loading"></div>}
      {error && <div className="error">Error: {error}</div>}
      <div className="analysis-output">
        {visibleLines.length > 0 ? (
          visibleLines.map((line, index) => (
            <p
              key={index}
              className={
                line.toLowerCase().includes("recommendation") ? "highlight" : ""
              }
            >
              {line}
            </p>
          ))
        ) : (
          <p>No analysis lines to display.</p>
        )}
      </div>
      <div className="action-buttons">
        <button onClick={handleStop} className="stop-animation-button">
          Stop/Reset
        </button>
        <button onClick={handleSaveAsTXT} className="save-analysis-button">
          Save as TXT
        </button>
        <button onClick={handleSaveAsJSON} className="save-analysis-button">
          Save as JSON
        </button>
        <button onClick={handleSaveAsPDF} className="save-analysis-button">
          Save as PDF
        </button>
        <button onClick={handleSaveAsCSV} className="save-analysis-button">
          Save as CSV
        </button>
      </div>
    </div>
  );
};

export default AnalysisSection;
