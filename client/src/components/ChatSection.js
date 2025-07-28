import React from 'react';
import ReactMarkdown from 'react-markdown';
import './ChatSection.css';

function ChatSection({ messages }) {
  return (
    <div className="chat-section">
      <h2>Conversation</h2>
      <div className="messages-container">
        {messages.map((msg, index) => (
          <div key={index} className={`message-bubble ${msg.sender}`}>
            {msg.sender === 'user' && (
              <div className="prompt-header"></div>
            )}
            {msg.sender === 'bot' && (
              <div className="response-header"></div>
            )}
            <div className="message-content">
              <ReactMarkdown>{msg.text}</ReactMarkdown>
            </div>
            {msg.sender === 'bot' && msg.sources && (
              <div className="sources">
                <strong>Sources:</strong> {msg.sources}
              </div>
            )}
          </div>
        ))}
      </div>
    </div>
  );
}

export default ChatSection;
