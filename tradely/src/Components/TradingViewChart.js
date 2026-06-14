import React, { useEffect } from "react";

const TradingViewChart = ({ symbol }) => {
  useEffect(() => {
    const script = document.createElement("script");
    script.src = "https://s3.tradingview.com/tv.js";
    script.async = true;
    script.onload = () => {
      new window.TradingView.widget({
        container_id: "tradingview_chart",
        width: "100%",
        height: 500,
        symbol: symbol,
        interval: "D",
        timezone: "Etc/UTC",
        theme: "dark",
        style: "1",
        locale: "en",
        toolbar_bg: "#f1f3f6",
        enable_publishing: false,
        allow_symbol_change: true,
      });
    };
    document.body.appendChild(script);
  }, [symbol]);

  return <div id="tradingview_chart"></div>;
};

export default TradingViewChart;
