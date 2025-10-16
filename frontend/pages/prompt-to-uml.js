import { useState } from 'react';
import { apiRequest } from '../utils/config';
import dynamic from 'next/dynamic';

const PlantUMLDiagram = dynamic(() => import('../components/PlantUMLDiagram'), { ssr: false });

export default function PromptToUML() {
  const [prompt, setPrompt] = useState('');
  const [diagram, setDiagram] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [diagramType, setDiagramType] = useState('class');
  const [showRawCode, setShowRawCode] = useState(false);

  const diagramTypes = [
    'class', 'sequence', 'usecase', 'state', 'activity', 'component', 'communication', 'deployment'
  ];

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError('');
    setDiagram('');
    try {
      const result = await apiRequest('/uml-from-prompt', {
        method: 'POST',
        body: JSON.stringify({ prompt, diagramType }),
      });
      if (result.diagram) {
        setDiagram(result.diagram);
      } else {
        setError('No diagram returned from server');
      }
    } catch (err) {
      setError(err.message || 'An error occurred');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex flex-col items-center justify-center bg-gradient-to-br from-pink-100 via-blue-50 to-emerald-100 px-4 py-8">
      <div className="w-full max-w-2xl bg-white/80 rounded-2xl shadow-xl p-8 flex flex-col items-center">
        <h1 className="text-3xl font-extrabold mb-2 text-emerald-700 tracking-tight text-center">Prompt to UML</h1>
        <p className="mb-4 text-lg text-gray-600 text-center">
          Generate UML diagrams from natural language prompts.
        </p>
        
        {/* Diagram Type Selection */}
        <div className="w-full mb-6">
          <label className="block text-sm font-medium text-gray-700 mb-2">Diagram Type:</label>
          <div className="flex flex-wrap gap-2 justify-center">
            {diagramTypes.map(type => (
              <button
                key={type}
                type="button"
                className={`px-3 py-2 rounded-lg text-sm font-medium transition ${
                  diagramType === type 
                    ? 'bg-emerald-600 text-white shadow-md' 
                    : 'bg-gray-100 text-gray-700 hover:bg-emerald-100'
                }`}
                onClick={() => setDiagramType(type)}
                disabled={loading}
              >
                {type.charAt(0).toUpperCase() + type.slice(1)}
              </button>
            ))}
          </div>
        </div>
        
        <form onSubmit={handleSubmit} className="w-full flex flex-col gap-4 mb-4">
          <textarea
            className="border-2 border-emerald-200 focus:border-emerald-400 rounded-lg px-4 py-2 text-lg transition outline-none bg-white/90 min-h-[100px]"
            placeholder="Describe your system, e.g. 'A library system with books, authors, and borrowers'"
            value={prompt}
            onChange={e => setPrompt(e.target.value)}
            disabled={loading}
            required
          />
          <button
            type="submit"
            className="bg-emerald-600 hover:bg-emerald-700 text-white font-semibold py-2 px-6 rounded-lg transition"
            disabled={loading}
          >
            {loading ? 'Generating...' : `Generate ${diagramType.charAt(0).toUpperCase() + diagramType.slice(1)} Diagram`}
          </button>
        </form>
        {error && <div className="text-red-600 mb-2">{error}</div>}
        {diagram && (
          <div className="w-full mt-4">
            <div className="flex justify-between items-center mb-2">
              <h2 className="text-lg font-bold">Generated {diagramType.charAt(0).toUpperCase() + diagramType.slice(1)} Diagram</h2>
              <button
                onClick={() => setShowRawCode(!showRawCode)}
                className="px-3 py-1 bg-gray-200 hover:bg-gray-300 rounded text-sm transition"
              >
                {showRawCode ? 'Show Visual' : 'Show Code'}
              </button>
            </div>
            {showRawCode ? (
              <pre className="bg-gray-100 p-4 rounded-lg overflow-auto text-sm">{diagram}</pre>
            ) : (
              <div className="border rounded-lg p-4 bg-white">
                <PlantUMLDiagram uml={diagram} />
              </div>
            )}
          </div>
        )}
      </div>
    </div>
	);
}
