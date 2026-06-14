import React from "react";
import "../Styles/questionSection.css";

const QuestionSection = ({
  analysis,
  userQuestion,
  setUserQuestion,
  answer,
  handleAskQuestion,
}) => {
  const handleSubmit = async () => {
    if (!userQuestion.trim()) {
      alert("Please enter a valid question.");
      return;
    }

    await handleAskQuestion(userQuestion); // Call the function passed from App.js
  };

  return (
    <div className="question-section">
      <h3>Ask a Question About the Stock Analysis</h3>
      <input
        type="text"
        value={userQuestion}
        onChange={(e) => setUserQuestion(e.target.value)}
        placeholder="Type your question here"
        className="question-input"
      />
      <button onClick={handleSubmit} className="question-button">
        Submit
      </button>
      {answer && <div className="answer">{answer}</div>}
    </div>
  );
};

export default QuestionSection;
