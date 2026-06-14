import React from "react";
import TradingViewChart from "./TradingViewChart";
import "../Styles/chartSection.css";

const ChartSection = ({ ticker, isLoading, analysis }) => {
  // Only render the chart if analysis is complete and not loading
  if (!ticker || isLoading || !analysis) {
    return null;
  }

  return (
    <div className="chart-section">
      <h3>Interactive Stock Chart</h3>
      <TradingViewChart symbol={ticker} />
    </div>
  );
};

export default ChartSection;
