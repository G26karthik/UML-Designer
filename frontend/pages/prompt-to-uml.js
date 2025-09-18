import React, { useState, useMemo } from 'react';
import MermaidDiagram from '../components/MermaidDiagram';
import { apiRequest } from '../utils/config';

export default function PromptToUML() {

  const [prompt, setPrompt] = useState('');
  const [diagram, setDiagram] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [debouncedPrompt, setDebouncedPrompt] = useState('');

  // Debounce prompt input for smoother UX
  useMemo(() => {
    const handler = setTimeout(() => setDebouncedPrompt(prompt), 300);
    return () => clearTimeout(handler);
  }, [prompt]);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError('');
    setDiagram('');
    try {
      // Use versioned API helper for consistent routing
      const data = await apiRequest('/uml-from-prompt', {
        method: 'POST',
        body: JSON.stringify({ prompt: debouncedPrompt })
      });
      // Accept both .diagram and .schema keys for compatibility
      setDiagram(data.diagram || data.schema || '');
    } catch (err) {
      setError('Failed to generate UML diagram.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gray-50 flex flex-col items-center justify-center p-4">
      <h1 className="text-2xl font-bold mb-4">Prompt to UML Diagram</h1>
      <form onSubmit={handleSubmit} className="w-full max-w-xl mb-6">
        <textarea
          className="w-full p-2 border rounded mb-2"
          rows={4}
          placeholder="Describe your system, requirements, or codebase in English..."
          value={prompt}
          onChange={e => setPrompt(e.target.value)}
        />
        <button
          type="submit"
          className="bg-blue-600 text-white px-4 py-2 rounded hover:bg-blue-700"
          disabled={loading || !prompt.trim()}
        >
          {loading ? 'Generating...' : 'Generate UML'}
        </button>
      </form>
      {error && <div className="text-red-600 mb-2">{error}</div>}
      {diagram && (
        <div className="w-full max-w-2xl bg-white p-4 rounded shadow">
          {/* Memoized diagram rendering for performance */}
          {useMemo(() => <MermaidDiagram diagram={diagram} />, [diagram])}
        </div>
      )}
    </div>
  );
}
