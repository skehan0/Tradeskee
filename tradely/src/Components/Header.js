import React, { useState } from "react";
import "../Styles/header.css";

const Header = () => {
  const [isDropdownOpen, setIsDropdownOpen] = useState(false);

  const toggleDropdown = () => {
    setIsDropdownOpen(!isDropdownOpen);
  };

  return (
    <header className="header">
      <h1>Tradeskee</h1>
      <nav>
        <ul>
          <li>
            <a href="#features" onClick={toggleDropdown}>
              Features
            </a>
            {isDropdownOpen && (
              <ul className="dropdown">
                <li>
                  <a href="#feature1">Feature 1</a>
                </li>
                <li>
                  <a href="#feature2">Feature 2</a>
                </li>
                <li>
                  <a href="#feature3">Feature 3</a>
                </li>
              </ul>
            )}
          </li>
          <li>
            <a href="#testimonials">Testimonials</a>
          </li>
          <li>
            <a href="#cta">Get Started</a>
          </li>
          <li>
            <a href="#faq">FAQ</a>
          </li>
          <li>
            <a href="#contact">Contact</a>
          </li>
        </ul>
      </nav>
    </header>
  );
};

export default Header;
