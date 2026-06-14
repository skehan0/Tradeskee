import React, { useState, useEffect } from "react";
import "../Styles/news.css";

const News = ({ fetchNews, isLiveNews = false }) => {
  const [data, setData] = useState([]);
  const [currentIndex, setCurrentIndex] = useState(0);
  const [error, setError] = useState(null);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    const cachedNews = localStorage.getItem(
      isLiveNews ? "liveNewsData" : "newsData",
    );
    const cachedTimestamp = localStorage.getItem(
      isLiveNews ? "liveNewsTimestamp" : "newsTimestamp",
    );
    const now = new Date().getTime();

    if (cachedNews && cachedTimestamp && now - cachedTimestamp < 3600000) {
      setData(JSON.parse(cachedNews).slice(0, 9)); // Limit to 9 articles
      setIsLoading(false);
    } else {
      fetchNews()
        .then((newsData) => {
          if (newsData && newsData.length > 0) {
            setData(newsData.slice(0, 9)); // Limit to 9 articles
            localStorage.setItem(
              isLiveNews ? "liveNewsData" : "newsData",
              JSON.stringify(newsData.slice(0, 9)),
            );
            localStorage.setItem(
              isLiveNews ? "liveNewsTimestamp" : "newsTimestamp",
              now,
            );
          } else {
            setError("No news available at the moment.");
          }
        })
        .catch(() => {
          setError("Failed to fetch news. Please try again later.");
        })
        .finally(() => {
          setIsLoading(false);
        });
    }
  }, [fetchNews, isLiveNews]);

  const handlePrev = () => {
    setCurrentIndex((prevIndex) => {
      const newIndex = prevIndex - 3;
      return newIndex < 0 ? 6 : newIndex; // Wrap around to the last page
    });
  };

  const handleNext = () => {
    setCurrentIndex((prevIndex) => {
      const newIndex = prevIndex + 3;
      return newIndex >= 9 ? 0 : newIndex; // Wrap around to the first page
    });
  };

  const renderDots = () => {
    const dots = [];
    for (let i = 0; i < 3; i++) {
      // Fixed to 3 pages
      dots.push(
        <span
          key={i}
          className={`dot ${currentIndex / 3 === i ? "active" : ""}`}
          onClick={() => setCurrentIndex(i * 3)} // Jump to the corresponding page
        ></span>,
      );
    }
    return dots;
  };

  if (isLoading) {
    return <div className="loading-message">Loading news...</div>;
  }

  if (error || data.length === 0) {
    return (
      <div className="no-news-message">No news available at the moment.</div>
    );
  }

  return (
    <div className="news">
      <h2>{isLiveNews ? "Live News" : "Latest News"}</h2>
      <div className="news-container">
        <button className="arrow left" onClick={handlePrev}>
          &#9664;
        </button>
        {data.slice(currentIndex, currentIndex + 3).map((article, index) => (
          <div key={index} className="news-article">
            {article.thumbnail && (
              <img src={article.thumbnail} alt="thumbnail" />
            )}
            <div className="news-content">
              <h3>{article.title}</h3>
              <p className="summary">{article.summary}</p>
              <a href={article.url} target="_blank" rel="noopener noreferrer">
                Read more
              </a>
            </div>
          </div>
        ))}
        <button className="arrow right" onClick={handleNext}>
          &#9654;
        </button>
      </div>
      <div className="dots-container">{renderDots()}</div>
    </div>
  );
};

export default News;
