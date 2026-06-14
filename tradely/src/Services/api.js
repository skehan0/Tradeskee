import axios from "axios";

// Create an instance of axios with the base URL
const api = axios.create({
  baseURL: process.env.REACT_APP_API_BASE_URL || "http://localhost:8000",
});

// Export the Axios instance
export default api;

// Helper function to handle API errors
const handleApiError = (error) => {
  if (error.response) {
    // Server responded with a status code outside the 2xx range
    throw new Error(error.response.data.message);
  } else if (error.request) {
    // Request was made but no response was received
    throw new Error("No response from server. Please try again.");
  } else {
    // Something else happened
    throw new Error(error.message || "An unexpected error occurred");
  }
};

// Fetch and Analyze Stock Data
export const analyzeStock = async (ticker) => {
  try {
    console.log(`Debug: Sending request to /analyze_all/${ticker}`);
    const response = await api.get(`/analyze_all/${ticker}`); // Use path parameter
    console.log("Debug: Response from /analyze_all:", response.data);
    return response.data;
  } catch (error) {
    console.error("Debug: Error in analyzeStock:", error);
    throw error;
  }
};

// Fetch Live Market Prices
export const fetchLiveMarketPrices = async () => {
  try {
    const response = await api.get(`/live-market-prices`);
    return response.data;
  } catch (error) {
    handleApiError(error);
  }
};

// Fetch Live News Headlines
export const fetchLiveNewsHeadlines = async (limit = 3) => {
  try {
    const response = await api.get(`/live-news-headlines`, {
      params: { limit },
    });
    console.log("Debug response from /live-news-headlines", response.data);

    // Access the nested "news" array inside "feed"
    if (response.data && response.data.feed && response.data.feed.news) {
      return response.data.feed.news; // Return the "news" array
    } else {
      console.warn("Debug: No news found in response:", response.data);
      return []; // Return an empty array if "news" is missing
    }
  } catch (error) {
    handleApiError(error);
    return []; // Ensure a fallback in case of an error
  }
};

// Fetch Top Gainers and Losers
export const fetchTopGainersLosers = async (limit = 5) => {
  try {
    const response = await api.get(`/top-gainers-losers`, {
      params: { limit },
    });
    return response.data;
  } catch (error) {
    console.error("Error fetching top gainers and losers:", error.message);
    return { gainers: [], losers: [] }; // Return empty arrays
  }
};

// Ask a Question About Stock Analysis
export const askQuestion = async (question, context) => {
  try {
    console.log("Debug: Payload being sent to /ask-question:", {
      question,
      context,
    });

    const response = await api.post("/ask-question", {
      question,
      context, // Send context as a string
    });

    console.log("Debug: Response from /ask-question:", response.data);
    return response.data;
  } catch (error) {
    console.error("Debug: Error in askQuestion API:", error);
    throw error;
  }
};
