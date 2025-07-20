"use client";
import { createContext, useState, useContext, ReactNode } from "react";

interface ChatMessage {
  role: "user" | "assistant";
  content: string;
}

interface ChatContextType {
  isChatOpen: boolean;
  toggleChat: () => void;
  chatHistory: ChatMessage[];
  sendMessage: (message: string) => void;
  isLoading: boolean;
}

const ChatContext = createContext<ChatContextType | undefined>(undefined);

export const useChat = () => {
  const context = useContext(ChatContext);
  if (!context) {
    throw new Error("useChat must be used within a ChatProvider");
  }
  return context;
};

export const ChatProvider = ({ children }: { children: ReactNode }) => {
  const [isChatOpen, setIsChatOpen] = useState(false);
  const [chatHistory, setChatHistory] = useState<ChatMessage[]>([]);
  const [threadId, setThreadId] = useState("new");
  const [isLoading, setIsLoading] = useState(false);

  const toggleChat = () => setIsChatOpen(!isChatOpen);

  const sendMessage = async (message: string) => {
    if (!message.trim()) return;

    setIsLoading(true);
    const userMessage: ChatMessage = { role: "user", content: message };
    
    setChatHistory((prev) => [
        ...prev, 
        userMessage, 
        { role: "assistant", content: "" }
    ]);

    // This now uses EventSource as requested
    const url = `http://localhost:8000/api/assistant/chat?thread_id=${threadId}&message=${encodeURIComponent(message)}`;
    const eventSource = new EventSource(url);

    eventSource.onmessage = (event) => {
      if (event.data === "[DONE]") {
        setIsLoading(false);
        eventSource.close();
        return;
      }
      if (event.data === "[ERROR]") {
        console.error("Stream error from server");
        setChatHistory((prev) => {
            const newHistory = [...prev];
            newHistory[newHistory.length - 1].content = "An error occurred.";
            return newHistory;
        });
        setIsLoading(false);
        eventSource.close();
        return;
      }
      
      try {
        const data = JSON.parse(event.data);

        if (data.thread_id && threadId === 'new') {
            setThreadId(data.thread_id);
        }

        if (data.delta) {
          setChatHistory((prev) => {
            const lastMsg = prev[prev.length - 1];
            const updatedLastMsg = {
                ...lastMsg,
                content: lastMsg.content + data.delta,
            };
            return [...prev.slice(0, -1), updatedLastMsg];
          });
        }
      } catch (e) {
        console.error("Failed to parse JSON from stream:", event.data, e);
      }
    };

    eventSource.onerror = (err) => {
      console.error("EventSource failed:", err);
      setChatHistory((prev) => {
        const newHistory = [...prev];
        newHistory[newHistory.length - 1].content = "Failed to connect to the assistant.";
        return newHistory;
      });
      setIsLoading(false);
      eventSource.close();
    };
  };

  const value = { isChatOpen, toggleChat, chatHistory, sendMessage, isLoading };

  return <ChatContext.Provider value={value}>{children}</ChatContext.Provider>;
};