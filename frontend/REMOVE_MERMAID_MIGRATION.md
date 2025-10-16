# Remove Mermaid.js and Use PlantUML for All Diagrams

## Migration Steps

1. All diagram rendering is now routed through PlantUML for all diagram types (class, sequence, activity, state, usecase, component, communication, deployment).
2. All MermaidDiagram components, utilities, and Mermaid-specific code are removed.
3. Mermaid is removed from package.json and uninstalled.
4. All tests, documentation, and configs referencing Mermaid are cleaned up.
5. All diagram generation and rendering is routed through PlantUML only.

## Files/Dirs to Remove
- frontend/components/MermaidDiagram.js
- frontend/utils/otherDiagramBuilders.js (if only used for Mermaid)
- frontend/utils/classDiagramBuilder.js (if only used for Mermaid)
- frontend/utils/diagramUtils.js (if only used for Mermaid)
- frontend/utils/constants.js (remove Mermaid-specific constants)
- All Mermaid references in README.md, tests, and docs
- Remove Mermaid from frontend/package.json

## Next Steps
- Run `npm uninstall mermaid` in frontend directory
- Test all diagram types in the UI to confirm PlantUML is used everywhere
