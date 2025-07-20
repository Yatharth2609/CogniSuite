'use client';
import React, { useState, useCallback } from 'react';
import Link from 'next/link';

// Types for better TypeScript support
interface VectorGraphicsRequest {
  prompt: string;
  vector_format: 'svg' | 'eps' | 'pdf';
  style: 'modern' | 'minimalist' | 'detailed' | 'artistic';
  complexity: 'simple' | 'medium' | 'complex';
  color_scheme: 'default' | 'monochrome' | 'vibrant' | 'pastel';
}

interface GenerationResponse {
  step: string;
  output: {
    svg_code?: string;
    vector_code?: string;
    format_specific_code?: Record<string, string>;
    is_valid?: boolean;
    validation_errors?: string[];
    generation_attempts?: number;
    generation_metadata?: Record<string, any>;
  };
  is_valid?: boolean;
  validation_errors?: string[];
  generation_attempts?: number;
  format?: string;
  error?: string;
}

export default function VectorGraphicsStudioPage() {
  // State management
  const [prompt, setPrompt] = useState('A modern minimalist logo with geometric shapes');
  const [vectorFormat, setVectorFormat] = useState<'svg' | 'eps' | 'pdf'>('svg');
  const [style, setStyle] = useState<'modern' | 'minimalist' | 'detailed' | 'artistic'>('modern');
  const [complexity, setComplexity] = useState<'simple' | 'medium' | 'complex'>('medium');
  const [colorScheme, setColorScheme] = useState<'default' | 'monochrome' | 'vibrant' | 'pastel'>('default');
  
  // Output state
  const [vectorCode, setVectorCode] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [isValid, setIsValid] = useState(false);
  const [validationErrors, setValidationErrors] = useState<string[]>([]);
  const [generationAttempts, setGenerationAttempts] = useState(0);
  const [generationMetadata, setGenerationMetadata] = useState<Record<string, any>>({});
  const [currentEventSource, setCurrentEventSource] = useState<EventSource | null>(null);

  // Enhanced generation handler using EventSource
  const handleGenerate = useCallback(async (e: React.FormEvent) => {
    e.preventDefault();
    if (!prompt.trim()) return;

    // Close any existing EventSource connection
    if (currentEventSource) {
      currentEventSource.close();
      setCurrentEventSource(null);
    }

    // Reset state
    setIsLoading(true);
    setVectorCode('');
    setIsValid(false);
    setValidationErrors([]);
    setGenerationAttempts(0);
    setGenerationMetadata({});

    // Build URL for EventSource
    let url = `http://localhost:8000/api/generate-${vectorFormat}?prompt=${encodeURIComponent(prompt)}&style=${style}`;
    
    // Add additional parameters for SVG
    if (vectorFormat === 'svg') {
      url += `&complexity=${complexity}&color_scheme=${colorScheme}`;
    }

    console.log('Connecting to:', url);

    const eventSource = new EventSource(url);
    setCurrentEventSource(eventSource);

    eventSource.onopen = (event) => {
      console.log('EventSource connection opened:', event);
    };

    eventSource.onmessage = (event) => {
      console.log('Received message:', event.data);
      
      let raw = event.data;
      
      // Clean data prefix if present
      if (raw.startsWith("data: ")) {
        raw = raw.slice(6);
      }

      console.log('Processing raw data:', JSON.stringify(raw));

      // Handle completion tokens
      if (raw === "[DONE]") {
        console.log('Generation completed successfully');
        setIsLoading(false);
        eventSource.close();
        setCurrentEventSource(null);
        return;
      }
      
      if (raw === "[ERROR]") {
        console.error("Stream error received");
        setIsLoading(false);
        setValidationErrors(['An error occurred during generation']);
        eventSource.close();
        setCurrentEventSource(null);
        return;
      }

      // Handle empty or whitespace-only messages
      if (!raw || raw.trim() === '') {
        console.log('Empty message received, skipping...');
        return;
      }

      // Parse JSON response
      try {
        const data: GenerationResponse = JSON.parse(raw);
        console.log('Parsed data:', data);
        handleGenerationResponse(data);
      } catch (parseError) {
        console.error('JSON Parse error:', parseError);
        console.error('Raw data that failed to parse:', JSON.stringify(raw));
        
        // Don't break the connection for parse errors, just log them
        // The generation might still be in progress
      }
    };
    
    eventSource.onerror = (error) => {
      console.error("EventSource error:", error);
      console.error("EventSource readyState:", eventSource.readyState);
      
      setIsLoading(false);
      
      // Add more specific error handling
      if (eventSource.readyState === EventSource.CLOSED) {
        console.log('EventSource connection was closed');
      } else if (eventSource.readyState === EventSource.CONNECTING) {
        console.log('EventSource is trying to reconnect...');
      }
      
      setValidationErrors(['Connection error occurred. Please try again.']);
      eventSource.close();
      setCurrentEventSource(null);
    };
  }, [prompt, vectorFormat, style, complexity, colorScheme, currentEventSource]);

  // Handle generation response
  const handleGenerationResponse = useCallback((data: GenerationResponse) => {
    console.log('Handling generation response:', data);
    
    if (data.output) {
      // Handle vector code based on format
      if (vectorFormat === 'svg' && data.output.svg_code) {
        console.log('Setting SVG code');
        setVectorCode(data.output.svg_code);
      } else if (data.output.vector_code) {
        console.log('Setting vector code');
        setVectorCode(data.output.vector_code);
      }
      
      // Handle validation status
      const validStatus = data.output.is_valid ?? data.is_valid ?? false;
      const errors = data.output.validation_errors ?? data.validation_errors ?? [];
      const attempts = data.output.generation_attempts ?? data.generation_attempts ?? 1;
      
      console.log('Validation status:', validStatus, 'Errors:', errors, 'Attempts:', attempts);
      
      setIsValid(validStatus);
      setValidationErrors(errors);
      setGenerationAttempts(attempts);
      setGenerationMetadata(data.output.generation_metadata ?? {});
    }
    
    if (data.error) {
      console.error('Response contains error:', data.error);
      setValidationErrors([data.error]);
      setIsValid(false);
    }
  }, [vectorFormat]);

  // Cancel generation
  const handleCancel = useCallback(() => {
    if (currentEventSource) {
      console.log('Cancelling generation...');
      currentEventSource.close();
      setCurrentEventSource(null);
      setIsLoading(false);
    }
  }, [currentEventSource]);

  // Download handler for generated code
  const handleDownload = useCallback(() => {
    if (!vectorCode) return;
    
    const extensions = { svg: 'svg', eps: 'eps', pdf: 'py' };
    const mimeTypes = { 
      svg: 'image/svg+xml', 
      eps: 'application/postscript', 
      pdf: 'text/x-python' 
    };
    
    const blob = new Blob([vectorCode], { type: mimeTypes[vectorFormat] });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `generated_vector.${extensions[vectorFormat]}`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  }, [vectorCode, vectorFormat]);

  // Copy to clipboard
  const handleCopy = useCallback(() => {
    if (vectorCode) {
      navigator.clipboard.writeText(vectorCode).then(() => {
        console.log('Code copied to clipboard');
        // You could add a toast notification here
      }).catch(err => {
        console.error('Failed to copy code:', err);
      });
    }
  }, [vectorCode]);

  // Cleanup on unmount
  React.useEffect(() => {
    return () => {
      if (currentEventSource) {
        currentEventSource.close();
      }
    };
  }, [currentEventSource]);

  return (
    <div className="flex flex-col h-full gap-6">
      {/* Header */}
      <div className="flex-shrink-0">
        <h1 className="text-3xl font-bold text-white mb-2">Vector Graphics Studio</h1>
        <p className="text-gray-400">Generate professional vector graphics in multiple formats using EventSource streaming</p>
      </div>

      {/* Generation Form */}
      <div className="flex-shrink-0">
        <form onSubmit={handleGenerate} className="space-y-4">
          {/* Prompt Input */}
          <div>
            <label className="block text-sm font-medium text-gray-300 mb-2">
              Prompt
            </label>
            <input
              type="text"
              value={prompt}
              onChange={(e) => setPrompt(e.target.value)}
              disabled={isLoading}
              className="w-full bg-gray-800 border border-gray-700 rounded-lg px-4 py-3 focus:outline-none focus:ring-2 focus:ring-blue-500 text-white placeholder-gray-400 disabled:opacity-50"
              placeholder="Describe the vector graphic you want to generate..."
            />
          </div>

          {/* Controls Grid */}
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            {/* Vector Format */}
            <div>
              <label className="block text-sm font-medium text-gray-300 mb-2">
                Format
              </label>
              <select
                value={vectorFormat}
                onChange={(e) => setVectorFormat(e.target.value as 'svg' | 'eps' | 'pdf')}
                disabled={isLoading}
                className="w-full bg-gray-800 border border-gray-700 rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500 text-white disabled:opacity-50"
              >
                <option value="svg">SVG</option>
                <option value="eps">EPS</option>
                <option value="pdf">PDF (Python)</option>
              </select>
            </div>

            {/* Style */}
            <div>
              <label className="block text-sm font-medium text-gray-300 mb-2">
                Style
              </label>
              <select
                value={style}
                onChange={(e) => setStyle(e.target.value as 'modern' | 'minimalist' | 'detailed' | 'artistic')}
                disabled={isLoading}
                className="w-full bg-gray-800 border border-gray-700 rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500 text-white disabled:opacity-50"
              >
                <option value="modern">Modern</option>
                <option value="minimalist">Minimalist</option>
                <option value="detailed">Detailed</option>
                <option value="artistic">Artistic</option>
              </select>
            </div>

            {/* Complexity */}
            <div>
              <label className="block text-sm font-medium text-gray-300 mb-2">
                Complexity
              </label>
              <select
                value={complexity}
                onChange={(e) => setComplexity(e.target.value as 'simple' | 'medium' | 'complex')}
                disabled={isLoading}
                className="w-full bg-gray-800 border border-gray-700 rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500 text-white disabled:opacity-50"
              >
                <option value="simple">Simple</option>
                <option value="medium">Medium</option>
                <option value="complex">Complex</option>
              </select>
            </div>

            {/* Color Scheme */}
            <div>
              <label className="block text-sm font-medium text-gray-300 mb-2">
                Colors
              </label>
              <select
                value={colorScheme}
                onChange={(e) => setColorScheme(e.target.value as 'default' | 'monochrome' | 'vibrant' | 'pastel')}
                disabled={isLoading}
                className="w-full bg-gray-800 border border-gray-700 rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500 text-white disabled:opacity-50"
              >
                <option value="default">Default</option>
                <option value="monochrome">Monochrome</option>
                <option value="vibrant">Vibrant</option>
                <option value="pastel">Pastel</option>
              </select>
            </div>
          </div>

          {/* Action Buttons */}
          <div className="flex gap-4">
            <button
              type="submit"
              disabled={isLoading}
              className="bg-blue-600 hover:bg-blue-500 text-white font-semibold px-8 py-3 rounded-lg disabled:bg-gray-600 disabled:cursor-not-allowed transition-colors"
            >
              {isLoading ? 'Generating...' : 'Generate Vector Graphics'}
            </button>
            
            {isLoading && (
              <button
                type="button"
                onClick={handleCancel}
                className="bg-red-600 hover:bg-red-500 text-white font-semibold px-6 py-3 rounded-lg transition-colors"
              >
                Cancel
              </button>
            )}
            
            {vectorCode && !isLoading && (
              <>
                <button
                  type="button"
                  onClick={handleDownload}
                  className="bg-green-600 hover:bg-green-500 text-white font-semibold px-6 py-3 rounded-lg transition-colors"
                >
                  Download
                </button>
                
                <button
                  type="button"
                  onClick={handleCopy}
                  className="bg-purple-600 hover:bg-purple-500 text-white font-semibold px-6 py-3 rounded-lg transition-colors"
                >
                  Copy Code
                </button>
              </>
            )}
          </div>
        </form>
      </div>

      {/* Status Information */}
      {(isLoading || generationAttempts > 0) && (
        <div className="flex-shrink-0 bg-gray-800/50 rounded-lg border border-gray-700 p-4">
          <div className="flex items-center gap-4 text-sm">
            {isLoading && (
              <div className="flex items-center gap-2">
                <div className="animate-spin h-4 w-4 border-2 border-blue-500 border-t-transparent rounded-full"></div>
                <span className="text-blue-400">Generating {vectorFormat.toUpperCase()}...</span>
              </div>
            )}
            
            {generationAttempts > 0 && (
              <span className="text-gray-400">
                Attempt: {generationAttempts}
              </span>
            )}
            
            {isValid !== undefined && (
              <span className={`${isValid ? 'text-green-400' : 'text-red-400'}`}>
                {isValid ? '✓ Valid' : '✗ Invalid'}
              </span>
            )}
          </div>
          
          {validationErrors.length > 0 && (
            <div className="mt-2 space-y-1">
              {validationErrors.map((error, index) => (
                <div key={index} className="text-red-400 text-sm">
                  • {error}
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {/* Preview/Code Display */}
      <div className="flex-grow bg-gray-800/50 rounded-lg border border-gray-700 overflow-hidden">
        <div className="h-full flex">
          {/* Preview Panel (for SVG) */}
          {vectorFormat === 'svg' && (
            <div className="flex-1 p-4 flex items-center justify-center border-r border-gray-700">
              {isLoading && (
                <div className="flex items-center gap-3 text-gray-400">
                  <div className="animate-spin h-8 w-8 border-2 border-blue-500 border-t-transparent rounded-full"></div>
                  <span>Generating preview...</span>
                </div>
              )}
              
              {vectorCode && vectorFormat === 'svg' && (
                <div
                  className="w-full h-full flex items-center justify-center"
                  dangerouslySetInnerHTML={{ __html: vectorCode }}
                />
              )}
              
              {!isLoading && !vectorCode && (
                <p className="text-gray-500">Vector graphic preview will appear here</p>
              )}
            </div>
          )}
          
          {/* Code Panel */}
          <div className={`${vectorFormat === 'svg' ? 'flex-1' : 'w-full'} flex flex-col`}>
            <div className="p-3 bg-gray-900 border-b border-gray-700 flex justify-between items-center">
              <h3 className="text-sm font-medium text-gray-300">
                {vectorFormat.toUpperCase()} Code
              </h3>
              {vectorCode && (
                <button
                  onClick={handleCopy}
                  className="text-xs bg-gray-700 hover:bg-gray-600 px-3 py-1 rounded text-gray-300 transition-colors"
                >
                  Copy
                </button>
              )}
            </div>
            
            <div className="flex-1 p-4 overflow-auto">
              {vectorCode ? (
                <pre className="text-sm text-gray-300 whitespace-pre-wrap font-mono">
                  <code>{vectorCode}</code>
                </pre>
              ) : (
                <p className="text-gray-500 text-center">
                  Generated {vectorFormat.toUpperCase()} code will appear here
                </p>
              )}
            </div>
          </div>
        </div>
      </div>

      {/* Metadata Display */}
      {Object.keys(generationMetadata).length > 0 && (
        <div className="flex-shrink-0 bg-gray-800/30 rounded-lg border border-gray-700 p-4">
          <h4 className="text-sm font-medium text-gray-300 mb-2">Generation Details</h4>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-xs text-gray-400">
            {Object.entries(generationMetadata).map(([key, value]) => (
              <div key={key}>
                <span className="font-medium">{key}:</span> {String(value)}
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
