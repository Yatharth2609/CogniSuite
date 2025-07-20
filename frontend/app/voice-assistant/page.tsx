'use client';
import { useState, useRef, useEffect } from 'react';
import { Mic } from 'lucide-react';

export default function VoiceAssistantPage() {
  const [isRecording, setIsRecording] = useState(false);
  const [threadId, setThreadId] = useState<string>('new');
  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const audioChunksRef = useRef<Blob[]>([]);

  const handleInteraction = async () => {
    if (isRecording) {
      // Stop recording
      mediaRecorderRef.current?.stop();
      setIsRecording(false);
    } else {
      // Start recording
      try {
        const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
        mediaRecorderRef.current = new MediaRecorder(stream);
        audioChunksRef.current = [];

        mediaRecorderRef.current.ondataavailable = (event) => {
          audioChunksRef.current.push(event.data);
        };

        mediaRecorderRef.current.onstop = async () => {
          const audioBlob = new Blob(audioChunksRef.current, { type: 'audio/webm' });
          
          const formData = new FormData();
          formData.append('file', audioBlob, 'recording.webm');
          formData.append('thread_id', threadId);

          const response = await fetch('http://localhost:8000/api/voice-assistant/chat', {
            method: 'POST',
            body: formData,
          });

          if (response.ok) {
            const audioBlobResponse = await response.blob();
            const audioUrl = URL.createObjectURL(audioBlobResponse);
            const audio = new Audio(audioUrl);
            audio.play();
          } else {
            console.error("Failed to get audio response from server.");
          }
        };

        mediaRecorderRef.current.start();
        setIsRecording(true);
      } catch (err) {
        console.error("Microphone access denied:", err);
        alert("Microphone access is required for the voice assistant.");
      }
    }
  };

  return (
    <div className="flex flex-col items-center justify-center h-full text-center">
      <h1 className="text-3xl font-bold mb-4">Voice Assistant</h1>
      <p className="text-gray-400 mb-8">Click and hold the button to speak. Release to get a response.</p>
      
      <button
        onMouseDown={handleInteraction}
        onMouseUp={handleInteraction}
        onTouchStart={handleInteraction}
        onTouchEnd={handleInteraction}
        className={`relative flex items-center justify-center w-32 h-32 rounded-full transition-all duration-300 ${
          isRecording ? 'bg-red-500 scale-110' : 'bg-blue-600'
        }`}
      >
        <Mic size={64} className="text-white" />
        {isRecording && (
          <div className="absolute inset-0 rounded-full border-4 border-red-300 animate-ping"></div>
        )}
      </button>
      <p className="mt-6 text-lg font-medium">
        {isRecording ? "Listening..." : "Click and Hold to Speak"}
      </p>
    </div>
  );
}