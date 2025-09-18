import { useEffect, useMemo, useState } from 'react';
import dynamic from 'next/dynamic';
import { config, validateGitHubUrl, apiRequest } from '../utils/config';
import { buildDiagram, validateSchema, getAvailableLanguages, getDiagramStats } from '../utils/diagramBuilder';
import { getLanguageColor } from '../utils/diagramUtils';
import { useErrorHandler, categorizeError } from '../utils/errorHandler';

const MermaidDiagram = dynamic(() => import('../components/MermaidDiagram'), { ssr: false });
const DiagramErrorBoundary = dynamic(() => import('../components/DiagramErrorBoundary'), { ssr: false });

export default function Home() {
  const [input, setInput] = useState('');
  const [prompt, setPrompt] = useState('');
  const [diagram, setDiagram] = useState('');
  const [svg, setSvg] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [diagramError, setDiagramError] = useState(null);
  const [showRawDiagram, setShowRawDiagram] = useState(false);
  const [showRelations, setShowRelations] = useState(true);
  const [showFields, setShowFields] = useState(true);
  const [showMethods, setShowMethods] = useState(true);
  const [relationFilter, setRelationFilter] = useState('all'); // all|heuristic|ai
  const [schemaData, setSchemaData] = useState(null);
  const [visibleLangs, setVisibleLangs] = useState({});
  const [colorEdgesBySource, setColorEdgesBySource] = useState(false);
  const [diagramType, setDiagramType] = useState('class'); // class|usecase|activity|sequence|state

  const errorHandler = useErrorHandler(setError, setLoading);

  // Diagram-specific error handlers
  const handleDiagramError = (errorDetails) => {
    setDiagramError(errorDetails);
    errorHandler.handleError(new Error(`Diagram rendering failed: ${errorDetails.message}`));
  };

  const handleDiagramRender = (svg, errorDetails) => {
    if (errorDetails) {
      handleDiagramError(errorDetails);
    } else {
      setSvg(svg);
      setDiagramError(null); // Clear any previous diagram errors
    }
  };

  const showDiagramFallback = () => {
    setShowRawDiagram(true);
  };

  // Handle prompt-based UML generation
  const handlePromptAnalyze = async () => {
    if (!prompt.trim()) {
      setError('Prompt is required');
      return;
    }
    errorHandler.clearError();
    setLoading(true);
    setDiagram('');
    setSvg('');
    setDiagramError(null);
    setShowRawDiagram(false);
    try {
      const result = await apiRequest('/uml-from-prompt', {
        method: 'POST',
        body: JSON.stringify({ prompt }),
      });
      const schema = result.schema || result;
      setSchemaData({ ...schema, meta: result.meta });
      setDiagram(buildDiagram(schema, diagramType, visibleLangs, {
        showFields,
        showMethods,
        showRelations,
        relationFilter,
        colorEdgesBySource
      }));
      setLoading(false);
    } catch (error) {
      await errorHandler.handleError(error, 'uml-from-prompt');
    }
  };

  const handleAnalyze = async () => {
    // Validate GitHub URL
    const validation = validateGitHubUrl(input);
    if (!validation.isValid) {
      setError(validation.error);
      return;
    }

    errorHandler.clearError();
    setLoading(true);
    setDiagram('');
    setSvg('');
    setDiagramError(null);
    setShowRawDiagram(false);
    
    const retryFn = async () => {
      const result = await apiRequest('/analyze', {
        method: 'POST',
        body: JSON.stringify({ githubUrl: validation.url }),
      });

      // Validate the received schema
      const schemaValidation = validateSchema(result.schema);
      if (!schemaValidation.isValid) {
        throw new Error(`Invalid response format: ${schemaValidation.error}`);
      }

      const schema = result.schema;
      setSchemaData({ ...schema, meta: result.meta });
      
      // Set up language visibility
      const availableLanguages = getAvailableLanguages(schema);
      const nextVis = {};
      for (const lang of availableLanguages) nextVis[lang] = true;
      setVisibleLangs(nextVis);
      
      // Build the diagram with current settings
      const diagramOptions = {
        showFields,
        showMethods,
        showRelations,
        relationFilter,
        colorEdgesBySource
      };
      
      setDiagram(buildDiagram(schema, diagramType, nextVis, diagramOptions));
      setLoading(false);
    };

    try {
      await retryFn();
    } catch (error) {
      await errorHandler.handleError(error, 'analyze', retryFn);
    }
  };













  const handleCopy = async () => {
    try {
      await navigator.clipboard.writeText(diagram);
    } catch {}
  };

  const handleDownload = () => {
    if (!svg) return;
    const blob = new Blob([svg], { type: 'image/svg+xml;charset=utf-8' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = 'uml.svg';
    a.click();
    URL.revokeObjectURL(url);
  };

  return (
    <div className="min-h-screen flex flex-col items-center justify-center bg-gradient-to-br from-pink-100 via-blue-50 to-emerald-100 px-4 py-8">
      <div className="w-full max-w-3xl bg-white/80 rounded-2xl shadow-xl p-8 flex flex-col items-center">
        <h1 className="text-4xl font-extrabold mb-2 text-emerald-700 tracking-tight text-center">UML Designer AI</h1>
        <p className="mb-6 text-lg text-gray-600 text-center">Generate beautiful UML diagrams (Class, Use Case, Activity, Sequence, State) from your code repositories or natural language prompts.</p>
        <div className="w-full flex flex-col gap-2 mb-4">
          <input
            className="border-2 border-emerald-200 focus:border-emerald-400 rounded-lg px-4 py-2 text-lg transition outline-none bg-white/90"
            placeholder="Paste GitHub repo URL (public)"
            value={input}
            onChange={e => setInput(e.target.value)}
            disabled={loading}
          />
          <div className="flex items-center gap-2 mt-2">
            <input
              className="border-2 border-pink-200 focus:border-pink-400 rounded-lg px-4 py-2 text-lg transition outline-none bg-white/90 flex-1"
              placeholder="Or describe your system (prompt)"
              value={prompt}
              onChange={e => setPrompt(e.target.value)}
              disabled={loading}
            />
            <button
              className="bg-gradient-to-r from-pink-400 to-emerald-400 text-white font-semibold px-4 py-2 rounded-lg shadow hover:from-pink-500 hover:to-emerald-500 transition disabled:opacity-50"
              onClick={handlePromptAnalyze}
              disabled={loading || !prompt.trim()}
            >
              {loading ? 'Generating…' : 'Prompt Analyze'}
            </button>
          </div>
          <div className="flex items-center gap-3 flex-wrap">
            <label className="text-sm text-gray-600">Diagram:</label>
            <select
              className="border rounded px-2 py-1 text-sm"
              value={diagramType}
              onChange={e => {
                const t = e.target.value;
                setDiagramType(t);
                if (schemaData) {
                  const diagramOptions = {
                    showFields,
                    showMethods,
                    showRelations,
                    relationFilter,
                    colorEdgesBySource
                  };
                  setDiagram(buildDiagram(schemaData, t, visibleLangs, diagramOptions));
                }
              }}
              disabled={loading}
            >
              <option value="class">Class</option>
              <option value="usecase">Use Case</option>
              <option value="activity">Activity</option>
              <option value="sequence">Sequence</option>
              <option value="state">State</option>
            </select>
          </div>
          <button
            className="bg-gradient-to-r from-emerald-400 to-pink-400 text-white font-semibold px-6 py-2 rounded-lg shadow hover:from-emerald-500 hover:to-pink-500 transition disabled:opacity-50"
            onClick={handleAnalyze}
            disabled={loading || !input.trim()}
          >
            {loading ? 'Analyzing…' : 'Analyze'}
          </button>
          {diagramType === 'class' && (
            <>
              <label className="flex items-center gap-2 text-sm text-gray-600 select-none">
                <input type="checkbox" checked={showRelations} onChange={e => { 
                  setShowRelations(e.target.checked); 
                  if (schemaData) {
                    const diagramOptions = {
                      showFields,
                      showMethods,
                      showRelations: e.target.checked,
                      relationFilter,
                      colorEdgesBySource
                    };
                    setDiagram(buildDiagram(schemaData, diagramType, visibleLangs, diagramOptions));
                  }
                }} />
                Show relations (extends/implements/uses)
              </label>
              <div className="flex flex-wrap gap-3 text-sm text-gray-600">
                <label className="flex items-center gap-2">
                  <input type="checkbox" checked={showFields} onChange={e => { 
                    setShowFields(e.target.checked); 
                    if (schemaData) {
                      const diagramOptions = {
                        showFields: e.target.checked,
                        showMethods,
                        showRelations,
                        relationFilter,
                        colorEdgesBySource
                      };
                      setDiagram(buildDiagram(schemaData, diagramType, visibleLangs, diagramOptions));
                    }
                  }} /> Fields
                </label>
                <label className="flex items-center gap-2">
                  <input type="checkbox" checked={showMethods} onChange={e => { 
                    setShowMethods(e.target.checked); 
                    if (schemaData) {
                      const diagramOptions = {
                        showFields,
                        showMethods: e.target.checked,
                        showRelations,
                        relationFilter,
                        colorEdgesBySource
                      };
                      setDiagram(buildDiagram(schemaData, diagramType, visibleLangs, diagramOptions));
                    }
                  }} /> Methods
                </label>
                <label className="flex items-center gap-2">
                  Source:
                  <select className="border rounded px-2 py-1" value={relationFilter} onChange={e => { 
                    setRelationFilter(e.target.value); 
                    if (schemaData) {
                      const diagramOptions = {
                        showFields,
                        showMethods,
                        showRelations,
                        relationFilter: e.target.value,
                        colorEdgesBySource
                      };
                      setDiagram(buildDiagram(schemaData, diagramType, visibleLangs, diagramOptions));
                    }
                  }}>
                    <option value="all">All</option>
                    <option value="heuristic">Heuristic</option>
                    <option value="ai">AI</option>
                  </select>
                </label>
                <label className="flex items-center gap-2">
                  <input type="checkbox" checked={colorEdgesBySource} onChange={e => { 
                    setColorEdgesBySource(e.target.checked); 
                    if (schemaData) {
                      const diagramOptions = {
                        showFields,
                        showMethods,
                        showRelations,
                        relationFilter,
                        colorEdgesBySource: e.target.checked
                      };
                      setDiagram(buildDiagram(schemaData, diagramType, visibleLangs, diagramOptions));
                    }
                  }} /> Color AI edges
                </label>
              </div>
            </>
          )}
        </div>
        {error && <div className="text-red-500 mb-2 text-center">{error}</div>}
        {diagram && (
          <div className="w-full bg-white/90 rounded-lg p-4 mt-4 shadow-inner overflow-x-auto">
            <div className="flex justify-end gap-2 mb-2">
              <button onClick={handleCopy} className="text-sm px-3 py-1 rounded bg-emerald-100 text-emerald-700 hover:bg-emerald-200">Copy Mermaid</button>
              <button onClick={handleDownload} className="text-sm px-3 py-1 rounded bg-pink-100 text-pink-700 hover:bg-pink-200">Download SVG</button>
            </div>
            {diagramType === 'class' && (
              <div className="text-xs text-gray-500 mb-3">
                Legend: Base <span title="extends">&lt;|--</span> Derived, Interface <span title="implements">&lt;|..</span> Class, Whole <span title="composition">*--</span> Part, Whole <span title="aggregation">o--</span> Part, Uses <span title="uses">..&gt;</span> <span className="ml-2">[H=heuristic, AI=model]</span>
              </div>
            )}
            {diagramType === 'usecase' && (
              <div className="text-xs text-gray-500 mb-3">
                Legend: User interacts with system use cases, System boundary contains all use case functionality
              </div>
            )}
            {diagramType === 'activity' && (
              <div className="text-xs text-gray-500 mb-3">
                Legend: Rounded rectangles = Activities, Diamonds = Decisions, Circles = Start/End, Bars = Parallel execution
              </div>
            )}
            {diagramType === 'sequence' && (
              <div className="text-xs text-gray-500 mb-3">
                Legend: Vertical lines = Lifelines, Horizontal arrows = Messages, Rectangles = Activations, Boxes = Alternatives
              </div>
            )}
            {diagramType === 'state' && (
              <div className="text-xs text-gray-500 mb-3">
                Legend: Rounded rectangles = States, Arrows = Transitions, Circles = Start/End, Nested boxes = Composite states
              </div>
            )}
            {schemaData && (
              <div className="text-xs text-gray-600 mb-3 flex flex-wrap gap-3">
                {schemaData.meta && (
                  <div className="mr-4 opacity-80">
                    {schemaData.meta.commit && <span className="mr-3">commit: {schemaData.meta.commit.slice(0,7)}</span>}
                    {typeof schemaData.meta.files_scanned === 'number' && <span>files: {schemaData.meta.files_scanned}</span>}
                  </div>
                )}
                {diagramType === 'class' && Object.keys(schemaData).filter(k => k !== 'relations' && Array.isArray(schemaData[k]) && schemaData[k].length > 0).map(lang => (
                  <label key={lang} className="flex items-center gap-2">
                    <span
                      className="inline-block w-3 h-3 rounded"
                      style={{ backgroundColor: ({
                        java: '#fde68a', python: '#bfdbfe', csharp: '#fca5a5', javascript: '#fcd34d', typescript: '#93c5fd', cpp: '#c7d2fe', c: '#a7f3d0'
                      }[lang] || '#e5e7eb') }}
                    />
                    <input
                      type="checkbox"
                      checked={!!visibleLangs[lang]}
                      onChange={e => {
                        const next = { ...visibleLangs, [lang]: e.target.checked };
                        setVisibleLangs(next);
                        const diagramOptions = {
                          showFields,
                          showMethods,
                          showRelations,
                          relationFilter,
                          colorEdgesBySource
                        };
                        setDiagram(buildDiagram(schemaData, diagramType, next, diagramOptions));
                      }}
                    /> {lang}
                  </label>
                ))}
              </div>
            )}
            
            {/* Enhanced diagram rendering with error boundary */}
            <DiagramErrorBoundary 
              onError={handleDiagramError}
              onFallback={showDiagramFallback}
            >
              <MermaidDiagram 
                chart={diagram} 
                onRender={handleDiagramRender}
                onError={handleDiagramError}
                timeout={30000}
                className="diagram-container"
                fallbackContent={
                  <div className="text-gray-500 text-center py-8">
                    Enter a GitHub repository URL to generate UML diagrams
                  </div>
                }
              />
            </DiagramErrorBoundary>

            {/* Raw diagram fallback */}
            {showRawDiagram && diagram && (
              <div className="mt-4 p-4 bg-gray-100 rounded-lg">
                <div className="flex justify-between items-center mb-2">
                  <h3 className="font-semibold text-gray-700">Raw Diagram Code</h3>
                  <button
                    onClick={() => setShowRawDiagram(false)}
                    className="text-gray-500 hover:text-gray-700"
                  >
                    ✕
                  </button>
                </div>
                <pre className="text-sm overflow-auto bg-white p-3 rounded border">
                  {diagram}
                </pre>
                <div className="mt-2 text-xs text-gray-600">
                  Copy this code to render manually in any Mermaid-compatible editor
                </div>
              </div>
            )}

            {/* Diagram error details (development only) */}
            {process.env.NODE_ENV === 'development' && diagramError && (
              <div className="mt-4 p-4 bg-red-50 border border-red-200 rounded-lg">
                <h3 className="font-semibold text-red-800 mb-2">Diagram Error Details</h3>
                <div className="text-sm text-red-700">
                  <p><strong>Message:</strong> {diagramError.message}</p>
                  <p><strong>Context:</strong> {diagramError.context}</p>
                  <p><strong>Attempts:</strong> {diagramError.attempts}</p>
                  {diagramError.chart && (
                    <details className="mt-2">
                      <summary className="cursor-pointer font-semibold">Chart Data (truncated)</summary>
                      <pre className="mt-1 text-xs bg-red-100 p-2 rounded overflow-auto">
                        {diagramError.chart}
                      </pre>
                    </details>
                  )}
                </div>
              </div>
            )}
          </div>
        )}
      </div>
      <footer className="mt-8 text-gray-400 text-sm">Made with <span className="text-pink-400">♥</span> by G Karthik</footer>
    </div>
  );
}
