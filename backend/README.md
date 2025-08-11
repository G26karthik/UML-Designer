# Backend Service

🚀 **Express.js API Gateway & Caching Layer**

The backend serves as an intelligent proxy between the frontend and Python parser, providing caching, security, and performance optimizations for the UML Designer AI application.

## 🎯 Purpose & Architecture

### **Core Responsibilities**
- **API Gateway**: Proxy requests to the Python parser microservice
- **Performance Layer**: Multi-tier caching (in-memory + disk) for faster response times
- **Security Layer**: CORS configuration, request validation, and rate limiting
- **File Handling**: Support for GitHub URLs and ZIP file uploads
- **Resilience**: Timeout handling, error recovery, and graceful degradation

### **Technology Stack**
- **Runtime**: Node.js 18+ with Express.js framework
- **Caching**: In-memory LRU cache + file system persistence
- **Security**: CORS, compression, request size limits
- **File Processing**: Multipart upload handling with security validation

## 🔧 Features

### **Intelligent Caching System**
```
Request Flow:
GitHub URL → Cache Key Generation → Memory Check → Disk Check → Python Parser → Cache Storage → Response
```

**Cache Key Strategy**:
- **Format**: `{url}@{commit_hash}` or `{url}` if commit unavailable
- **TTL**: Configurable expiration for both memory and disk
- **Eviction**: LRU (Least Recently Used) policy for memory cache

### **Request Processing Pipeline**
1. **Input Validation**: URL format validation, file size checks
2. **Cache Lookup**: Check memory cache, then disk cache
3. **Proxy Request**: Forward to Python parser if cache miss
4. **Response Processing**: Validate response, update cache
5. **Client Response**: Return cached or fresh data

### **Security Features**
- **CORS Configuration**: Configurable allowed origins
- **Request Size Limits**: JSON and file upload limits
- **Timeout Protection**: Prevents hanging requests
- **Path Traversal Protection**: Safe file handling
- **Input Sanitization**: URL and file validation

## 📊 API Endpoints

### **POST /analyze**
Analyze a GitHub repository or uploaded ZIP file.

#### **GitHub Repository Analysis**
```bash
curl -X POST http://localhost:3001/analyze \
  -H "Content-Type: application/json" \
  -d '{"githubUrl": "https://github.com/username/repository"}'
```

**Request Body:**
```json
{
  "githubUrl": "https://github.com/username/repository"
}
```

#### **ZIP File Upload**
```bash
curl -X POST http://localhost:3001/analyze \
  -F "repoZip=@repository.zip"
```

**Response Format:**
```json
{
  "schema": {
    "python": [
      {
        "class": "ClassName",
        "fields": ["field1: type", "field2"],
        "methods": ["method1", "method2"]
      }
    ],
    "java": [...],
    "relations": [
      {
        "from": "BaseClass",
        "to": "DerivedClass",
        "type": "extends",
        "source": "heuristic"
      }
    ],
    "meta": {
      "commit": "abc123def456...",
      "files_scanned": 245,
      "cached": false,
      "cache_key": "github.com/user/repo@abc123"
    }
  }
}
```

### **GET /health**
Health check endpoint for monitoring and load balancers.

```bash
curl http://localhost:3001/health
```

**Response:**
```json
{
  "status": "healthy",
  "timestamp": "2025-01-15T10:30:00.000Z",
  "uptime": 86400,
  "cache": {
    "memory_entries": 45,
    "disk_entries": 123,
    "memory_size": "2.5MB",
    "disk_size": "15.2MB"
  }
}
```

## ⚙️ Configuration

### **Environment Variables**

| Variable | Default | Description |
|----------|---------|-------------|
| `PORT` | `3001` | Server port |
| `PYTHON_PARSER_URL` | `http://localhost:5000` | Python parser service URL |
| `ANALYZE_TIMEOUT_MS` | `120000` | Request timeout (2 minutes) |
| `JSON_LIMIT` | `5mb` | Max JSON request size |
| `UPLOAD_LIMIT_BYTES` | `52428800` | Max file upload size (50MB) |
| `CACHE_TTL_MS` | `300000` | Memory cache TTL (5 minutes) |
| `DISK_CACHE_TTL_MS` | `86400000` | Disk cache TTL (24 hours) |
| `MAX_CACHE_ENTRIES` | `200` | Max memory cache entries |
| `DISK_CACHE_DIR` | `./cache` | Disk cache directory |
| `ALLOWED_ORIGINS` | `*` | CORS allowed origins (comma-separated) |

### **Example Configuration**

#### **Development** (`.env`)
```bash
PORT=3001
PYTHON_PARSER_URL=http://localhost:5000
ANALYZE_TIMEOUT_MS=60000
CACHE_TTL_MS=300000
ALLOWED_ORIGINS=http://localhost:3000
NODE_ENV=development
```

#### **Production** (`.env.production`)
```bash
PORT=3001
PYTHON_PARSER_URL=http://python-parser:5000
ANALYZE_TIMEOUT_MS=180000
CACHE_TTL_MS=600000
DISK_CACHE_TTL_MS=86400000
MAX_CACHE_ENTRIES=500
ALLOWED_ORIGINS=https://yourdomain.com,https://app.yourdomain.com
DISK_CACHE_DIR=/var/cache/uml-designer
NODE_ENV=production
```

## 🚀 Deployment

### **Local Development**
```bash
# Install dependencies
npm install

# Start development server with hot reload
npm run dev

# Start production server
npm start

# Run tests
npm test

# Run tests with coverage
npm run test:coverage
```

### **Docker Deployment**
```dockerfile
FROM node:18-alpine

WORKDIR /app
COPY package*.json ./
RUN npm ci --only=production

COPY . .
EXPOSE 3001

USER node
CMD ["npm", "start"]
```

### **Production Considerations**

#### **Performance Tuning**
- **Memory Cache**: Increase `MAX_CACHE_ENTRIES` for high-traffic scenarios
- **Disk Cache**: Use fast storage (SSD) for `DISK_CACHE_DIR`
- **Timeouts**: Adjust `ANALYZE_TIMEOUT_MS` based on repository sizes
- **Concurrency**: Use PM2 or cluster mode for multi-core utilization

#### **Monitoring & Observability**
```javascript
// Example monitoring setup
const promClient = require('prom-client');

// Metrics to track
const httpDuration = new promClient.Histogram({
  name: 'http_request_duration_seconds',
  help: 'Duration of HTTP requests in seconds',
  labelNames: ['method', 'route', 'status']
});

const cacheHitRate = new promClient.Counter({
  name: 'cache_hits_total',
  help: 'Total cache hits',
  labelNames: ['cache_type']
});
```

#### **Security Hardening**
- Set `ALLOWED_ORIGINS` to specific domains in production
- Use HTTPS reverse proxy (nginx, CloudFlare)
- Implement rate limiting for public APIs
- Regular security updates and dependency scanning

## 🧪 Testing

### **Test Structure**
```
__tests__/
├── analyze.test.js     # Main API endpoint tests
├── cache.test.js       # Caching logic tests
├── health.test.js      # Health check tests
└── fixtures/           # Test data and mocks
```

### **Running Tests**
```bash
# Run all tests
npm test

# Run specific test file
npm test analyze.test.js

# Run tests with coverage
npm run test:coverage

# Run tests in watch mode
npm run test:watch
```

### **Test Coverage Targets**
- **Statements**: > 80%
- **Branches**: > 75%
- **Functions**: > 80%
- **Lines**: > 80%

## 🔍 Monitoring & Debugging

### **Health Checks**
The `/health` endpoint provides comprehensive system status:

```bash
# Check service health
curl http://localhost:3001/health | jq

# Monitor cache performance
watch -n 5 'curl -s http://localhost:3001/health | jq .cache'
```

### **Common Issues & Solutions**

#### **High Memory Usage**
```bash
# Check cache size
curl -s http://localhost:3001/health | jq .cache.memory_size

# Solutions:
# 1. Reduce MAX_CACHE_ENTRIES
# 2. Decrease CACHE_TTL_MS
# 3. Monitor for memory leaks
```

#### **Slow Response Times**
```bash
# Check if python-parser is responding
curl -X POST http://localhost:5000/analyze \
  -H "Content-Type: application/json" \
  -d '{"githubUrl": "https://github.com/octocat/Hello-World"}'

# Solutions:
# 1. Increase ANALYZE_TIMEOUT_MS
# 2. Check network connectivity
# 3. Scale python-parser instances
```

#### **Cache Miss Rate Issues**
```bash
# Monitor cache hit patterns
tail -f logs/app.log | grep "cache"

# Solutions:
# 1. Increase CACHE_TTL_MS
# 2. Check cache key generation logic
# 3. Verify disk cache persistence
```

## 🛠️ Development

### **Project Structure**
```
backend/
├── index.js            # Main application entry point
├── routes/             # API route handlers
│   ├── analyze.js      # Analysis endpoint logic
│   └── health.js       # Health check logic
├── middleware/         # Express middleware
│   ├── cache.js        # Caching middleware
│   ├── cors.js         # CORS configuration
│   └── validation.js   # Request validation
├── utils/              # Utility functions
│   ├── cache-manager.js # Cache implementation
│   └── file-utils.js   # File handling utilities
├── __tests__/          # Test suite
├── package.json        # Dependencies and scripts
└── README.md          # This file
```

### **Adding New Features**

#### **1. New API Endpoint**
```javascript
// routes/new-endpoint.js
const express = require('express');
const router = express.Router();

router.post('/new-endpoint', async (req, res) => {
  try {
    // Implementation
    res.json({ success: true });
  } catch (error) {
    res.status(500).json({ error: error.message });
  }
});

module.exports = router;
```

#### **2. New Middleware**
```javascript
// middleware/new-middleware.js
module.exports = (options = {}) => {
  return (req, res, next) => {
    // Middleware logic
    next();
  };
};
```

#### **3. Testing New Features**
```javascript
// __tests__/new-feature.test.js
const request = require('supertest');
const app = require('../index');

describe('New Feature', () => {
  test('should handle new endpoint', async () => {
    const response = await request(app)
      .post('/new-endpoint')
      .send({ data: 'test' });
    
    expect(response.status).toBe(200);
    expect(response.body.success).toBe(true);
  });
});
```

## 📈 Performance Optimization

### **Cache Strategy Tuning**
```javascript
// Optimal cache configuration for different scenarios

// High Traffic, Small Repositories
MAX_CACHE_ENTRIES=1000
CACHE_TTL_MS=1800000      // 30 minutes
DISK_CACHE_TTL_MS=604800000 // 7 days

// Low Traffic, Large Repositories  
MAX_CACHE_ENTRIES=100
CACHE_TTL_MS=3600000      // 1 hour
DISK_CACHE_TTL_MS=2592000000 // 30 days

// Development Environment
MAX_CACHE_ENTRIES=50
CACHE_TTL_MS=300000       // 5 minutes
DISK_CACHE_TTL_MS=86400000 // 1 day
```

### **Memory Management**
```javascript
// Monitor memory usage
process.on('warning', (warning) => {
  if (warning.name === 'MaxListenersExceededWarning') {
    console.warn('Memory warning:', warning);
  }
});

// Graceful memory cleanup
process.on('SIGTERM', () => {
  console.log('Cleaning up caches...');
  cacheManager.clear();
  process.exit(0);
});
```

## 🔄 Integration

### **Frontend Integration**
The backend is designed to work seamlessly with the Next.js frontend:

```javascript
// Frontend API call example
const analyzeRepository = async (githubUrl) => {
  const response = await fetch(`${BACKEND_URL}/analyze`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ githubUrl })
  });
  
  return response.json();
};
```

### **Python Parser Integration**
Communication with the Python parser is handled transparently:

```javascript
// Backend forwards requests to Python parser
const pythonParserResponse = await axios.post(
  `${PYTHON_PARSER_URL}/analyze`,
  requestData,
  { timeout: ANALYZE_TIMEOUT_MS }
);
```

---

**Made with ⚡ for fast, reliable UML generation**

*This backend service is designed for production-scale deployment with comprehensive caching, monitoring, and security features.*
