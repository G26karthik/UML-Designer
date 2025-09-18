# UML Backend - Render Deployment Guide

## 🚀 Quick Deployment Steps

### 1. Prerequisites
- GitHub repository with your UML backend code
- Render account (free tier available)
- Python parser service deployed separately (if needed)

### 2. Render Service Configuration

#### A. Create New Web Service
1. Go to [Render Dashboard](https://dashboard.render.com)
2. Click "New" → "Web Service" 
3. Connect your GitHub repository
4. Select the `backend` folder as root directory

#### B. Service Settings
- **Name**: `uml-backend` (or your preferred name)
- **Environment**: `Node`
- **Region**: Choose closest to your users
- **Branch**: `main` (or your production branch)
- **Root Directory**: `backend` (if backend is in subdirectory)

#### C. Build & Deploy Configuration
- **Build Command**: `npm run build`
- **Start Command**: `npm run render:start`
- **Node Version**: `18.x` or higher

### 3. Environment Variables Setup

Copy the following environment variables to your Render service:

```bash
# Essential Variables
NODE_ENV=production
PORT=10000
LOG_LEVEL=info

# Cache Configuration
CACHE_TTL_MS=1800000
DISK_CACHE_TTL_MS=86400000
MAX_CACHE_ENTRIES=1000

# Request Limits
ANALYZE_TIMEOUT_MS=300000
JSON_LIMIT=20mb
UPLOAD_LIMIT_BYTES=52428800

# CORS Setup (Replace with your frontend domains)
ALLOWED_ORIGINS=https://your-frontend.vercel.app,https://your-domain.com
CORS_CREDENTIALS=false

# Rate Limiting
RATE_LIMIT_WINDOW_MS=900000
RATE_LIMIT_MAX_REQUESTS=100

# External Services (Update with your Python service URL)
PYTHON_PARSER_URL=https://your-python-parser.render.com
```

### 4. Advanced Configuration

#### A. Health Checks
Render will automatically health check using: `GET /health`

#### B. Monitoring Endpoints
- Health Summary: `GET /health/summary`
- Metrics: `GET /metrics`
- System Info: `GET /system/info`

#### C. Process Management
The service uses PM2 for:
- Auto-restart on crashes
- Memory limit management (500MB)
- Cluster mode for better performance
- Centralized logging

### 5. Deployment Process

#### Automatic Deployment
1. Push code to your connected GitHub branch
2. Render automatically triggers build and deploy
3. Monitor deployment in Render dashboard

#### Manual Deployment
1. Go to your service in Render dashboard
2. Click "Manual Deploy" → "Deploy latest commit"

### 6. Post-Deployment Verification

#### A. Health Check
```bash
curl https://your-service.onrender.com/health
```

Expected response:
```json
{
  "status": "healthy",
  "timestamp": "2025-09-14T12:00:00.000Z",
  "version": "1.0.0",
  "services": {
    "pythonParser": {
      "status": "healthy"
    }
  }
}
```

#### B. Test Endpoints
```bash
# Test basic functionality
curl https://your-service.onrender.com/test

# Check metrics
curl https://your-service.onrender.com/metrics

# Health summary
curl https://your-service.onrender.com/health/summary
```

### 7. Performance Optimization

#### A. Render Service Plan
- **Free Tier**: Suitable for development/testing
- **Starter Plan ($7/month)**: Better for production
- **Standard Plan ($25/month)**: High traffic applications

#### B. Resource Monitoring
Monitor these metrics in Render dashboard:
- CPU usage
- Memory consumption
- Response times
- Error rates

### 8. Logging & Debugging

#### A. View Logs
```bash
# In Render dashboard
Service → Logs → View live logs

# Or via Render CLI
render logs --service=uml-backend --tail
```

#### B. PM2 Monitoring
The service includes PM2 monitoring for:
- Process status
- Memory usage
- CPU usage
- Restart count

### 9. Scaling Configuration

#### A. Horizontal Scaling
```json
// ecosystem.config.json
{
  "instances": "max", // Uses all available CPU cores
  "exec_mode": "cluster"
}
```

#### B. Vertical Scaling
Upgrade Render service plan for more resources

### 10. Security Considerations

#### A. Environment Variables
- Never commit `.env` files
- Use Render's environment variable management
- Rotate sensitive credentials regularly

#### B. CORS Configuration
```bash
# Update ALLOWED_ORIGINS with your actual domains
ALLOWED_ORIGINS=https://yourdomain.com,https://app.yourdomain.com
```

#### C. Rate Limiting
Current configuration allows:
- 100 requests per 15 minutes per IP
- Adjustable via environment variables

### 11. Troubleshooting

#### Common Issues:

**Build Failures**
- Check Node.js version compatibility
- Verify all dependencies are in package.json
- Review build logs in Render dashboard

**Service Won't Start**
- Check environment variables
- Verify PORT configuration
- Review startup logs

**External Service Connectivity**
- Verify PYTHON_PARSER_URL is correct
- Check if Python service is running
- Review CORS configuration

**Performance Issues**
- Monitor memory usage (500MB limit)
- Check PM2 restart logs
- Consider upgrading service plan

### 12. Continuous Integration

#### A. Automated Testing
The build process includes:
```bash
npm test  # Runs all test suites
```

#### B. Zero-Downtime Deployment
Render provides zero-downtime deployments:
- Health checks during deployment
- Automatic rollback on failure
- Blue-green deployment strategy

### 13. Backup & Recovery

#### A. Data Persistence
- Logs are rotated and compressed
- Cache is rebuilt automatically
- No persistent database (stateless design)

#### B. Service Recovery
- Automatic restart on crashes
- Health check monitoring
- Manual restart via dashboard

---

## 🔗 Useful Links

- [Render Documentation](https://render.com/docs)
- [PM2 Documentation](https://pm2.keymetrics.io/docs/)
- [Node.js on Render](https://render.com/docs/node-version)
- [Environment Variables](https://render.com/docs/environment-variables)

## 📞 Support

For deployment issues:
1. Check Render dashboard logs
2. Review this deployment guide
3. Check GitHub repository issues
4. Contact Render support for platform issues