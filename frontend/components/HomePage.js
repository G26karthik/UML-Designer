import { useEffect, useMemo, useState } from 'react';
import dynamic from 'next/dynamic';
import { validateGitHubUrl, apiRequest } from '../utils/config';
import { buildDiagram, validateSchema, getAvailableLanguages, getDiagramStats } from '../utils/diagramBuilder';
// errorHandler.js and related exports removed. Use simple error handling below.

const PlantUMLDiagram = dynamic(() => import('./PlantUMLDiagram'), { ssr: false });

// Only allow supported diagram types and hardcode renderer logic
const DIAGRAM_TYPES = ['class', 'usecase', 'activity', 'sequence', 'state', 'component', 'communication', 'deployment'];
const DIAGRAM_LABELS = {
  class: 'Class',
  usecase: 'Use Case',
  activity: 'Activity',
  sequence: 'Sequence',
  state: 'State',
  component: 'Component',
  communication: 'Communication',
  deployment: 'Deployment',
};
// Map diagram type to renderer
const getRendererForType = (type) => {
  // PlantUML supports all diagram types in this app
  return "plantuml";
};

export default function HomePage() {
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
  const [relationFilter, setRelationFilter] = useState('all');
  const [schemaData, setSchemaData] = useState(null);
  const [visibleLangs, setVisibleLangs] = useState({});
  const [colorEdgesBySource, setColorEdgesBySource] = useState(false);
  const [diagramType, setDiagramType] = useState('class');
  // Remove diagramFormat state, always use renderer mapping
  const [lastPrompt, setLastPrompt] = useState(''); // Track last prompt for regeneration
  const [isPromptDiagram, setIsPromptDiagram] = useState(false); // Track if current diagram is from prompt

  // errorHandler removed. Use setError and setLoading directly.



  // Auto-regenerate when format or type changes for prompt-based diagrams
  useEffect(() => {
    if (isPromptDiagram && lastPrompt && !loading) {
      // Regenerate the diagram with new type
      const regenerate = async () => {
        setLoading(true);
        setDiagram('');
        setSvg('');
        setDiagramError(null);

        try {
          const renderer = getRendererForType(diagramType);
          const result = await apiRequest('/uml-from-prompt', {
            method: 'POST',
            body: JSON.stringify({
              prompt: lastPrompt,
              diagramType: diagramType,
              format: renderer
            })
          });

          if (result.diagram) {
            setDiagram(result.diagram);
          } else {
            throw new Error('No diagram returned from server');
          }
        } catch (err) {
          setError('An error occurred while regenerating the UML diagram.');
          setLoading(false);
        } finally {
          setLoading(false);
        }
      };
      regenerate();
    }
  }, [diagramType]); // Only re-run when type changes

  const handleDiagramError = (errorDetails) => {
  setDiagramError(errorDetails);
  setError(`Diagram rendering failed: ${errorDetails?.message || 'Unknown error'}`);
  setLoading(false);
  };

  const handleDiagramRender = (renderedSvg, errorDetails) => {
    if (errorDetails) {
      handleDiagramError(errorDetails);
    } else {
      setSvg(renderedSvg);
      setDiagramError(null);
    }
  };

  const showDiagramFallback = () => {
    setShowRawDiagram(true);
  };

  const buildCurrentDiagram = async (schema, type = diagramType, langs = visibleLangs, overrides = {}) => {
    if (!schema) return '';
    const correlationId = `build-${Date.now()}`;
    const renderer = getRendererForType(type);
    const diagramOptions = {
      showFields,
      showMethods,
      showRelations,
      relationFilter,
      colorEdgesBySource,
      format: renderer,
      correlationId,
      ...overrides
    };
    return buildDiagram(schema, type, langs, diagramOptions);
  };

  const handlePromptAnalyze = async () => {
    if (!prompt.trim()) {
      setError('Prompt is required');
      return;
    }

  setError(null);
    setLoading(true);
    setDiagram('');
    setSvg('');
    setDiagramError(null);
    setShowRawDiagram(false);
    setIsPromptDiagram(false); // Prevent regeneration loop during initial generation

    try {
      const renderer = getRendererForType(diagramType);
      const result = await apiRequest('/uml-from-prompt', {
        method: 'POST',
        body: JSON.stringify({
          prompt: prompt.trim(),
          diagramType: diagramType,
          format: renderer
        })
      });

      // The response contains the diagram directly, not a schema
      if (result.diagram) {
        setDiagram(result.diagram);
        setLastPrompt(prompt.trim());
        setIsPromptDiagram(true);
      } else {
        throw new Error('No diagram returned from server');
      }
    } catch (err) {
  setError('An error occurred while generating the UML diagram.');
  setLoading(false);
    } finally {
      setLoading(false);
    }
  };

  const handleAnalyze = async () => {
    const validation = validateGitHubUrl(input);
    if (!validation.isValid) {
      setError(validation.error);
      return;
    }

  setError(null);
    setLoading(true);
    setDiagram('');
    setSvg('');
    setDiagramError(null);
    setShowRawDiagram(false);
    setIsPromptDiagram(false); // Disable prompt mode for GitHub analysis
    setLastPrompt(''); // Clear last prompt

    const retryFn = async () => {
      const result = await apiRequest('/analyze', {
        method: 'POST',
        body: JSON.stringify({ githubUrl: validation.url })
      });

      const schemaValidation = validateSchema(result.schema);
      if (!schemaValidation.isValid) {
        const error = schemaValidation.error;
        error.correlationId = `analyze-${Date.now()}`;
        throw error;
      }

      const schema = result.schema;
      setSchemaData({ ...schema, meta: result.meta });

      const availableLanguages = getAvailableLanguages(schema);
      const nextVis = {};
      for (const lang of availableLanguages) nextVis[lang] = true;
      setVisibleLangs(nextVis);

      const diagramSyntax = await buildCurrentDiagram(schema, diagramType, nextVis);
      setDiagram(diagramSyntax);
    };

    try {
      await retryFn();
    } catch (err) {
  setError('An error occurred during analysis.');
  setLoading(false);
    } finally {
      setLoading(false);
    }
  };

  // Remove handleFormatChange
  const handleDiagramTypeChange = async (type) => {
    setDiagramType(type);
    if (schemaData) {
      const diagramSyntax = await buildCurrentDiagram(schemaData, type);
      setDiagram(diagramSyntax);
    }
  };

  const handleToggleOption = async (updater, overrides = {}) => {
    updater();
    if (schemaData) {
      const diagramSyntax = await buildCurrentDiagram(schemaData, diagramType, visibleLangs, overrides);
      setDiagram(diagramSyntax);
    }
  };

  const handleCopy = async () => {
    try {
      await navigator.clipboard.writeText(diagram);
    } catch {
      // Ignore clipboard errors quietly
    }
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

  const languageEntries = useMemo(() => {
    if (!schemaData || diagramType !== 'class') return [];
    return Object.keys(schemaData)
      .filter(key => key !== 'relations' && Array.isArray(schemaData[key]) && schemaData[key].length > 0)
      .map(lang => ({
        lang,
        color: ({
          java: '#fde68a',
          python: '#bfdbfe',
          csharp: '#fca5a5',
          javascript: '#fcd34d',
          typescript: '#93c5fd',
          cpp: '#c7d2fe',
          c: '#a7f3d0'
        }[lang] || '#e5e7eb')
      }));
  }, [schemaData, diagramType]);



  return (
    <div className="min-h-screen flex flex-col items-center justify-center bg-gradient-to-br from-pink-100 via-blue-50 to-emerald-100 px-4 py-8">
      <div className="w-full max-w-3xl bg-white/80 rounded-2xl shadow-xl p-8 flex flex-col items-center">
        <h1 className="text-4xl font-extrabold mb-2 text-emerald-700 tracking-tight text-center">UML Designer AI</h1>
        <p className="mb-4 text-lg text-gray-600 text-center">
          Generate beautiful UML diagrams from code repositories or natural language prompts.
        </p>
        {/* Navigation hint */}
        <div className="mb-4 text-sm text-center">
          <span className="text-gray-600">💡 For natural language prompts, try our </span>
          <a href="/prompt-to-uml" className="text-emerald-600 hover:text-emerald-700 font-semibold underline">
            Prompt to UML page
          </a>
        </div>
        


        <div className="w-full flex flex-col gap-2 mb-4">
          <input
            className="border-2 border-emerald-200 focus:border-emerald-400 rounded-lg px-4 py-2 text-lg transition outline-none bg-white/90"
            placeholder="Paste GitHub repo URL (public)"
            value={input}
            onChange={e => setInput(e.target.value)}
            disabled={loading}
          />
          <div className="flex items-center gap-3 flex-wrap">
            <label className="text-sm text-gray-600">Diagram:</label>
            <select
              className="border rounded px-2 py-1 text-sm"
              value={diagramType}
              onChange={e => handleDiagramTypeChange(e.target.value)}
              disabled={loading}
            >
              {DIAGRAM_TYPES.map(type => (
                <option key={type} value={type}>
                  {DIAGRAM_LABELS[type] || type}
                </option>
              ))}
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
                <input
                  type="checkbox"
                  checked={showRelations}
                  onChange={e => handleToggleOption(() => setShowRelations(e.target.checked), { showRelations: e.target.checked })}
                />
                Show relations (extends/implements/uses)
              </label>
              <div className="flex flex-wrap gap-3 text-sm text-gray-600">
                <label className="flex items-center gap-2">
                  <input
                    type="checkbox"
                    checked={showFields}
                    onChange={e => handleToggleOption(() => setShowFields(e.target.checked), { showFields: e.target.checked })}
                  />
                  Fields
                </label>
                <label className="flex items-center gap-2">
                  <input
                    type="checkbox"
                    checked={showMethods}
                    onChange={e => handleToggleOption(() => setShowMethods(e.target.checked), { showMethods: e.target.checked })}
                  />
                  Methods
                </label>
                <label className="flex items-center gap-2">
                  Source:
                  <select
                    className="border rounded px-2 py-1"
                    value={relationFilter}
                    onChange={e => handleToggleOption(() => setRelationFilter(e.target.value), { relationFilter: e.target.value })}
                  >
                    <option value="all">All</option>
                    <option value="heuristic">Heuristic</option>
                    <option value="ai">AI</option>
                  </select>
                </label>
                <label className="flex items-center gap-2">
                  <input
                    type="checkbox"
                    checked={colorEdgesBySource}
                    onChange={e => handleToggleOption(() => setColorEdgesBySource(e.target.checked), { colorEdgesBySource: e.target.checked })}
                  />
                  Color AI edges
                </label>
              </div>
            </>
          )}
        </div>
        {error && (
          <div className="w-full bg-red-50 border border-red-200 rounded-lg p-4 mb-4">
            <div className="flex items-start gap-3">
              <div className="flex-shrink-0">
                <svg className="w-5 h-5 text-red-400" fill="currentColor" viewBox="0 0 20 20">
                  <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clipRule="evenodd" />
                </svg>
              </div>
              <div className="flex-1">
                <h3 className="text-sm font-medium text-red-800 mb-1">
                  {typeof error === 'object' && error.userMessage ? error.userMessage.title : 'Error'}
                </h3>
                <p className="text-sm text-red-700 mb-2">
                  {typeof error === 'object' && error.userMessage ? error.userMessage.message : error}
                </p>
                {typeof error === 'object' && error.correlationId && (
                  <p className="text-xs text-red-600">
                    Correlation ID: {error.correlationId}
                  </p>
                )}
                {typeof error === 'object' && error.userMessage && error.userMessage.suggestion && (
                  <div className="mt-2 p-2 bg-red-100 rounded text-xs text-red-800">
                    💡 {error.userMessage.suggestion}
                  </div>
                )}
              </div>
            </div>
          </div>
        )}
        {diagram && (
          <div className="w-full bg-white/90 rounded-lg p-4 mt-4 shadow-inner overflow-x-auto">
            <div className="flex justify-end gap-2 mb-2">
              <button onClick={handleCopy} className="text-sm px-3 py-1 rounded bg-emerald-100 text-emerald-700 hover:bg-emerald-200">
                Copy PlantUML
              </button>
              <button onClick={handleDownload} className="text-sm px-3 py-1 rounded bg-pink-100 text-pink-700 hover:bg-pink-200">
                Download SVG
              </button>
            </div>
            {diagramType === 'class' && (
              <div className="text-xs text-gray-500 mb-3">
                Legend: Base <span title="extends">&lt;|--</span> Derived, Interface <span title="implements">&lt;|..</span> Class, Whole <span title="composition">*--</span> Part, Whole <span title="aggregation">o--</span> Part, Uses <span title="uses">..&gt;</span>
                <span className="ml-2">[H=heuristic, AI=model]</span>
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
                    {schemaData.meta.commit && <span className="mr-3">commit: {schemaData.meta.commit.slice(0, 7)}</span>}
                    {typeof schemaData.meta.files_scanned === 'number' && <span>files: {schemaData.meta.files_scanned}</span>}
                  </div>
                )}
                {diagramType === 'class' &&
                  languageEntries.map(({ lang, color }) => (
                    <label key={lang} className="flex items-center gap-2">
                      <span className="inline-block w-3 h-3 rounded" style={{ backgroundColor: color }} />
                      <input
                        type="checkbox"
                        checked={!!visibleLangs[lang]}
                        onChange={async e => {
                          const next = { ...visibleLangs, [lang]: e.target.checked };
                          setVisibleLangs(next);
                          if (schemaData) {
                            const diagramSyntax = await buildCurrentDiagram(schemaData, diagramType, next);
                            setDiagram(diagramSyntax);
                          }
                        }}
                      />
                      {lang}
                    </label>
                  ))}
              </div>
            )}

            <PlantUMLDiagram
              uml={diagram}
              onRender={handleDiagramRender}
              onError={handleDiagramError}
              timeout={30000}
              format="svg"
              className="diagram-container"
              fallbackContent={
                <div className="text-gray-500 text-center py-8">
                  Enter a GitHub repository URL to generate UML diagrams
                </div>
              }
            />

            {showRawDiagram && diagram && (
              <div className="mt-4 p-4 bg-gray-100 rounded-lg">
                <div className="flex justify-between items-center mb-2">
                  <h3 className="font-semibold text-gray-700">
                    Raw Diagram Code (PlantUML)
                  </h3>
                  <button onClick={() => setShowRawDiagram(false)} className="text-gray-500 hover:text-gray-700">
                    ✕
                  </button>
                </div>
                <pre className="text-sm overflow-auto bg-white p-3 rounded border">{diagram}</pre>
                <div className="mt-2 text-xs text-gray-600">
                  Copy this code to render manually in any PlantUML-compatible editor
                </div>
              </div>
            )}

            {process.env.NODE_ENV === 'development' && diagramError && (
              <div className="mt-4 p-4 bg-red-50 border border-red-200 rounded-lg">
                <h3 className="font-semibold text-red-800 mb-2">Diagram Error Details</h3>
                <div className="text-sm text-red-700">
                  <p>
                    <strong>Message:</strong> {diagramError.message}
                  </p>
                  <p>
                    <strong>Context:</strong> {diagramError.context}
                  </p>
                  <p>
                    <strong>Attempts:</strong> {diagramError.attempts}
                  </p>
                  {diagramError.chart && (
                    <details className="mt-2">
                      <summary className="cursor-pointer font-semibold">Chart Data (truncated)</summary>
                      <pre className="mt-1 text-xs bg-red-100 p-2 rounded overflow-auto">{diagramError.chart}</pre>
                    </details>
                  )}
                </div>
              </div>
            )}
          </div>
        )}
      </div>
      <footer className="mt-8 text-gray-400 text-sm">
        Made with <span className="text-pink-400">♥</span> by G Karthik
      </footer>
    </div>
  );
}
