import React, { useState } from 'react';
import axios from 'axios';
import './App.css';
import UploadSection from './components/UploadSection';
import QuerySection from './components/QuerySection';
import ChatSection from './components/ChatSection';
import ConfirmationDialog from './components/ConfirmationDialog';

function App() {
  const [file, setFile] = useState([]);
  const [uploadMessage, setUploadMessage] = useState('');
  const [query, setQuery] = useState('');
  const [answer, setAnswer] = useState('');
  const [showResetConfirm, setShowResetConfirm] = useState(false);
  const [loading, setLoading] = useState({ upload: false, ask: false });
  const [sessionId, setSessionId] = useState(null);
  const [messages, setMessages] = useState([]);
  const [uploadedFileName, setUploadedFileName] = useState('');

  const handleFileChange = (e) => {
  const selectedFiles = Array.from(e.target.files);
  console.log('Selected files:', selectedFiles);
  setFile(selectedFiles);
  setUploadMessage('');
  setAnswer('');
  setUploadedFileName(selectedFiles.map(f => f.name).join(', '));
};

  const handleUpload = async () => {
  if (!file || file.length === 0) {
    setUploadMessage('Please select at least one PDF file');
    return;
  }

  const formData = new FormData();
  file.forEach(f => formData.append('files', f));

  try {
    setLoading({ ...loading, upload: true });
    const res = await axios.post('https://rag-zanardy-bycahud2h6aud9gp.southeastasia-01.azurewebsites.net/upload', formData, {
      headers: { 'Content-Type': 'multipart/form-data' }
    });
    setUploadMessage(res.data.message);
    setSessionId(res.data.session_id);
    setMessages([{ text: `Uploaded: ${uploadedFileName}`, sender: 'bot' }]);
  } catch (error) {
    console.error('Upload error:', error);
    setUploadMessage(error.response?.data?.detail || 'Upload failed. Please try again.');
  } finally {
    setLoading({ ...loading, upload: false });
  }
};

  const handleAsk = async () => {
    if (!query.trim()) {
      setAnswer('Please enter a question');
      return;
    }
  
    try {
      setLoading({ ...loading, ask: true });
  
      const payload = { question: query };
      if (sessionId) {
        payload.session_id = sessionId;
      }
  
      const res = await axios.post('https://rag-zanardy-bycahud2h6aud9gp.southeastasia-01.azurewebsites.net/query', payload, {
        headers: { 'Content-Type': 'application/json' }
      });
  
      setAnswer(res.data.answer);
      setMessages(prev => [
        ...prev,
        { text: query, sender: 'user' },
        { text: res.data.answer, sender: 'bot' }
      ]);
      setQuery('');
    } catch (error) {
      console.error('Query error:', error);
      setAnswer(error.response?.data?.detail || 'Failed to get answer. Please try again.');
    } finally {
      setLoading({ ...loading, ask: false });
    }
  };

  const handleReset = () => setShowResetConfirm(true);

  const confirmReset = async () => {
    try {
      if (sessionId) {
        await axios.post('https://rag-zanardy-bycahud2h6aud9gp.southeastasia-01.azurewebsites.net/reset', { session_id: sessionId }, {
          headers: { 'Content-Type': 'application/json' }
        });
      }
      setSessionId(null);
      setMessages([{ text: "Session reset. All uploaded documents and history have been cleared.", sender: 'bot' }]);
      setFile(null);
      setUploadedFileName('');
      setQuery('');
      setAnswer('');
      setUploadMessage('');
    } catch (error) {
      console.error("Reset failed:", error);
      setMessages(prev => [...prev, { text: "Failed to reset session. Please try again.", sender: 'bot' }]);
    } finally {
      setShowResetConfirm(false);
    }
  };

  const cancelReset = () => setShowResetConfirm(false);

  return (
    <div className="app-container">
      <header className="app-header">
        <h1>Document AI Assistant</h1>
      </header>

      <UploadSection
        file={file}
        onFileChange={handleFileChange}
        onUpload={handleUpload}
        loading={loading.upload}
        uploadMessage={uploadMessage}
      />
      
      <ChatSection messages={messages} />
      
      <QuerySection
        query={query}
        onQueryChange={setQuery}
        onAsk={handleAsk}
        onReset={handleReset}
        loading={loading.ask}
      />

      {showResetConfirm && (
        <ConfirmationDialog
          onConfirm={confirmReset}
          onCancel={cancelReset}
        />
      )}

    </div>
  );
}

export default App;
