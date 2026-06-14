import React from "react";
import "../Styles/topGainersLosers.css";

const TopGainersLosers = ({ gainers, losers }) => {
  return (
    <div className="top-gainers-losers">
      <h2>Top Gainers and Losers</h2>
      <div className="tables-container">
        {/* Gainers Table */}
        <div className="table-section">
          <h3>Top Gainers</h3>
          <table className="gainers-table">
            <thead>
              <tr>
                <th>Ticker</th>
                <th>Price</th>
                <th>Change Amount</th>
                <th>Change %</th>
                <th>Volume</th>
              </tr>
            </thead>
            <tbody>
              {gainers.map((gainer, index) => (
                <tr key={index}>
                  <td>{gainer.ticker}</td>
                  <td>{gainer.price}</td>
                  <td>{gainer.change_amount}</td>
                  <td>{gainer.change_percentage}</td>
                  <td>{gainer.volume}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        {/* Losers Table */}
        <div className="table-section">
          <h3>Top Losers</h3>
          <table className="losers-table">
            <thead>
              <tr>
                <th>Ticker</th>
                <th>Price</th>
                <th>Change Amount</th>
                <th>Change %</th>
                <th>Volume</th>
              </tr>
            </thead>
            <tbody>
              {losers.map((loser, index) => (
                <tr key={index}>
                  <td>{loser.ticker}</td>
                  <td>{loser.price}</td>
                  <td>{loser.change_amount}</td>
                  <td>{loser.change_percentage}</td>
                  <td>{loser.volume}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};

export default TopGainersLosers;
