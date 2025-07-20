'use client';
import { useChat } from '../context/ChatContext';
import { Bot, User, X, Send } from 'lucide-react';
import { useEffect, useRef } from 'react';

export default function ChatWidget() {
  const { isChatOpen, toggleChat, chatHistory, sendMessage, isLoading } = useChat();
  const messagesEndRef = useRef<HTMLDivElement | null>(null);
  const inputRef = useRef<HTMLInputElement | null>(null);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [chatHistory]);
  
  useEffect(() => {
    if (isChatOpen) {
      inputRef.current?.focus();
    }
  }, [isChatOpen]);


  if (!isChatOpen) return null;

  const handleFormSubmit = (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    const input = e.currentTarget.elements.namedItem('message') as HTMLInputElement;
    sendMessage(input.value);
    input.value = '';
  };

  return (
    <div className="fixed bottom-4 right-4 w-96 h-[600px] bg-gray-900 border border-gray-700 rounded-lg shadow-2xl flex flex-col z-50">
      {/* Header */}
      <div className="flex items-center justify-between p-4 border-b border-gray-700">
        <h3 className="font-semibold text-lg">AI Assistant</h3>
        <button onClick={toggleChat} className="text-gray-400 hover:text-white">
          <X size={20} />
        </button>
      </div>

      {/* Messages */}
      <div className="flex-grow p-4 overflow-y-auto">
        {chatHistory.map((msg, index) => (
          <div key={index} className={`flex items-start gap-3 my-4`}>
            {msg.role === 'assistant' && <div className="bg-gray-700 p-2 rounded-full"><Bot size={20}/></div>}
            <div className={`px-4 py-2 rounded-lg max-w-xs ${msg.role === 'user' ? 'bg-blue-600 ml-auto' : 'bg-gray-700'}`}>
              {msg.content || <span className="animate-pulse">...</span>}
            </div>
            {msg.role === 'user' && <div className="bg-blue-600 p-2 rounded-full"><User size={20}/></div>}
          </div>
        ))}
         <div ref={messagesEndRef} />
      </div>

      {/* Input */}
      <div className="p-4 border-t border-gray-700">
        <form onSubmit={handleFormSubmit} className="flex gap-2">
          <input
            ref={inputRef}
            name="message"
            type="text"
            disabled={isLoading}
            className="flex-grow bg-gray-800 border border-gray-600 rounded-lg px-4 py-2 disabled:cursor-not-allowed"
            placeholder="Ask anything..."
          />
          <button type="submit" disabled={isLoading} className="bg-blue-600 px-4 py-2 rounded-lg disabled:bg-gray-600">
            <Send size={20} />
          </button>
        </form>
      </div>
    </div>
  );
}