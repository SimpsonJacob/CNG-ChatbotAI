import React, { useState } from 'react';
import './App.css';
import userAvatar from './user.jpg';
import botAvatar from './CharterandGo.jpg';
import logo from './chartandgo-logo-2.png';

function App() {
  const [messages, setMessages] = useState([]);
  const [inputText, setInputText] = useState('');

  const handleInput = (e) => {
    if (e.key === 'Enter') {
      const userMessage = inputText.trim();
      if (userMessage !== '') {
        // Add the user's message to the chat
        setMessages((prevMessages) => [
          ...prevMessages,
          { text: userMessage, isUser: true },
        ]);
        setInputText('');

        // Simulate a response
        setTimeout(() => {
          const botResponse = "Bot response goes here"; // Will replace with a API call of some sort
          setMessages((prevMessages) => [
            ...prevMessages,
            { text: botResponse, isUser: false },
          ]);
        }, 800); // Simulate a delay for the bot response
      }
    }
  };

  return (
    <div className="App">
      <header className="App-header">
        <img src={logo} alt="Logo" className="logo" />
      </header>
      <div className="chat-container">
        <div className="chat-messages">
          {messages.map((message, index) => (
            <div
              key={index}
              className={`chat-message ${message.isUser ? 'user' : 'bot'}`}
            >
              {message.isUser ? (
                <div className="avatar">
                  <img src={userAvatar} alt="User Avatar" />
                </div>
              ) : (
                <div className="avatar">
                  <img src={botAvatar} alt="Bot Avatar" />
                </div>
              )}
              {message.text}
            </div>
          ))}
        </div>
        <input
          className="chat-input"
          type="text"
          placeholder="Type a message..."
          value={inputText}
          onChange={(e) => setInputText(e.target.value)}
          onKeyPress={handleInput}
        />
      </div>
    </div>
  );
}

export default App;