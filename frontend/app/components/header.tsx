'use client'; // <-- Add this directive
import { BotMessageSquare } from 'lucide-react';
import { useChat } from '../context/ChatContext'; // <-- Import the hook

export default function Header() {
  const { toggleChat } = useChat(); // <-- Get the toggle function

  return (
    <header className="bg-gray-900/70 backdrop-blur-sm border-b border-gray-700 p-4 flex justify-between items-center">
      {/* This title part would ideally be dynamic */}
      <h1 className="text-xl font-semibold">CogniSuite</h1>
      <button 
        onClick={toggleChat} // <-- Add onClick handler
        className="flex items-center gap-2 bg-gray-700 hover:bg-gray-600 px-4 py-2 rounded-lg text-sm"
      >
        <BotMessageSquare size={16} />
        AI Assistant
      </button>
    </header>
  );
}