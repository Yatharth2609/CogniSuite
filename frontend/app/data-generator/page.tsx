'use client';
import { useState } from 'react';

export default function DataGeneratorPage() {
  const [prompt, setPrompt] = useState('A person with a first name, last name, and a job title.');
  const [count, setCount] = useState(5);
  const [jsonData, setJsonData] = useState('');
  const [isLoading, setIsLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    if (!prompt || count < 1) return;

    setIsLoading(true);
    setJsonData('');

    const url = `http://localhost:8000/api/generate-data?prompt=${encodeURIComponent(prompt)}&count=${encodeURIComponent(count)}`;
    const eventSource = new EventSource(url);

    // Using your provided EventSource handler logic
    eventSource.onmessage = (event) => {
      let rawData = event.data;
      
      // The native EventSource should strip the "data: " prefix automatically,
      // but this check adds robustness in case it doesn't.
      if (rawData.startsWith("data: ")) {
        rawData = rawData.slice(6);
      }
      
      if (rawData === "[DONE]") {
        setIsLoading(false);
        eventSource.close();
        return;
      }
      
      if (rawData === "[ERROR]") {
        console.error("Stream error from server");
        setJsonData("An error occurred on the server.");
        setIsLoading(false);
        eventSource.close();
        return;
      }
      
      try {
        const data = JSON.parse(rawData);
        // Modified to handle the data generator's output
        if (data.output?.generated_json) {
          const parsedInnerJson = JSON.parse(data.output.generated_json);
          setJsonData(JSON.stringify(parsedInnerJson, null, 2));
        }
      } catch (e) {
        console.error("Failed to parse JSON from stream:", rawData, e);
      }
    };
    
    eventSource.onerror = (err) => {
      console.error("EventSource failed:", err);
      setIsLoading(false);
      setJsonData("Failed to connect to the stream.");
      eventSource.close();
    };
  };

  return (
    <div className="flex flex-col h-full gap-8">
      <div className="flex-shrink-0">
        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label htmlFor="prompt" className="block text-sm font-medium text-gray-300 mb-2">Data Description</label>
            <textarea
              id="prompt"
              rows={3}
              value={prompt}
              onChange={(e) => setPrompt(e.target.value)}
              className="w-full bg-gray-800 border border-gray-700 rounded-lg px-4 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
              placeholder="e.g., A product with a name, price, and category."
            />
          </div>
          <div className="flex items-end gap-4">
            <div className="w-24">
              <label htmlFor="count" className="block text-sm font-medium text-gray-300 mb-2">Count</label>
              <input
                type="number"
                id="count"
                value={count}
                onChange={(e) => setCount(Number(e.target.value))}
                className="w-full bg-gray-800 border border-gray-700 rounded-lg px-4 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
            </div>
            <button
              type="submit"
              disabled={isLoading}
              className="bg-blue-600 hover:bg-blue-500 text-white font-semibold px-6 py-2 rounded-lg disabled:bg-gray-600 disabled:cursor-not-allowed"
            >
              {isLoading ? 'Generating...' : 'Generate Data'}
            </button>
          </div>
        </form>
      </div>
      <div className="flex-grow bg-gray-900/70 rounded-lg border border-gray-700 p-4 overflow-auto">
        <pre className="text-sm text-green-300">
          <code>
            {isLoading && !jsonData ? 'Waiting for generated data...' : jsonData}
          </code>
        </pre>
      </div>
    </div>
  );
}