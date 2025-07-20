'use client';
import { useState } from 'react';
import { Upload, MessageSquare, User, Bot } from 'lucide-react';

interface ChatMessage {
  sender: 'user' | 'bot';
  text: string;
}

export default function DocInspectorPage() {
  const [file, setFile] = useState<File | null>(null);
  const [threadId, setThreadId] = useState<string | null>(null);
  const [status, setStatus] = useState<'idle' | 'uploading' | 'ready' | 'querying'>('idle');
  
  const [question, setQuestion] = useState('');
  const [chatHistory, setChatHistory] = useState<ChatMessage[]>([]);

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files) {
      setFile(e.target.files[0]);
    }
  };

  const handleUpload = async () => {
    if (!file) return;
    setStatus('uploading');
    setChatHistory([]);
    
    const formData = new FormData();
    formData.append('file', file);

    try {
      const response = await fetch('http://localhost:8000/api/doc-intel/upload', {
        method: 'POST',
        body: formData,
      });
      const data = await response.json();
      if (data.thread_id) {
        setThreadId(data.thread_id);
        setStatus('ready');
        setChatHistory([{ sender: 'bot', text: 'Document processed! What would you like to know?' }]);
      }
    } catch (error) {
      console.error("Upload failed:", error);
      setStatus('idle');
    }
  };

  const handleAskQuestion = async (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    if (!question || !threadId) return;

    setStatus('querying');
    const userMessage: ChatMessage = { sender: 'user', text: question };
    setChatHistory(prev => [...prev, userMessage]);
    setQuestion('');

    const url = `http://localhost:8000/api/doc-intel/ask?thread_id=${threadId}&question=${encodeURIComponent(question)}`;
    const eventSource = new EventSource(url);

    let botMessage = '';
    eventSource.onmessage = (event) => {
      if (event.data === "[DONE]") {
        setStatus('ready');
        eventSource.close();
        return;
      }
       if (event.data === "[ERROR]") {
        console.error("Stream error from server");
        setStatus('ready');
        eventSource.close();
        return;
      }
      try {
        const data = JSON.parse(event.data);
        if (data.answer) {
          botMessage = data.answer;
          setChatHistory(prev => [...prev.slice(0, -1), userMessage, { sender: 'bot', text: botMessage }]);
        }
      } catch (e) {
        console.error("Failed to parse JSON:", e);
      }
    };
    eventSource.onerror = () => {
      setStatus('ready');
      eventSource.close();
    };
  };

  return (
    <div className="flex flex-col h-full max-w-4xl mx-auto">
      {/* File Upload Section */}
      <div className="flex-shrink-0 p-4 border-b border-gray-700">
        <h2 className="text-lg font-semibold mb-2">1. Upload Document</h2>
        <div className="flex items-center gap-4">
          <input type="file" onChange={handleFileChange} accept=".pdf" className="file:mr-4 file:py-2 file:px-4 file:rounded-lg file:border-0 file:text-sm file:font-semibold file:bg-gray-700 file:text-gray-200 hover:file:bg-gray-600"/>
          <button onClick={handleUpload} disabled={!file || status === 'uploading'} className="bg-blue-600 px-4 py-2 rounded-lg disabled:bg-gray-600">
            {status === 'uploading' ? 'Processing...' : 'Upload & Process'}
          </button>
        </div>
        {status === 'ready' && <p className="text-green-400 mt-2">Ready to answer questions.</p>}
      </div>

      {/* Chat Section */}
      <div className="flex-grow flex flex-col p-4 overflow-hidden">
        <h2 className="text-lg font-semibold mb-2">2. Ask Questions</h2>
        <div className="flex-grow bg-gray-800/50 rounded-lg p-4 overflow-y-auto mb-4">
          {chatHistory.map((msg, index) => (
            <div key={index} className={`flex items-start gap-3 my-4 ${msg.sender === 'user' ? 'justify-end' : ''}`}>
              {msg.sender === 'bot' && <div className="bg-gray-700 p-2 rounded-full"><Bot size={20}/></div>}
              <div className={`px-4 py-2 rounded-lg max-w-lg ${msg.sender === 'user' ? 'bg-blue-600' : 'bg-gray-700'}`}>
                {msg.text}
              </div>
              {msg.sender === 'user' && <div className="bg-blue-600 p-2 rounded-full"><User size={20}/></div>}
            </div>
          ))}
        </div>
        <form onSubmit={handleAskQuestion} className="flex gap-4">
          <input
            type="text"
            value={question}
            onChange={(e) => setQuestion(e.target.value)}
            disabled={status !== 'ready'}
            className="flex-grow bg-gray-800 border border-gray-700 rounded-lg px-4 py-2 disabled:cursor-not-allowed"
            placeholder={status === 'ready' ? 'Ask a question about the document...' : 'Please upload a document first.'}
          />
          <button type="submit" disabled={status !== 'ready'} className="bg-blue-600 px-4 py-2 rounded-lg disabled:bg-gray-600">
            {status === 'querying' ? 'Thinking...' : 'Ask'}
          </button>
        </form>
      </div>
    </div>
  );
}