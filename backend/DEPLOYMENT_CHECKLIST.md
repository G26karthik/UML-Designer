# UML Backend - Deployment Checklist

## 🚀 Pre-Deployment Checklist

### ✅ Code Preparation
- [ ] All tests passing locally (`npm test`)
- [ ] Code committed to main/production branch
- [ ] No sensitive data in repository
- [ ] Dependencies updated and secure
- [ ] Environment variables documented

### ✅ Configuration Files
- [ ] `package.json` has correct scripts
- [ ] `ecosystem.config.json` configured for PM2
- [ ] `render.yaml` configured (if using GitOps)
- [ ] `.env.render.example` completed
- [ ] Build and start scripts are executable

### ✅ Environment Variables Setup
```bash
# Essential Variables (Set in Render Dashboard)
NODE_ENV=production
PORT=10000
LOG_LEVEL=info

# Cache Configuration
CACHE_TTL_MS=1800000
DISK_CACHE_TTL_MS=86400000
MAX_CACHE_ENTRIES=1000

# Security & CORS
ALLOWED_ORIGINS=https://your-frontend.vercel.app
CORS_CREDENTIALS=false

# External Services
PYTHON_PARSER_URL=https://your-python-parser.onrender.com
```

## 🔧 Render Service Configuration

### Service Settings
- [ ] **Service Type**: Web Service
- [ ] **Environment**: Node
- [ ] **Build Command**: `npm run build`
- [ ] **Start Command**: `npm run render:start`
- [ ] **Health Check Path**: `/health`
- [ ] **Auto Deploy**: Enabled
- [ ] **Branch**: main (or your production branch)

### Performance Settings
- [ ] **Plan**: Starter or higher for production
- [ ] **Region**: Closest to your users
- [ ] **Disk**: 1GB minimum for cache
- [ ] **Scaling**: Configure based on expected load

## 🧪 Post-Deployment Verification

### Automatic Checks
```bash
# Run deployment verification
npm run verify-deployment

# Run health checks
npm run health-check
```

### Manual Verification
- [ ] Health endpoint responds: `GET /health`
- [ ] Metrics endpoint works: `GET /metrics`
- [ ] Health summary available: `GET /health/summary`
- [ ] System info accessible: `GET /system/info`
- [ ] Error handling works: `GET /nonexistent-endpoint` returns 404
- [ ] CORS headers present in responses

### Performance Verification
- [ ] Response times < 2 seconds average
- [ ] Memory usage stable
- [ ] No memory leaks after sustained load
- [ ] Cache hit rates improving over time
- [ ] PM2 process monitoring working

## 📊 Monitoring Setup

### Render Dashboard
- [ ] Service logs accessible
- [ ] Metrics showing green
- [ ] No deployment errors
- [ ] Health checks passing

### Application Monitoring
- [ ] Winston logs being written
- [ ] PM2 monitoring active
- [ ] Performance metrics collected
- [ ] Error rates within acceptable limits

### Alerting (Optional)
- [ ] Set up Render alerts for downtime
- [ ] Configure log monitoring
- [ ] Set up performance alerts

## 🔒 Security Checklist

### Environment Security
- [ ] Sensitive data in environment variables only
- [ ] CORS origins properly configured
- [ ] Rate limiting enabled
- [ ] Security headers configured

### Access Control
- [ ] Repository access limited
- [ ] Render account secured with 2FA
- [ ] Environment variables not logged
- [ ] No hardcoded secrets

## 🔄 CI/CD Pipeline

### Automatic Deployment
- [ ] GitHub integration configured
- [ ] Auto-deploy on push to main
- [ ] Build notifications working
- [ ] Rollback plan documented

### Testing Pipeline
```bash
# Tests run during build
npm test

# Post-deployment verification
npm run verify-deployment
```

## 📈 Scaling Considerations

### Current Configuration
- PM2 cluster mode enabled
- Auto-scaling: 1-3 instances
- Memory limit: 500MB per instance
- Disk cache: 1GB

### Scaling Triggers
- [ ] CPU usage > 80% sustained
- [ ] Memory usage > 400MB sustained
- [ ] Response times > 3 seconds
- [ ] Error rate > 5%

## 🚨 Troubleshooting Guide

### Common Issues
1. **Build Failures**
   - Check Node.js version compatibility
   - Verify all dependencies in package.json
   - Review build logs in Render

2. **Start Failures**
   - Verify environment variables
   - Check PORT configuration
   - Review PM2 logs

3. **Performance Issues**
   - Monitor memory usage
   - Check cache hit rates
   - Review slow query logs

4. **External Service Issues**
   - Verify Python parser URL
   - Check service connectivity
   - Review CORS configuration

### Emergency Procedures
- [ ] Rollback plan documented
- [ ] Emergency contacts identified
- [ ] Service restart procedure
- [ ] Log access procedures

## 📞 Support Resources

### Documentation
- [Render Documentation](https://render.com/docs)
- [PM2 Documentation](https://pm2.keymetrics.io/docs/)
- [Node.js Best Practices](https://nodejs.org/en/docs/guides/)

### Monitoring Commands
```bash
# Check service health
curl https://your-service.onrender.com/health

# View metrics
curl https://your-service.onrender.com/metrics

# Performance summary
curl https://your-service.onrender.com/health/summary
```

## ✅ Final Deployment Sign-off

- [ ] All checklist items completed
- [ ] Performance benchmarks met
- [ ] Security review passed
- [ ] Monitoring configured
- [ ] Documentation updated
- [ ] Team notified of deployment

**Deployment Date**: ___________
**Deployed By**: ___________
**Version**: ___________
**Service URL**: ___________