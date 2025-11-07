# 🚀 CompliancePro360 - Docker SaaS Platform

Production-ready, multi-tenant SaaS compliance management system with AI automation, background task processing, and license-based billing.

---

## ⚡ Quick Start (5 Minutes)

### Windows
```powershell
cd E:\Projects\Dump\CompliancePro360
copy .env.example .env
notepad .env    # IMPORTANT: Update all passwords and API keys!
.\deploy.bat    # Note: Use .\ prefix in PowerShell
```

### Linux/Mac
```bash
cd /path/to/CompliancePro360
cp .env.example .env
nano .env       # IMPORTANT: Update all passwords and API keys!
chmod +x deploy.sh
./deploy.sh
```

### Access Your Application
- 🌐 **Main Application**: https://localhost
- 📚 **API Documentation**: https://localhost/api/docs  
- 🌸 **Flower Dashboard**: https://localhost/flower/
- 🔧 **Direct API**: http://localhost:8000
- 🎨 **Direct Frontend**: http://localhost:5000

---

## 🏗️ System Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    NGINX (Port 80/443)                  │
│          SSL, Load Balancing, Rate Limiting             │
└─────────────┬──────────────────────┬────────────────────┘
              │                      │
      ┌───────▼────────┐    ┌───────▼────────┐
      │   Frontend     │    │   API Backend  │
      │  Flask:5000    │    │ FastAPI:8000   │
      └───────┬────────┘    └───────┬────────┘
              │                     │
              └──────────┬──────────┘
                         │
        ┌────────────────┼────────────────┐
        │                │                │
   ┌────▼────┐     ┌────▼────┐     ┌────▼────┐
   │PostgreSQL│     │  Redis  │     │ Celery  │
   │  :5432  │     │  :6379  │     │ Workers │
   └─────────┘     └─────────┘     └─────────┘
```

**Services:**
- **NGINX**: Reverse proxy, SSL/TLS, rate limiting, static files
- **Frontend**: Flask web application (Python)
- **API**: FastAPI backend with OpenAPI docs
- **PostgreSQL**: Primary relational database
- **Redis**: Cache & message broker
- **Celery Workers**: Background task processing
- **Celery Beat**: Scheduled task automation
- **Flower**: Real-time Celery monitoring

---

## 📋 Prerequisites

- Docker Desktop 20.10+ (Windows/Mac) or Docker Engine (Linux)
- Docker Compose 2.0+
- 4GB+ RAM available
- 20GB+ disk space
- Domain name (for production SSL)

---

## 🔧 Configuration

### 1. Copy Environment Template
```bash
cp .env.example .env
```

### 2. Edit Critical Variables

**⚠️ MUST CHANGE BEFORE DEPLOYMENT:**

```env
# Application Secrets (Generate with: openssl rand -hex 32)
SECRET_KEY=your-super-secret-key-change-this-now
JWT_SECRET_KEY=your-jwt-secret-key-change-this-now

# Database (Use strong password)
POSTGRES_PASSWORD=YourSecurePasswordHere123!
DATABASE_URL=postgresql://postgres:YourSecurePasswordHere123!@postgres:5432/compliancepro360

# Redis (Use strong password)
REDIS_PASSWORD=YourSecureRedisPassword123!
REDIS_URL=redis://:YourSecureRedisPassword123!@redis:6379/0

# Email Service (SendGrid)
SENDGRID_API_KEY=SG.your-sendgrid-api-key-here
EMAIL_FROM=noreply@yourdomain.com

# SMS Service (Twilio)
TWILIO_ACCOUNT_SID=ACxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
TWILIO_AUTH_TOKEN=your-twilio-auth-token
TWILIO_PHONE_NUMBER=+1234567890

# AI Services
OPENAI_API_KEY=sk-your-openai-api-key
ANTHROPIC_API_KEY=sk-ant-your-anthropic-key

# Payment Gateway (Razorpay)
RAZORPAY_KEY_ID=rzp_live_xxxxxxxxxx
RAZORPAY_KEY_SECRET=your-razorpay-secret

# Monitoring (Sentry)
SENTRY_DSN=https://your-sentry-dsn@sentry.io/project

# Flower Dashboard
FLOWER_USER=admin
FLOWER_PASSWORD=ChangeThisSecurePassword123!
```

### 3. Generate Strong Secrets
```bash
# Linux/Mac
openssl rand -hex 32

# Windows (PowerShell)
[System.Convert]::ToBase64String((1..32 | ForEach-Object { Get-Random -Maximum 256 }))
```

---

## 🚀 Deployment

### Automated Deployment

**Windows (PowerShell):**
```powershell
.\deploy.bat
```

**Linux/Mac:**
```bash
chmod +x deploy.sh
./deploy.sh
```

### Manual Deployment

```bash
# 1. Create directories
mkdir -p logs uploads backups nginx/ssl

# 2. Generate SSL certificates (development only)
openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
  -keyout nginx/ssl/key.pem \
  -out nginx/ssl/cert.pem \
  -subj "/C=IN/ST=State/L=City/O=CompliancePro360/CN=localhost"

# 3. Build Docker images
docker-compose build

# 4. Start all services
docker-compose up -d

# 5. Check status
docker-compose ps

# 6. Initialize database
docker-compose exec api alembic upgrade head

# 7. (Optional) Create test users
docker-compose exec api python seed_test_users.py
```

---

## 🛠️ Daily Operations

### View Logs
```bash
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f api
docker-compose logs -f frontend
docker-compose logs -f celery_worker
docker-compose logs -f postgres

# Last 100 lines
docker-compose logs --tail=100 api
```

### Check Service Status
```bash
docker-compose ps
docker stats
```

### Restart Services
```bash
# Restart all
docker-compose restart

# Restart specific service
docker-compose restart api
docker-compose restart nginx
```

### Stop Services
```bash
# Stop without removing
docker-compose stop

# Stop and remove containers
docker-compose down

# Stop and remove EVERYTHING including data (⚠️ CAUTION!)
docker-compose down -v
```

### Scale Services
```bash
# Scale API instances
docker-compose up -d --scale api=3

# Scale Celery workers
docker-compose up -d --scale celery_worker=5
```

### Execute Commands in Containers
```bash
# Python shell in API
docker-compose exec api python

# Database shell
docker-compose exec postgres psql -U postgres compliancepro360

# Redis CLI
docker-compose exec redis redis-cli -a YourRedisPassword

# Check API health
curl http://localhost:8000/health
```

---

## 🧪 Development Mode

Enable hot-reload and verbose logging:

```bash
# Use development override
docker-compose -f docker-compose.yml -f docker-compose.dev.yml up

# Or set in .env
APP_ENV=development
```

**Development Features:**
- ✅ Code hot-reload (automatic restart on file changes)
- ✅ Detailed error messages and stack traces
- ✅ Direct service access (bypasses NGINX)
- ✅ Verbose logging
- ✅ Database and Redis exposed on localhost

---

## 💾 Backup & Restore

### Manual Database Backup

**Linux/Mac:**
```bash
docker-compose exec postgres pg_dump -U postgres compliancepro360 > backup_$(date +%Y%m%d_%H%M%S).sql
gzip backup_*.sql
```

**Windows (PowerShell):**
```powershell
docker-compose exec postgres pg_dump -U postgres compliancepro360 > backup_$(Get-Date -Format 'yyyyMMdd_HHmmss').sql
```

### Restore Database
```bash
# Linux/Mac
cat backup.sql | docker-compose exec -T postgres psql -U postgres compliancepro360

# Windows
Get-Content backup.sql | docker-compose exec -T postgres psql -U postgres compliancepro360
```

### Automated Backups

**Linux/Mac (Crontab):**
```bash
# Edit crontab
crontab -e

# Add daily backup at 2 AM
0 2 * * * cd /path/to/CompliancePro360 && ./scripts/backup.sh
```

**Windows (Task Scheduler):**
```powershell
# Create scheduled task for daily backup
$action = New-ScheduledTaskAction -Execute "PowerShell.exe" -Argument "-File C:\path\to\backup.ps1"
$trigger = New-ScheduledTaskTrigger -Daily -At 2am
Register-ScheduledTask -TaskName "CompliancePro360Backup" -Action $action -Trigger $trigger
```

### Backup Uploads Directory
```bash
tar -czf uploads_backup_$(date +%Y%m%d).tar.gz uploads/
```

---

## 📊 Monitoring & Health Checks

### Service Health
```bash
# API health endpoint
curl http://localhost:8000/health

# NGINX health endpoint
curl http://localhost/health

# Container health status
docker-compose ps
```

### Flower Dashboard (Celery Monitoring)
Access at: **https://localhost/flower/**

- Real-time task monitoring
- Worker status and statistics
- Task history and results
- Failed task inspection
- Login: Check `FLOWER_USER` and `FLOWER_PASSWORD` in `.env`

### Resource Usage
```bash
# Real-time container stats
docker stats

# Disk usage
docker system df

# Container processes
docker-compose top
```

### Database Monitoring
```bash
# Database size
docker-compose exec postgres psql -U postgres compliancepro360 -c \
  "SELECT pg_size_pretty(pg_database_size('compliancepro360'));"

# Active connections
docker-compose exec postgres psql -U postgres -c \
  "SELECT count(*) FROM pg_stat_activity;"

# Table sizes
docker-compose exec postgres psql -U postgres compliancepro360 -c \
  "SELECT schemaname, tablename, pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) 
   FROM pg_tables ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC LIMIT 10;"
```

---

## 🐛 Troubleshooting

### Port Already in Use

**Windows:**
```powershell
netstat -ano | findstr :80
netstat -ano | findstr :443
netstat -ano | findstr :5432
```

**Linux/Mac:**
```bash
lsof -i :80
lsof -i :443
sudo netstat -tulpn | grep LISTEN
```

**Solution:** Change ports in `.env`
```env
HTTP_PORT=8080
HTTPS_PORT=8443
POSTGRES_PORT=5433
```

### Services Won't Start

```bash
# Check Docker daemon
docker info

# Check logs for errors
docker-compose logs

# Remove and recreate
docker-compose down -v
docker-compose up -d

# Rebuild images
docker-compose build --no-cache
docker-compose up -d
```

### Database Connection Failed

```bash
# Wait for database to be ready
docker-compose exec postgres pg_isready -U postgres

# Check database logs
docker-compose logs postgres

# Restart database
docker-compose restart postgres

# Reset database (⚠️ DELETES ALL DATA!)
docker-compose down -v
docker volume rm compliancepro360_postgres_data
docker-compose up -d
```

### Redis Connection Issues

```bash
# Test Redis connection
docker-compose exec redis redis-cli -a YourRedisPassword ping

# Check Redis logs
docker-compose logs redis

# Restart Redis
docker-compose restart redis
```

### SSL Certificate Errors

**Development (Self-Signed Certificate):**
- Browser will show security warning
- Click "Advanced" → "Proceed to localhost (unsafe)"
- This is NORMAL for development

**Production (Let's Encrypt):**
```bash
# Install certbot
sudo apt install certbot

# Get certificate
sudo certbot certonly --standalone -d yourdomain.com -d www.yourdomain.com

# Copy certificates
sudo cp /etc/letsencrypt/live/yourdomain.com/fullchain.pem nginx/ssl/cert.pem
sudo cp /etc/letsencrypt/live/yourdomain.com/privkey.pem nginx/ssl/key.pem

# Restart NGINX
docker-compose restart nginx
```

### Container Keeps Restarting

```bash
# Check container logs
docker-compose logs <service-name>

# Inspect container
docker inspect compliancepro_api

# Check resource limits
docker stats

# Check disk space
df -h
docker system df
```

### API Returns 502 Bad Gateway

```bash
# Check API container status
docker-compose ps api

# Check API logs
docker-compose logs api

# Restart API
docker-compose restart api

# Rebuild API
docker-compose up -d --build api
```

---

## 🌐 Production Deployment

### Pre-Deployment Checklist

- [ ] Changed **ALL** default passwords in `.env`
- [ ] Generated strong secrets (`openssl rand -hex 32`)
- [ ] Configured real domain and DNS (A record pointing to server IP)
- [ ] Obtained SSL certificates (Let's Encrypt recommended)
- [ ] Set up email service (SendGrid API key)
- [ ] Configured SMS service (Twilio credentials)
- [ ] Added AI API keys (OpenAI, Anthropic)
- [ ] Configured payment gateway (Razorpay keys)
- [ ] Set up error monitoring (Sentry DSN)
- [ ] Configured automated backups (S3 credentials)
- [ ] Set up firewall (only expose ports 80, 443)
- [ ] Updated CORS_ORIGINS for your domain
- [ ] Tested all critical features
- [ ] Set up monitoring and alerting
- [ ] Configured backup retention policy

### Server Setup (Ubuntu/Debian)

```bash
# 1. Update system
sudo apt update && sudo apt upgrade -y

# 2. Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo usermod -aG docker $USER
newgrp docker

# 3. Install Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# 4. Clone/upload your application
git clone https://github.com/yourusername/CompliancePro360.git
cd CompliancePro360

# 5. Configure environment
cp .env.example .env
nano .env  # Update with production values

# 6. Get SSL certificates (Let's Encrypt)
sudo apt install certbot
sudo certbot certonly --standalone -d yourdomain.com -d www.yourdomain.com
sudo cp /etc/letsencrypt/live/yourdomain.com/fullchain.pem nginx/ssl/cert.pem
sudo cp /etc/letsencrypt/live/yourdomain.com/privkey.pem nginx/ssl/key.pem
sudo chmod 644 nginx/ssl/*.pem

# 7. Deploy application
./deploy.sh

# 8. Configure firewall
sudo ufw allow 22/tcp   # SSH
sudo ufw allow 80/tcp   # HTTP
sudo ufw allow 443/tcp  # HTTPS
sudo ufw enable

# 9. Set up automated backups
crontab -e
# Add: 0 2 * * * cd /path/to/CompliancePro360 && ./scripts/backup.sh

# 10. Set up SSL auto-renewal
sudo certbot renew --dry-run
```

### Domain Configuration

1. **DNS Setup:**
   - Add A record: `yourdomain.com` → Server IP
   - Add A record: `www.yourdomain.com` → Server IP

2. **Update `.env`:**
   ```env
   DOMAIN_NAME=yourdomain.com
   CORS_ORIGINS=https://yourdomain.com,https://www.yourdomain.com
   ALLOWED_HOSTS=yourdomain.com,www.yourdomain.com
   ```

3. **Update `nginx/nginx.conf`:**
   Replace `server_name _;` with `server_name yourdomain.com www.yourdomain.com;`

4. **Restart NGINX:**
   ```bash
   docker-compose restart nginx
   ```

### Scaling for Production

**Horizontal Scaling:**
```bash
# Multiple API instances
docker-compose up -d --scale api=3

# Multiple Celery workers
docker-compose up -d --scale celery_worker=5
```

**Use Managed Services:**
- **Database**: AWS RDS, DigitalOcean Managed Database
- **Redis**: AWS ElastiCache, Redis Cloud
- **Storage**: AWS S3, DigitalOcean Spaces
- **CDN**: CloudFlare, AWS CloudFront
- **Monitoring**: Sentry, DataDog, New Relic

### CI/CD Pipeline (GitHub Actions Example)

```yaml
# .github/workflows/deploy.yml
name: Deploy to Production
on:
  push:
    branches: [main]

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      
      - name: Deploy to server
        uses: appleboy/ssh-action@master
        with:
          host: ${{ secrets.SERVER_IP }}
          username: ${{ secrets.SERVER_USER }}
          key: ${{ secrets.SSH_PRIVATE_KEY }}
          script: |
            cd /path/to/CompliancePro360
            git pull
            docker-compose down
            docker-compose build
            docker-compose up -d
            docker-compose exec -T api alembic upgrade head
```

---

## 🔒 Security Best Practices

### Critical Security Measures

1. **Never commit `.env` file** (already in `.gitignore`)
2. **Use strong passwords** (minimum 32 characters)
3. **Generate unique secrets** (`openssl rand -hex 32`)
4. **Enable HTTPS** (Let's Encrypt certificates)
5. **Firewall configuration** (only ports 80, 443 exposed)
6. **Regular updates** (Docker images, dependencies)
7. **Automated backups** (daily, with retention policy)
8. **Error monitoring** (Sentry integration)
9. **Rate limiting** (configured in NGINX)
10. **Access control** (restrict admin panels)
11. **CORS restrictions** (only trusted domains)
12. **Database security** (never expose PostgreSQL publicly)
13. **Redis authentication** (password protected)
14. **Flower authentication** (basic auth enabled)

### Generate Secure Passwords

```bash
# Linux/Mac
openssl rand -base64 32

# Python
python -c "import secrets; print(secrets.token_urlsafe(32))"

# PowerShell
[System.Convert]::ToBase64String((1..32 | ForEach-Object { Get-Random -Maximum 256 }))
```

---

## 📁 Project Structure

```
CompliancePro360/
├── app/                          # FastAPI backend
│   ├── main.py                   # API entry point
│   ├── models/                   # SQLAlchemy models
│   ├── routers/                  # API endpoints
│   ├── services/                 # Business logic
│   ├── tasks/                    # Celery tasks
│   └── db/                       # Database configuration
├── templates/                    # Flask Jinja2 templates
├── static/                       # Static files (CSS, JS, images)
├── nginx/                        # NGINX reverse proxy
│   ├── nginx.conf               # Main configuration
│   └── ssl/                     # SSL certificates
├── scripts/                      # Utility scripts
│   └── backup.sh                # Database backup automation
├── logs/                         # Application logs
├── uploads/                      # User uploaded files
├── backups/                      # Database backups
├── docker-compose.yml            # Production Docker config
├── docker-compose.dev.yml        # Development overrides
├── Dockerfile                    # Application image
├── app_production.py             # Flask frontend server
├── requirements.txt              # Python dependencies
├── .env.example                  # Environment template
├── .gitignore                    # Git ignore rules
├── deploy.sh                     # Linux deployment script
├── deploy.bat                    # Windows deployment script
└── README.md                     # This file
```

---

## 🎯 Features

### Core Functionality
- ✅ **Multi-Tenancy**: License-based user isolation
- ✅ **License Management**: Trial, Starter, Professional, Enterprise plans
- ✅ **AI Automation**: OpenAI & Anthropic integration
- ✅ **Web Scraping**: Selenium-based compliance data collection
- ✅ **Task Scheduling**: Celery Beat for automated workflows
- ✅ **Background Processing**: Async task execution with Celery
- ✅ **Real-time Monitoring**: Flower dashboard for task inspection

### Communication
- ✅ **Email Notifications**: SendGrid integration
- ✅ **SMS Alerts**: Twilio integration
- ✅ **WhatsApp Notifications**: Twilio WhatsApp Business API

### Business Features
- ✅ **Payment Gateway**: Razorpay integration for subscriptions
- ✅ **Client Portal**: Shareable access links for clients
- ✅ **Invoice Generation**: Automated billing system
- ✅ **Usage Tracking**: Per-company billing and limits

### Technical Features
- ✅ **RESTful API**: Full OpenAPI documentation at `/api/docs`
- ✅ **Rate Limiting**: DDoS protection via NGINX
- ✅ **Caching**: Redis-based caching layer
- ✅ **Database Migrations**: Alembic version control
- ✅ **Health Checks**: Monitoring endpoints for all services
- ✅ **Backup System**: Automated PostgreSQL backups
- ✅ **SSL/TLS**: HTTPS encryption for all traffic

---

## 💰 Pricing Plans

| Plan | Monthly Fee | Setup Fee | Companies | Clients | Features |
|------|------------|-----------|-----------|---------|----------|
| **Trial** | ₹0 | ₹0 | 5 | 2 | Basic features, 15 days |
| **Starter** | ₹2,999 | ₹0 | 50 | 5 | AI automation, data scraping, analytics |
| **Professional** | ₹5,999 | ₹0 | 200 | 20 | Advanced analytics, risk prediction, client portal |
| **Enterprise** | ₹14,999 | ₹5,000 | 1,000 | 100 | All features, WhatsApp, API access, priority support |

**Additional Charges:**
- Starter: ₹50/company (beyond limit)
- Professional: ₹40/company
- Enterprise: ₹30/company

---

## 🔄 Update & Maintenance

### Update Application Code
```bash
# Pull latest code
git pull

# Rebuild and restart
docker-compose down
docker-compose build --no-cache
docker-compose up -d

# Run database migrations
docker-compose exec api alembic upgrade head
```

### Update Docker Images
```bash
# Pull latest base images
docker-compose pull

# Rebuild application
docker-compose build --pull
docker-compose up -d
```

### Clean Up Old Data
```bash
# Remove unused images
docker image prune -a

# Remove unused volumes
docker volume prune

# Remove unused networks
docker network prune

# Complete cleanup (⚠️ CAUTION!)
docker system prune -a --volumes
```

---

## 📚 API Documentation

Once deployed, access interactive API documentation at:
- **Swagger UI**: https://localhost/api/docs
- **ReDoc**: https://localhost/api/redoc

### Example API Usage

```bash
# Register new user
curl -X POST "https://localhost/api/v1/auth/register" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user@example.com",
    "password": "SecurePass123!",
    "first_name": "John",
    "last_name": "Doe",
    "firm_name": "Doe Consulting"
  }'

# Login
curl -X POST "https://localhost/api/v1/auth/login" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user@example.com",
    "password": "SecurePass123!"
  }'

# Get user info (with JWT token)
curl -X GET "https://localhost/api/v1/users/me" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"
```

---

## 🤝 Support & Contributing

### Getting Help
1. Check this README thoroughly
2. Review logs: `docker-compose logs -f`
3. Check API documentation: https://localhost/api/docs
4. Verify configuration in `.env`

### Reporting Issues
When reporting issues, include:
- Error messages from logs
- Steps to reproduce
- Environment details (OS, Docker version)
- Relevant configuration (sanitized)

---

## 📄 License

This is a **commercial SaaS product**. All rights reserved.

Unauthorized copying, distribution, or modification is prohibited.

For licensing inquiries: https://yourdomain.com/pricing

---

## 📞 Contact

- **Website**: https://yourdomain.com
- **Email**: support@yourdomain.com
- **Documentation**: See `/Documentation` folder (if exists)

---

## 🎉 You're All Set!

Your CompliancePro360 SaaS platform is ready to deploy!

**Next Steps:**
1. Edit `.env` with your credentials
2. Run `.\deploy.bat` (Windows) or `./deploy.sh` (Linux/Mac)
3. Visit https://localhost
4. Create your admin account
5. Start managing compliance!

---

**Built with:** FastAPI • Flask • PostgreSQL • Redis • Celery • NGINX • Docker

**Version:** 2.0.0 | **Last Updated:** 2024

---

*For detailed technical documentation, architecture diagrams, and advanced configurations, please refer to the project wiki or contact support.*
