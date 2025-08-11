'use client';

import { useEffect, useRef, useId } from 'react';

export default function MermaidDiagram({ chart, onRender }) {
  const ref = useRef(null);
  const uid = useId().replace(/[:]/g, '_');

  useEffect(() => {
    let isMounted = true;

    async function render() {
      if (!chart || !ref.current) return;
      try {
        // Log the Mermaid chart string for debugging
        console.log('Rendering Mermaid chart string:', chart);
        const mermaid = (await import('mermaid')).default;
        mermaid.initialize({ startOnLoad: false });
        const { svg } = await mermaid.render(`mermaid_${uid}`, chart);
        if (isMounted && ref.current) {
          ref.current.innerHTML = svg;
          onRender && onRender(svg);
        }
      } catch (e) {
        console.error('Mermaid render error:', e, '\nChart string was:', chart);
        if (isMounted && ref.current) {
          ref.current.innerHTML = '<div style="color:red">Failed to render diagram.<br/>Check console for Mermaid source and error details.</div>';
          onRender && onRender('');
        }
      }
    }

    render();
    return () => {
      isMounted = false;
    };
  }, [chart, uid, onRender]);

  return <div ref={ref} />;
}
