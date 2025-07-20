'use client';
import { useState } from 'react';
import { Upload, FileCode, Bot } from 'lucide-react';

// A simple component to render markdown
const MarkdownRenderer = ({ content }: { content: string }) => {
    // Basic markdown conversion for demonstration purposes
    const htmlContent = content
        .replace(/### (.*)/g, '<h3 class="text-lg font-semibold mt-4 mb-2">$1</h3>')
        .replace(/## (.*)/g, '<h2 class="text-xl font-bold mt-6 mb-3">$1</h2>')
        .replace(/`([^`]+)`/g, '<code class="bg-gray-700 text-green-300 px-1 rounded">$1</code>')
        .replace(/\n/g, '<br />');

    return <div dangerouslySetInnerHTML={{ __html: htmlContent }} />;
};


export default function CodeAnalyzerPage() {
  const [file, setFile] = useState<File | null>(null);
  const [threadId, setThreadId] = useState<string | null>(null);
  const [status, setStatus] = useState<'idle' | 'uploading' | 'analyzing' | 'done'>('idle');
  const [analysis, setAnalysis] = useState('');

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files) {
      setFile(e.target.files[0]);
      setAnalysis('');
      setStatus('idle');
    }
  };

  const handleAnalyze = async () => {
    if (!file) return;

    // 1. Upload the file
    setStatus('uploading');
    const formData = new FormData();
    formData.append('file', file);

    try {
      const uploadResponse = await fetch('http://localhost:8000/api/code-analyzer/upload', {
        method: 'POST',
        body: formData,
      });
      const uploadData = await uploadResponse.json();

      if (!uploadData.thread_id) throw new Error("Upload failed to return thread_id");
      
      const currentThreadId = uploadData.thread_id;
      setThreadId(currentThreadId);
      setStatus('analyzing');

      // 2. Start streaming the analysis
      const url = `http://localhost:8000/api/code-analyzer/analyze?thread_id=${currentThreadId}`;
      const eventSource = new EventSource(url);

      eventSource.onmessage = (event) => {
        if (event.data === "[DONE]") {
          setStatus('done');
          eventSource.close();
          return;
        }
        if (event.data === "[ERROR]") {
          console.error("Stream error from server");
          setAnalysis("An error occurred during analysis.");
          setStatus('idle');
          eventSource.close();
          return;
        }
        try {
          const data = JSON.parse(event.data);
          if (data.analysis) {
            setAnalysis(data.analysis);
          }
        } catch (e) {
          console.error("Failed to parse JSON:", e);
        }
      };

      eventSource.onerror = () => {
        setAnalysis("Failed to connect to the analysis service.");
        setStatus('idle');
        eventSource.close();
      };

    } catch (error) {
      console.error("Analysis process failed:", error);
      setStatus('idle');
    }
  };

  return (
    <div className="flex flex-col h-full max-w-4xl mx-auto">
      <div className="flex-shrink-0 p-4 border-b border-gray-700">
        <h2 className="text-lg font-semibold mb-2">Upload Code File</h2>
        <div className="flex items-center gap-4">
          <input type="file" onChange={handleFileChange} className="file:mr-4 file:py-2 file:px-4 file:rounded-lg file:border-0 file:text-sm file:font-semibold file:bg-gray-700 file:text-gray-200 hover:file:bg-gray-600"/>
          <button onClick={handleAnalyze} disabled={!file || status === 'uploading' || status === 'analyzing'} className="bg-blue-600 px-4 py-2 rounded-lg disabled:bg-gray-600">
            {status === 'uploading' ? 'Uploading...' : status === 'analyzing' ? 'Analyzing...' : 'Analyze Code'}
          </button>
        </div>
      </div>
      <div className="flex-grow p-4 overflow-y-auto">
        {analysis ? (
           <div className="bg-gray-800/50 rounded-lg p-6">
             <MarkdownRenderer content={analysis} />
           </div>
        ) : (
          <div className="flex flex-col items-center justify-center h-full text-gray-500">
            <FileCode size={48} className="mb-4"/>
            <p>Upload a code file and click "Analyze" to see the results here.</p>
          </div>
        )}
      </div>
    </div>
  );
}