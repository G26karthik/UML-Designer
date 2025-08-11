import { useEffect, useState } from 'react';
import axios from 'axios';
import dynamic from 'next/dynamic';

const MermaidDiagram = dynamic(() => import('../components/MermaidDiagram'), { ssr: false });

export default function Home() {
  const [input, setInput] = useState('');
  const [diagram, setDiagram] = useState('');
  const [svg, setSvg] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [showRelations, setShowRelations] = useState(true);
  const [showFields, setShowFields] = useState(true);
  const [showMethods, setShowMethods] = useState(true);
  const [relationFilter, setRelationFilter] = useState('all'); // all|heuristic|ai
  const [schemaData, setSchemaData] = useState(null);
  const [visibleLangs, setVisibleLangs] = useState({});
  const [colorEdgesBySource, setColorEdgesBySource] = useState(false);

  const handleAnalyze = async () => {
    setLoading(true);
    setError('');
    setDiagram('');
    setSvg('');
    try {
  const base = process.env.NEXT_PUBLIC_BACKEND_URL || 'http://localhost:3001';
  const res = await axios.post(`${base}/analyze`, { githubUrl: input });
  const schema = res.data.schema || res.data;
      setSchemaData(schema);
  const langs = Object.keys(schema).filter(k => k !== 'relations' && Array.isArray(schema[k]) && schema[k].length > 0);
      const nextVis = {};
      for (const l of langs) nextVis[l] = true;
      setVisibleLangs(nextVis);
      setDiagram(jsonToMermaid(schema, nextVis));
    } catch (err) {
      setError('Analysis failed. ' + (err.response?.data?.error || err.message));
    }
    setLoading(false);
  };

  function jsonToMermaid(schema, languageVisibility = visibleLangs) {
    let out = 'classDiagram\n';
    let classFound = false;
    const classes = new Set();
    const alias = new Map(); // original -> safe id
    const byLangIds = {}; // lang -> Set(ids)
    const safe = (name) => {
      if (!name) return name;
      if (alias.has(name)) return alias.get(name);
      let s = String(name).replace(/[^A-Za-z0-9_]/g, '_');
      if (!/^[A-Za-z_]/.test(s)) s = `C_${s}`; // ensure leading letter/_ for Mermaid id safety
      alias.set(name, s);
      return s;
    };
  const label = (name) => `"${String(name).replace(/"/g, '\\"')}"`;

  const languages = Object.keys(schema).filter(k => k !== 'relations' && Array.isArray(schema[k]) && schema[k].length > 0);
    const relations = schema.relations || [];

    const addClass = (cls, lang) => {
      // Filter out invalid class names (e.g., with spaces, language suffixes)
      if (!cls.class || /\s/.test(cls.class) || /java$|python$|csharp$|cpp$|typescript$|javascript$|\.js$|\.py$|\.cs$|\.cpp$/i.test(cls.class)) return;
      classFound = true;
      const id = safe(cls.class);
      classes.add(cls.class);
      
      const fields = (cls.fields || []).filter(f => f && f.trim());
      const methods = (cls.methods || []).filter(m => m && m.trim());
      
      // Only add braces if there are fields or methods
      if ((showFields && fields.length > 0) || (showMethods && methods.length > 0)) {
        out += `class ${id} {\n`;
        if (showFields) for (const f of fields) out += `  ${f}\n`;
        if (showMethods) for (const m of methods) out += `  ${m}()\n`;
        out += '}\n';
      } else {
        // Empty class - no braces needed
        out += `class ${id}\n`;
      }
      
      if (id !== cls.class) out += `class ${id} as ${label(cls.class)}\n`;
      if (lang) {
        (byLangIds[lang] ||= new Set()).add(id);
      }
    };

    // Render classes for all languages in schema
    for (const lang of languages) {
      if (!languageVisibility[lang]) continue;
      for (const cls of schema[lang] || []) addClass(cls, lang);
    }

    // Ensure all relation endpoints have at least placeholder classes
    for (const r of relations) {
      const from = r.from || r.parent;
      const to = r.to || r.child;
      if (from && !classes.has(from)) {
        const id = safe(from);
        out += `class ${id}\n`;
        if (id !== from) out += `class ${id} as ${label(from)}\n`;
        classes.add(from);
      }
      if (to && !classes.has(to)) {
        const id = safe(to);
        out += `class ${id}\n`;
        if (id !== to) out += `class ${id} as ${label(to)}\n`;
        classes.add(to);
      }
    }

    // Map relation types to Mermaid edges
    const edge = (r) => {
  const t = (r.type || '').toLowerCase();
  const from = safe(r.from || r.parent);
  const to = safe(r.to || r.child);
      if (!from || !to) return '';
  if (from === to) return '';
      const label = r.source === 'ai' ? ' : AI' : (r.source === 'heuristic' ? ' : H' : '');
      let line;
      switch (t) {
        case 'extends':
          line = `${from} <|-- ${to}${label}`; break;
        case 'implements':
          line = `${from} <|.. ${to}${label}`; break;
        case 'composes':
        case 'composition':
          line = `${from} *-- ${to}${label}`; break;
        case 'aggregates':
        case 'aggregation':
          line = `${from} o-- ${to}${label}`; break;
        case 'uses':
        case 'depends':
        case 'dependency':
          line = `${from} ..> ${to}${label}`; break;
        case 'associates':
        case 'association':
          line = `${from} --> ${to}${label}`; break;
        default:
          line = `${from} ..> ${to}${label}`; break;
      }
      return line;
    };

    const filtered = (showRelations ? relations : []).filter(r => relationFilter === 'all' || (r.source || 'heuristic') === relationFilter);
    const edgeLines = [];
    const styleLines = [];
    for (const r of filtered) {
      const line = edge(r);
      if (!line) continue;
      const idx = edgeLines.length; // index in Mermaid link style order
      edgeLines.push(line);
      if (colorEdgesBySource && (r.source || 'heuristic') === 'ai') {
        styleLines.push(`linkStyle ${idx} stroke:#7c3aed,stroke-width:2px;`);
      }
    }
    if (edgeLines.length) {
      out += edgeLines.join('\n') + '\n';
      // Note: linkStyle not supported in this context, removing for now
      // if (styleLines.length) out += styleLines.join('\n') + '\n';
    }

    // Language styles (not used in Mermaid output, only for UI)
    const palette = {
      java: '#fde68a',
      python: '#bfdbfe',
      csharp: '#fca5a5',
      javascript: '#fcd34d',
      typescript: '#93c5fd',
      cpp: '#c7d2fe',
      c: '#a7f3d0'
    };

    // Remove any invalid Mermaid lines (e.g., 'class ... java;')
    out = out
      .split('\n')
      .filter(line =>
        !/class\s+\w+\s+java;/.test(line) &&
        !/class\s+\w+\s+java\s+fill:/.test(line) &&
        !/class\s+\w+\s+python;/.test(line) &&
        !/class\s+\w+\s+csharp;/.test(line) &&
        !/class\s+\w+\s+cpp;/.test(line) &&
        !/class\s+\w+\s+typescript;/.test(line) &&
        !/class\s+\w+\s+javascript;/.test(line) &&
        !/classA\s+java\s+fill:/.test(line) &&
        !/classA\s+python\s+fill:/.test(line) &&
        !/classA\s+csharp\s+fill:/.test(line) &&
        !/classA\s+cpp\s+fill:/.test(line) &&
        !/classA\s+typescript\s+fill:/.test(line) &&
        !/classA\s+javascript\s+fill:/.test(line)
      )
      .join('\n');

    if (!classFound && relations.length === 0) {
      return 'classDiagram\n  note "No supported classes found in the repository."';
    }
    return out;
  }

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
        <p className="mb-6 text-lg text-gray-600 text-center">Generate beautiful UML class diagrams from your code repositories using AI.</p>
        <div className="w-full flex flex-col gap-2 mb-4">
          <input
            className="border-2 border-emerald-200 focus:border-emerald-400 rounded-lg px-4 py-2 text-lg transition outline-none bg-white/90"
            placeholder="Paste GitHub repo URL (public)"
            value={input}
            onChange={e => setInput(e.target.value)}
            disabled={loading}
          />
          <button
            className="bg-gradient-to-r from-emerald-400 to-pink-400 text-white font-semibold px-6 py-2 rounded-lg shadow hover:from-emerald-500 hover:to-pink-500 transition disabled:opacity-50"
            onClick={handleAnalyze}
            disabled={loading || !input.trim()}
          >
            {loading ? 'Analyzing…' : 'Analyze'}
          </button>
          <label className="flex items-center gap-2 text-sm text-gray-600 select-none">
            <input type="checkbox" checked={showRelations} onChange={e => setShowRelations(e.target.checked)} />
            Show relations (extends/implements/uses)
          </label>
          <div className="flex flex-wrap gap-3 text-sm text-gray-600">
            <label className="flex items-center gap-2">
              <input type="checkbox" checked={showFields} onChange={e => setShowFields(e.target.checked)} /> Fields
            </label>
            <label className="flex items-center gap-2">
              <input type="checkbox" checked={showMethods} onChange={e => setShowMethods(e.target.checked)} /> Methods
            </label>
            <label className="flex items-center gap-2">
              Source:
              <select className="border rounded px-2 py-1" value={relationFilter} onChange={e => setRelationFilter(e.target.value)}>
                <option value="all">All</option>
                <option value="heuristic">Heuristic</option>
                <option value="ai">AI</option>
              </select>
            </label>
            <label className="flex items-center gap-2">
              <input type="checkbox" checked={colorEdgesBySource} onChange={e => setColorEdgesBySource(e.target.checked)} /> Color AI edges
            </label>
          </div>
        </div>
        {error && <div className="text-red-500 mb-2 text-center">{error}</div>}
        {diagram && (
          <div className="w-full bg-white/90 rounded-lg p-4 mt-4 shadow-inner overflow-x-auto">
            <div className="flex justify-end gap-2 mb-2">
              <button onClick={handleCopy} className="text-sm px-3 py-1 rounded bg-emerald-100 text-emerald-700 hover:bg-emerald-200">Copy Mermaid</button>
              <button onClick={handleDownload} className="text-sm px-3 py-1 rounded bg-pink-100 text-pink-700 hover:bg-pink-200">Download SVG</button>
            </div>
            <div className="text-xs text-gray-500 mb-3">
              Legend: Base <span title="extends">&lt;|--</span> Derived, Interface <span title="implements">&lt;|..</span> Class, Whole <span title="composition">*--</span> Part, Whole <span title="aggregation">o--</span> Part, Uses <span title="uses">..&gt;</span> <span className="ml-2">[H=heuristic, AI=model]</span>
            </div>
            {schemaData && (
              <div className="text-xs text-gray-600 mb-3 flex flex-wrap gap-3">
                {schemaData.meta && (
                  <div className="mr-4 opacity-80">
                    {schemaData.meta.commit && <span className="mr-3">commit: {schemaData.meta.commit.slice(0,7)}</span>}
                    {typeof schemaData.meta.files_scanned === 'number' && <span>files: {schemaData.meta.files_scanned}</span>}
                  </div>
                )}
                {Object.keys(schemaData).filter(k => k !== 'relations' && Array.isArray(schemaData[k]) && schemaData[k].length > 0).map(lang => (
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
                        setDiagram(jsonToMermaid(schemaData, next));
                      }}
                    /> {lang}
                  </label>
                ))}
              </div>
            )}
            <MermaidDiagram chart={diagram} onRender={setSvg} />
          </div>
        )}
      </div>
      <footer className="mt-8 text-gray-400 text-sm">Made with <span className="text-pink-400">♥</span> by G Karthik</footer>
    </div>
  );
}
