import React from "react";
import "../Styles/liveMarketPrices.css";

const LiveMarketPrices = ({ data }) => {
  return (
    <div className="live-market-prices">
      <h2>Live Market Data</h2>
      {Object.keys(data).map((symbol) => {
        const latestData = data[symbol];
        const { current_price, price_5_days_ago } = latestData;
        const price_change = current_price - price_5_days_ago;
        const percentage_change = (
          (price_change / price_5_days_ago) *
          100
        ).toFixed(2);
        const isPositive = price_change >= 0;
        const arrow = isPositive ? "▲" : "▼";
        const arrowColor = isPositive ? "green" : "red";

        return (
          <div className="item-container" key={symbol}>
            <div className="price-info">
              <h3>{symbol}</h3>
              <p>
                <strong>Current Price:</strong> {current_price}
              </p>
              <p
                className={`price-change ${isPositive ? "positive" : "negative"}`}
              >
                {price_change.toFixed(2)} ({percentage_change}%){" "}
                <span style={{ color: arrowColor }}>{arrow}</span>
              </p>
            </div>
          </div>
        );
      })}
    </div>
  );
};

export default LiveMarketPrices;
