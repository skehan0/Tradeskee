import { render } from "@testing-library/react";
import App from "./App";

// Mock the API service to avoid axios import issues
jest.mock("./Services/api", () => ({
  fetchLiveMarketPrices: jest.fn(() => Promise.resolve({})),
  fetchLiveNewsHeadlines: jest.fn(() => Promise.resolve([])),
  fetchTopGainersLosers: jest.fn(() => Promise.resolve({})),
  analyzeStock: jest.fn(() => Promise.resolve({})),
  askQuestion: jest.fn(() => Promise.resolve({})),
}));

test("renders app without crashing", () => {
  render(<App />);
  // Just test that the app renders without errors
  expect(document.body).toBeInTheDocument();
});
