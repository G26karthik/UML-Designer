# Frontend Application

🎨 **Next.js React Application for UML Diagram Visualization**

The frontend provides an intuitive, responsive web interface for generating and viewing UML class diagrams from code repositories. Built with modern React patterns and optimized for performance.

## 🎯 Purpose & Architecture

### **Core Responsibilities**
- **User Interface**: Clean, intuitive design for repository input and diagram viewing
- **Diagram Rendering**: Client-side Mermaid.js integration for UML visualization
- **Interactive Controls**: Dynamic filtering, customization, and export options
- **State Management**: Efficient React state handling for complex diagram data
- **Performance**: Optimized rendering and responsive design

### **Technology Stack**
- **Framework**: Next.js 13+ with App Router
- **UI Library**: React 18+ with Hooks
- **Styling**: Tailwind CSS with custom design system
- **Diagram Rendering**: Mermaid.js (client-side only)
- **HTTP Client**: Axios for API communication
- **Build Tools**: Next.js built-in bundling and optimization

## 🎨 Features & Components

### **Core Components**

#### **MermaidDiagram Component**
```javascript
// Client-side rendering with error handling
import dynamic from 'next/dynamic';

const MermaidDiagram = dynamic(() => import('../components/MermaidDiagram'), { 
  ssr: false 
});

// Features:
// - Safe client-side rendering
// - Error boundaries and fallbacks
// - SVG export capabilities
// - Real-time diagram updates
```

#### **Main Application Interface**
- **Repository Input**: GitHub URL validation and input handling
- **Analysis Controls**: Fields, methods, and relationships toggles
- **Language Filters**: Per-language visibility and color coding
- **Export Options**: Copy Mermaid source and SVG download
- **Status Display**: Loading states, error messages, and metadata

### **Interactive Features**

#### **Dynamic Filtering System**
```javascript
// Real-time diagram updates based on user selections
const updateDiagram = () => {
  const filteredSchema = {
    ...schemaData,
    // Apply language visibility filters
    python: visibleLangs.python ? schemaData.python : [],
    java: visibleLangs.java ? schemaData.java : [],
    // Apply relationship filters
    relations: relations.filter(r => 
      relationFilter === 'all' || r.source === relationFilter
    )
  };
  
  setDiagram(jsonToMermaid(filteredSchema));
};
```

#### **Language Color Coding**
```javascript
// Consistent color palette across the application
const languageColors = {
  java: '#fde68a',      // Warm yellow
  python: '#bfdbfe',    // Light blue  
  csharp: '#fca5a5',    // Light red
  javascript: '#fcd34d', // Golden yellow
  typescript: '#93c5fd', // Blue
  cpp: '#c7d2fe',       // Purple-blue
  c: '#a7f3d0'          // Light green
};
```

## 🔄 Data Flow & State Management

### **Application State Structure**
```javascript
const AppState = {
  // Input & Analysis
  input: '',                    // GitHub URL input
  loading: false,              // Analysis in progress
  error: '',                   // Error messages
  
  // Schema Data
  schemaData: null,            // Raw analysis results
  diagram: '',                 // Generated Mermaid string
  svg: '',                     // Rendered SVG output
  
  // UI Controls
  showRelations: true,         // Show/hide relationships
  showFields: true,            // Show/hide class fields
  showMethods: true,           // Show/hide class methods
  relationFilter: 'all',       // Filter by source (all|heuristic|ai)
  visibleLangs: {},           // Per-language visibility
  colorEdgesBySource: false    // Color AI vs heuristic edges
};
```

### **Data Processing Pipeline**
```
User Input (GitHub URL)
    ↓ Form Submission
API Request to Backend (/analyze)
    ↓ Response Processing
Schema Validation & Storage
    ↓ Mermaid Generation
JSON to Mermaid Conversion
    ↓ Client Rendering
Mermaid.js SVG Generation
    ↓ User Interaction
Real-time Filtering & Updates
```

## 🎛️ User Interface Components

### **Main Application Layout**
```javascript
export default function Home() {
  return (
    <div className="min-h-screen bg-gradient-to-br from-pink-100 via-blue-50 to-emerald-100">
      <div className="max-w-3xl mx-auto bg-white/80 rounded-2xl shadow-xl p-8">
        {/* Header Section */}
        <Header />
        
        {/* Input Section */}
        <RepositoryInput 
          value={input}
          onChange={setInput}
          onSubmit={handleAnalyze}
          loading={loading}
        />
        
        {/* Controls Section */}
        <DiagramControls
          showRelations={showRelations}
          showFields={showFields}
          showMethods={showMethods}
          onToggleRelations={setShowRelations}
          onToggleFields={setShowFields}
          onToggleMethods={setShowMethods}
        />
        
        {/* Results Section */}
        <DiagramDisplay
          diagram={diagram}
          error={error}
          loading={loading}
          onRender={setSvg}
        />
        
        {/* Export Section */}
        <ExportControls
          diagram={diagram}
          svg={svg}
          onCopy={handleCopy}
          onDownload={handleDownload}
        />
      </div>
    </div>
  );
}
```

### **Component Breakdown**

#### **RepositoryInput Component**
- URL validation and formatting
- Loading state management
- Error handling and user feedback
- Accessibility features (ARIA labels, keyboard navigation)

#### **DiagramControls Component**
- Toggle switches for diagram elements
- Language filter checkboxes with color indicators
- Relationship source filtering (heuristic vs AI)
- Real-time diagram updates

#### **DiagramDisplay Component**
- Mermaid diagram rendering with error boundaries
- Responsive layout for different screen sizes
- Loading states and progress indicators
- Error messages with actionable guidance

#### **ExportControls Component**
- Copy Mermaid source to clipboard
- SVG download functionality
- Share and permalink options
- Metadata display (commit hash, files scanned)

## 🎨 Styling & Design System

### **Tailwind CSS Configuration**
```javascript
// tailwind.config.js
module.exports = {
  content: ['./pages/**/*.{js,ts,jsx,tsx}', './components/**/*.{js,ts,jsx,tsx}'],
  theme: {
    extend: {
      colors: {
        // Custom color palette
        'uml-primary': '#059669',    // Emerald green
        'uml-secondary': '#ec4899',  // Pink
        'uml-accent': '#3b82f6',     // Blue
        'uml-neutral': '#6b7280',    // Gray
      },
      fontFamily: {
        'display': ['Inter', 'system-ui', 'sans-serif'],
        'body': ['system-ui', 'sans-serif'],
      },
      animation: {
        'fade-in': 'fadeIn 0.5s ease-in-out',
        'slide-up': 'slideUp 0.3s ease-out',
      }
    }
  },
  plugins: [
    require('@tailwindcss/forms'),
    require('@tailwindcss/typography'),
  ]
};
```

### **Design Principles**
- **Accessibility First**: WCAG 2.1 AA compliance
- **Mobile Responsive**: Mobile-first design approach
- **Performance Optimized**: Minimal CSS bundle size
- **Consistent Spacing**: 8px grid system
- **Color Accessibility**: High contrast ratios

## 🔧 Configuration & Environment

### **Environment Variables**
```bash
# .env.local (Development)
NEXT_PUBLIC_BACKEND_URL=http://localhost:3001

# .env.production (Production)
NEXT_PUBLIC_BACKEND_URL=https://api.yourdomain.com
NEXT_PUBLIC_ANALYTICS_ID=your-analytics-id
NEXT_PUBLIC_SENTRY_DSN=your-sentry-dsn
```

### **Next.js Configuration**
```javascript
// next.config.js
/** @type {import('next').NextConfig} */
const nextConfig = {
  experimental: {
    appDir: true,
  },
  
  // Performance optimizations
  compress: true,
  poweredByHeader: false,
  
  // Image optimization
  images: {
    domains: ['github.com', 'avatars.githubusercontent.com'],
  },
  
  // Bundle analysis
  webpack: (config, { isServer }) => {
    if (!isServer) {
      config.resolve.fallback = {
        ...config.resolve.fallback,
        fs: false,
      };
    }
    return config;
  },
};

module.exports = nextConfig;
```

## 🚀 Development & Deployment

### **Local Development**
```bash
# Install dependencies
npm install

# Start development server with hot reload
npm run dev

# Build for production
npm run build

# Start production server
npm start

# Run linting
npm run lint

# Run tests
npm test
```

### **Development Workflow**
1. **Component Development**: Create/modify components in `/components`
2. **Page Development**: Update pages in `/pages` 
3. **Styling**: Use Tailwind classes, custom CSS for complex layouts
4. **Testing**: Write unit tests for components and integration tests
5. **Performance**: Monitor bundle size and rendering performance

### **Production Build Optimization**
```bash
# Analyze bundle size
npm run analyze

# Performance audit
npm run lighthouse

# Security audit
npm audit

# Type checking (if using TypeScript)
npm run type-check
```

### **Deployment Options**

#### **Vercel (Recommended)**
```bash
# Install Vercel CLI
npm i -g vercel

# Deploy to Vercel
vercel --prod
```

#### **Static Export**
```bash
# Build static export
npm run build && npm run export

# Deploy to any static hosting
# (Netlify, GitHub Pages, S3, etc.)
```

#### **Docker Deployment**
```dockerfile
FROM node:18-alpine

WORKDIR /app
COPY package*.json ./
RUN npm ci --only=production

COPY . .
RUN npm run build

EXPOSE 3000
CMD ["npm", "start"]
```

## 🧪 Testing Strategy

### **Test Structure**
```
__tests__/
├── components/         # Component unit tests
│   ├── MermaidDiagram.test.js
│   └── DiagramControls.test.js
├── pages/             # Page integration tests
│   └── index.test.js
├── utils/             # Utility function tests
│   └── mermaid-converter.test.js
└── fixtures/          # Test data and mocks
    └── sample-schemas.js
```

### **Testing Technologies**
- **Jest**: Test runner and assertion library
- **React Testing Library**: Component testing utilities
- **MSW**: API mocking for integration tests
- **Playwright**: End-to-end testing

### **Example Component Test**
```javascript
// __tests__/components/MermaidDiagram.test.js
import { render, screen } from '@testing-library/react';
import MermaidDiagram from '../../components/MermaidDiagram';

describe('MermaidDiagram', () => {
  test('renders diagram when valid chart provided', async () => {
    const validChart = 'classDiagram\nclass TestClass';
    
    render(<MermaidDiagram chart={validChart} />);
    
    // Wait for Mermaid to render
    await screen.findByRole('img', { hidden: true });
    
    expect(screen.queryByText('Failed to render diagram')).not.toBeInTheDocument();
  });
  
  test('shows error message for invalid chart', async () => {
    const invalidChart = 'invalid mermaid syntax';
    
    render(<MermaidDiagram chart={invalidChart} />);
    
    await screen.findByText(/Failed to render diagram/);
    
    expect(screen.getByText(/Check console for Mermaid source/)).toBeInTheDocument();
  });
});
```

## 🔍 Performance Optimization

### **Bundle Size Optimization**
```javascript
// Dynamic imports for large components
const MermaidDiagram = dynamic(() => import('../components/MermaidDiagram'), {
  ssr: false,
  loading: () => <DiagramSkeleton />
});

// Code splitting by route
const AdvancedSettings = lazy(() => import('../components/AdvancedSettings'));
```

### **Rendering Performance**
```javascript
// Memoized components for expensive renders
const MemoizedDiagram = React.memo(MermaidDiagram, (prevProps, nextProps) => {
  return prevProps.chart === nextProps.chart;
});

// Debounced state updates
const debouncedUpdateDiagram = useMemo(
  () => debounce(updateDiagram, 300),
  [schemaData, visibleLangs, showFields, showMethods]
);
```

### **User Experience Optimizations**
- **Loading States**: Skeleton screens and progress indicators
- **Error Boundaries**: Graceful error handling with recovery options
- **Responsive Design**: Optimized for mobile and desktop
- **Accessibility**: Screen reader support and keyboard navigation

## 🐛 Debugging & Troubleshooting

### **Common Issues**

#### **Mermaid Rendering Failures**
```javascript
// Debug Mermaid issues
console.log('Chart string:', chart);

// Common fixes:
// 1. Check for invalid class names
// 2. Verify relationship syntax
// 3. Ensure proper escaping of special characters
```

#### **State Management Issues**
```javascript
// Debug state updates
useEffect(() => {
  console.log('State changed:', { 
    visibleLangs, 
    showFields, 
    showMethods 
  });
}, [visibleLangs, showFields, showMethods]);
```

#### **API Communication Issues**
```javascript
// Debug API calls
const analyzeRepository = async (githubUrl) => {
  try {
    console.log('Analyzing:', githubUrl);
    const response = await axios.post('/analyze', { githubUrl });
    console.log('Response:', response.data);
    return response.data;
  } catch (error) {
    console.error('API Error:', error.response?.data || error.message);
    throw error;
  }
};
```

## 🔄 Integration Points

### **Backend API Integration**
```javascript
// API service layer
class UMLAnalysisService {
  constructor(baseURL) {
    this.api = axios.create({
      baseURL,
      timeout: 120000,
      headers: {
        'Content-Type': 'application/json',
      },
    });
  }
  
  async analyzeRepository(githubUrl) {
    const response = await this.api.post('/analyze', { githubUrl });
    return response.data;
  }
  
  async uploadRepository(file) {
    const formData = new FormData();
    formData.append('repoZip', file);
    
    const response = await this.api.post('/analyze', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    });
    
    return response.data;
  }
}
```

### **Mermaid.js Integration**
```javascript
// Safe Mermaid initialization
useEffect(() => {
  const initializeMermaid = async () => {
    if (typeof window !== 'undefined') {
      const mermaid = (await import('mermaid')).default;
      
      mermaid.initialize({
        startOnLoad: false,
        theme: 'default',
        securityLevel: 'strict',
        fontFamily: 'inherit',
      });
    }
  };
  
  initializeMermaid();
}, []);
```

---

**Made with 🎨 for beautiful UML visualization**

*This frontend application provides a modern, accessible, and performant interface for UML diagram generation and visualization.*
