import React, { useState, useEffect } from "react";
import "./Styles/App.css";
import "./Styles/topGainersLosers.css";
import "./Styles/questionSection.css";
import Header from "./Components/Header";
import News from "./Components/News";
import LiveMarketData from "./Components/LiveMarketPrices";
import Footer from "./Components/footer";
import TopGainersLosers from "./Components/TopGainersLosers";
import {
  fetchLiveMarketPrices,
  fetchLiveNewsHeadlines,
  fetchTopGainersLosers,
  analyzeStock,
  askQuestion,
} from "./Services/api";
import AnalysisSection from "./Components/AnalysisSection";
import ChartSection from "./Components/ChartSection";
import QuestionSection from "./Components/QuestionSection";
import logo from "./Assets/Tradeskee_logo_transparent.png";

function App() {
  const [ticker, setTicker] = useState("");
  const [range, setRange] = useState("1y");
  const [liveMarketData, setLiveMarketPrices] = useState(null);
  const [liveNews, setLiveNews] = useState(null);
  const [error, setError] = useState(null);
  const [analysis, setAnalysis] = useState(null);
  const [isLoading, setIsLoading] = useState(false);
  const [gainersLosers, setGainersLosers] = useState({
    gainers: [],
    losers: [],
  });
  const [userQuestion, setUserQuestion] = useState("");
  const [answer, setAnswer] = useState("");

  useEffect(() => {
    const fetchLiveData = async () => {
      try {
        // Fetch live market prices
        const marketData = await fetchLiveMarketPrices();
        console.log("Live Market Data:", marketData);
        setLiveMarketPrices(marketData);

        // Fetch live news
        const newsData = await fetchLiveNewsHeadlines();
        console.log("Live News Data:", newsData);
        setLiveNews(newsData);

        // Fetch top gainers and losers
        const gainersLosersData = await fetchTopGainersLosers(5);
        console.log("Top Gainers and Losers:", gainersLosersData);
        setGainersLosers(gainersLosersData);
      } catch (error) {
        console.error("Error fetching live data:", error);
        setError(error.message);
      }
    };

    fetchLiveData();
  }, []);

  const handleInputChange = (event) => {
    setTicker(event.target.value);
  };

  const handleRangeChange = (event) => {
    setRange(event.target.value);
  };

  const handleSubmit = async (event) => {
    event.preventDefault();
    setIsLoading(true);
    setError(null);

    try {
      const analysisData = await analyzeStock(ticker);
      console.log("Debug: Stock Analysis Data:", analysisData);
      setAnalysis(analysisData); // Update the state
      console.log("Debug: Updated analysis state:", analysisData); // Confirm state update
      setIsLoading(false);
    } catch (err) {
      console.error("Debug: Error fetching stock analysis:", err);
      setError(err.response?.data?.message);
      setIsLoading(false);
    }
  };

  const handleAskQuestion = async (question) => {
    if (!analysis) {
      setAnswer("Please analyze a stock first before asking a question.");
      return;
    }

    try {
      setIsLoading(true);
      setAnswer(""); // Clear the previous answer

      // Use a simple string as the context
      const context = "stock analysis";

      const response = await askQuestion(question, context);

      if (response && response.answer) {
        setAnswer(response.answer);
      } else {
        setAnswer("No answer received from the backend.");
      }
    } catch (err) {
      setAnswer(
        "An error occurred while fetching the answer. Please try again.",
      );
    } finally {
      setIsLoading(false);
    }
  };

  // const handleSubmit = async (event) => {
  //   event.preventDefault();
  //   setIsLoading(true);
  //   setError(null);

  //   try {
  //     // Make an API call to fetch the analysis
  //     const response = await fetch(`http://localhost:8000/analyze_all/${ticker}`, {
  //       method: 'GET',
  //     });

  //     if (!response.ok) {
  //       throw new Error('Failed to fetch analysis');
  //     }

  //     const data = await response.json();
  //     setAnalysis(data.analysis); // Use the real analysis data from the backend
  //     setIsLoading(false);
  //   } catch (err) {
  //     setError('Failed to fetch analysis. Please try again.');
  //     setIsLoading(false);
  //   }
  // };

  // /* Mock Data */
  // const handleSubmit = async (event) => {
  //   event.preventDefault();
  //   setIsLoading(true);
  //   setError(null);

  //   try {
  //     // Mock LLM response
  //     const mockLlmResponse = `
  //       Mock LLM response for ${ticker}:
  //       - Tesla (TSLA) is a leader in the EV market.
  //       - Strong revenue growth and high profit margins.
  //       - Recommendation: Buy with caution due to market volatility.
  //     `;
  //     console.log("Debug: Mock LLM response:", mockLlmResponse);

  //     // Send the mock LLM response to DeepSeek
  //     const deepThinkingResponse = await mockSendToDeepSeek(mockLlmResponse);

  //     // Set the analysis and DeepThinking response in the state
  //     setAnalysis(deepThinkingResponse);
  //     setIsLoading(false);
  //   } catch (err) {
  //     console.error("Debug: Error in handleSubmit:", err);
  //     setError('Failed to fetch analysis. Please try again.');
  //     setIsLoading(false);
  //   }
  // };

  return (
    <div className="App">
      <Header />
      <header className="App-header">
        <div className="hero-section">
          <img src={logo} alt="Logo" className="logo" />
          <h2>Welcome to Tradeskee</h2>
          <p>Your go-to platform for stock market analysis and insights.</p>
        </div>
        <form onSubmit={handleSubmit}>
          <input
            list="tickers"
            value={ticker}
            onChange={handleInputChange}
            placeholder="Enter stock ticker"
            className="stock-input"
          />
          <datalist id="tickers">
            <option value="AAPL">Apple</option>
            <option value="GOOGL">Alphabet</option>
            <option value="MSFT">Microsoft</option>
            <option value="AMZN">Amazon</option>
            <option value="TSLA">Tesla</option>
          </datalist>
          <select value={range} onChange={handleRangeChange}>
            <option value="1d">1 Day</option>
            <option value="5d">5 Days</option>
            <option value="1mo">1 Month</option>
            <option value="3mo">3 Months</option>
            <option value="6mo">6 Months</option>
            <option value="1y">1 Year</option>
            <option value="2y">2 Years</option>
            <option value="5y">5 Years</option>
            <option value="10y">10 Years</option>
            <option value="ytd">Year to Date</option>
            <option value="max">Max</option>
          </select>
          <button type="submit">Analyze Stock</button>
        </form>
        {error && <div>Error: {error}</div>}
        <AnalysisSection
          analysis={analysis}
          isLoading={isLoading}
          error={error}
        />
        <ChartSection
          ticker={ticker}
          isLoading={isLoading}
          analysis={analysis}
        />
        <QuestionSection
          analysis={analysis}
          userQuestion={userQuestion}
          setUserQuestion={setUserQuestion}
          answer={answer}
          handleAskQuestion={handleAskQuestion}
        />
        {liveMarketData && <LiveMarketData data={liveMarketData} />}
        <TopGainersLosers
          gainers={gainersLosers.gainers}
          losers={gainersLosers.losers}
        />
        {liveNews && <News fetchNews={fetchLiveNewsHeadlines} />}
      </header>
      <Footer />
    </div>
  );
}

export default App;

// const mockSendToDeepSeek = async (llmResponse) => {
//   console.log("Debug: Mock LLM response being sent to DeepSeek:", llmResponse);

//   // Simulate a delay to mimic an API call
//   return new Promise((resolve) => {
//     setTimeout(() => {
//       const deepThinkingResponse = `
//         Deeper analysis based on the LLM response:
//         - Tesla (TSLA) is a leader in the EV market.
//         - Strong revenue growth and high profit margins.
//         - Recommendation: Buy with caution due to market volatility.
//       `;
//       console.log("Debug: Mock DeepThinking response:", deepThinkingResponse);
//       resolve(deepThinkingResponse);
//     }, 2000); // Simulate a 2-second delay
//   });
// };
