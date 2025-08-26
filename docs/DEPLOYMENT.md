# AI Hedge Fund - Deployment Guide

## 📋 Přehled

Tento guide pokrývá různé způsoby nasazení AI Hedge Fund aplikace do produkčního prostředí. Aplikace je ve stavu **Production-ready beta (v1.5)** s kompletní Docker containerizací a připravena pro produkční nasazení.

**Aktuální stav**: ✅ **Production-ready beta (v1.5)**  
**Docker status**: ✅ **Kompletní containerizace hotová**  
**Deployment možnosti**: 4 plně podporované způsoby

### 🎯 Co je hotové
- ✅ **Docker Compose** - kompletní multi-container setup
- ✅ **FastAPI backend** - production-ready s 36 endpointy
- ✅ **React frontend** - optimalizovaný build pro produkci
- ✅ **Databázová migrace** - Alembic migrations připraveny
- ✅ **Environment konfigurace** - kompletní .env setup
- ✅ **Multi-LLM podpora** - 6 providerů připraveno

### ⚠️ Před produkčním nasazením
- **Security fixes** - 13 bezpečnostních problémů k opravě
- **Code quality** - 1,397 code issues k refaktoringu
- **Testing** - zvýšit coverage z 2.9% na 80%+
- **Monitoring** - implementovat production monitoring

---

## 🚀 Deployment Možnosti

### 1. Docker Deployment (Doporučeno) ✅ HOTOVÉ
### 2. Manual Server Deployment ✅ HOTOVÉ
### 3. Cloud Platform Deployment ✅ HOTOVÉ
### 4. Development Deployment ✅ HOTOVÉ

---

## 🐳 Docker Deployment

### Předpoklady
- Docker 20.10+
- Docker Compose 2.0+
- 4GB+ RAM
- 10GB+ disk space

### Rychlé spuštění

```bash
# Klonování repozitáře
git clone https://github.com/virattt/ai-hedge-fund.git
cd ai-hedge-fund

# Kopírování environment variables
cp .env.example .env
# Upravte .env soubor s vašimi API klíči

# Spuštění pomocí Docker Compose
cd docker
docker-compose up -d
```

### Docker Compose konfigurace

```yaml
# docker/docker-compose.yml
version: '3.8'

services:
  backend:
    build:
      context: ..
      dockerfile: docker/Dockerfile
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=sqlite:///./hedge_fund.db
    volumes:
      - ../app/backend/hedge_fund.db:/app/hedge_fund.db
      - ../.env:/app/.env
    restart: unless-stopped

  frontend:
    build:
      context: ../app/frontend
      dockerfile: ../../docker/Dockerfile.frontend
    ports:
      - "5173:5173"
    depends_on:
      - backend
    restart: unless-stopped

  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf
      - ./ssl:/etc/nginx/ssl
    depends_on:
      - frontend
      - backend
    restart: unless-stopped
```

### Dockerfile pro backend

```dockerfile
# docker/Dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install Poetry
RUN pip install poetry

# Copy dependency files
COPY pyproject.toml poetry.lock ./

# Configure Poetry
RUN poetry config virtualenvs.create false \
    && poetry install --no-dev

# Copy application code
COPY . .

# Expose port
EXPOSE 8000

# Run application
CMD ["uvicorn", "app.backend.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### Dockerfile pro frontend

```dockerfile
# docker/Dockerfile.frontend
FROM node:18-alpine

WORKDIR /app

# Copy package files
COPY package*.json ./

# Install dependencies
RUN npm ci --only=production

# Copy source code
COPY . .

# Build application
RUN npm run build

# Expose port
EXPOSE 5173

# Serve application
CMD ["npm", "run", "preview", "--", "--host", "0.0.0.0"]
```

---

## 🖥️ Manual Server Deployment

### Předpoklady
- Ubuntu 20.04+ / CentOS 8+ / RHEL 8+
- Python 3.11+
- Node.js 18+
- Nginx
- SSL certifikát (Let's Encrypt doporučeno)

### Backend deployment

```bash
# 1. Příprava serveru
sudo apt update && sudo apt upgrade -y
sudo apt install python3.11 python3.11-venv python3-pip nginx -y

# 2. Vytvoření uživatele
sudo useradd -m -s /bin/bash hedgefund
sudo su - hedgefund

# 3. Klonování a setup
git clone https://github.com/virattt/ai-hedge-fund.git
cd ai-hedge-fund

# 4. Python environment
python3.11 -m venv venv
source venv/bin/activate
pip install poetry
poetry install

# 5. Environment variables
cp .env.example .env
# Upravte .env s produkčními hodnotami

# 6. Databáze setup
cd app/backend
alembic upgrade head

# 7. Systemd service
sudo tee /etc/systemd/system/hedgefund-backend.service > /dev/null <<EOF
[Unit]
Description=AI Hedge Fund Backend
After=network.target

[Service]
Type=simple
User=hedgefund
WorkingDirectory=/home/hedgefund/ai-hedge-fund
Environment=PATH=/home/hedgefund/ai-hedge-fund/venv/bin
ExecStart=/home/hedgefund/ai-hedge-fund/venv/bin/uvicorn app.backend.main:app --host 0.0.0.0 --port 8000
Restart=always

[Install]
WantedBy=multi-user.target
EOF

sudo systemctl enable hedgefund-backend
sudo systemctl start hedgefund-backend
```

### Frontend deployment

```bash
# 1. Frontend build
cd app/frontend
npm ci
npm run build

# 2. Nginx konfigurace
sudo tee /etc/nginx/sites-available/hedgefund > /dev/null <<EOF
server {
    listen 80;
    server_name your-domain.com;
    
    # Frontend
    location / {
        root /home/hedgefund/ai-hedge-fund/app/frontend/dist;
        try_files \$uri \$uri/ /index.html;
    }
    
    # Backend API
    location /api/ {
        proxy_pass http://localhost:8000/;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
    }
}
EOF

sudo ln -s /etc/nginx/sites-available/hedgefund /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

### SSL Setup (Let's Encrypt)

```bash
# 1. Install Certbot
sudo apt install certbot python3-certbot-nginx -y

# 2. Získání SSL certifikátu
sudo certbot --nginx -d your-domain.com

# 3. Auto-renewal
sudo crontab -e
# Přidejte: 0 12 * * * /usr/bin/certbot renew --quiet
```

---

## ☁️ Cloud Platform Deployment

### AWS Deployment

#### EC2 Instance
```bash
# 1. Launch EC2 instance (t3.medium doporučeno)
# 2. Security Groups:
#    - HTTP (80)
#    - HTTPS (443)
#    - SSH (22)
#    - Custom TCP (8000) - pouze pro development

# 3. Elastic IP
aws ec2 allocate-address --domain vpc

# 4. Route 53 DNS
aws route53 change-resource-record-sets --hosted-zone-id Z123456789 \
  --change-batch file://dns-change.json
```

#### ECS Deployment
```yaml
# ecs-task-definition.json
{
  "family": "ai-hedge-fund",
  "networkMode": "awsvpc",
  "requiresCompatibilities": ["FARGATE"],
  "cpu": "1024",
  "memory": "2048",
  "executionRoleArn": "arn:aws:iam::account:role/ecsTaskExecutionRole",
  "containerDefinitions": [
    {
      "name": "backend",
      "image": "your-account.dkr.ecr.region.amazonaws.com/ai-hedge-fund-backend:latest",
      "portMappings": [
        {
          "containerPort": 8000,
          "protocol": "tcp"
        }
      ],
      "environment": [
        {
          "name": "DATABASE_URL",
          "value": "postgresql://user:pass@rds-endpoint:5432/hedgefund"
        }
      ]
    }
  ]
}
```

### Google Cloud Platform

#### Cloud Run Deployment
```bash
# 1. Build and push image
gcloud builds submit --tag gcr.io/PROJECT-ID/ai-hedge-fund-backend

# 2. Deploy to Cloud Run
gcloud run deploy ai-hedge-fund-backend \
  --image gcr.io/PROJECT-ID/ai-hedge-fund-backend \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated \
  --set-env-vars DATABASE_URL=postgresql://...
```

### Azure Deployment

#### Container Instances
```bash
# 1. Create resource group
az group create --name ai-hedge-fund-rg --location eastus

# 2. Deploy container
az container create \
  --resource-group ai-hedge-fund-rg \
  --name ai-hedge-fund-backend \
  --image your-registry/ai-hedge-fund-backend:latest \
  --dns-name-label ai-hedge-fund \
  --ports 8000 \
  --environment-variables DATABASE_URL=postgresql://...
```

---

## 🔧 Production Konfigurace

### Environment Variables

```bash
# Produkční .env
NODE_ENV=production
DATABASE_URL=postgresql://user:password@localhost:5432/hedgefund_prod
REDIS_URL=redis://localhost:6379
SECRET_KEY=your-super-secret-key-here

# API Keys
OPENAI_API_KEY=sk-...
GROQ_API_KEY=gsk_...
ANTHROPIC_API_KEY=sk-ant-...
FINANCIAL_DATASETS_API_KEY=...

# Security
ALLOWED_HOSTS=your-domain.com,www.your-domain.com
CORS_ORIGINS=https://your-domain.com,https://www.your-domain.com

# Monitoring
SENTRY_DSN=https://...
LOG_LEVEL=INFO
```

### Databáze konfigurace

#### PostgreSQL Setup
```bash
# 1. Install PostgreSQL
sudo apt install postgresql postgresql-contrib -y

# 2. Create database
sudo -u postgres psql
CREATE DATABASE hedgefund_prod;
CREATE USER hedgefund WITH PASSWORD 'secure_password';
GRANT ALL PRIVILEGES ON DATABASE hedgefund_prod TO hedgefund;
\q

# 3. Update connection string
DATABASE_URL=postgresql://hedgefund:secure_password@localhost:5432/hedgefund_prod
```

#### Redis Setup (pro caching)
```bash
# 1. Install Redis
sudo apt install redis-server -y

# 2. Configure Redis
sudo nano /etc/redis/redis.conf
# Uncomment: requirepass your_redis_password

sudo systemctl restart redis-server
```

### Monitoring a Logging

#### Prometheus + Grafana
```yaml
# docker-compose.monitoring.yml
version: '3.8'

services:
  prometheus:
    image: prom/prometheus
    ports:
      - "9090:9090"
    volumes:
      - ./prometheus.yml:/etc/prometheus/prometheus.yml

  grafana:
    image: grafana/grafana
    ports:
      - "3000:3000"
    environment:
      - GF_SECURITY_ADMIN_PASSWORD=admin
```

#### Application Logging
```python
# app/backend/logging_config.py
import logging
from logging.handlers import RotatingFileHandler

def setup_logging():
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            RotatingFileHandler('logs/app.log', maxBytes=10485760, backupCount=5),
            logging.StreamHandler()
        ]
    )
```

---

## 🔒 Security Best Practices

### 1. API Keys Management
```bash
# Použijte externí secret management
# AWS Secrets Manager, Azure Key Vault, Google Secret Manager

# Nebo environment variables s restricted access
sudo chmod 600 .env
sudo chown hedgefund:hedgefund .env
```

### 2. Firewall konfigurace
```bash
# UFW setup
sudo ufw default deny incoming
sudo ufw default allow outgoing
sudo ufw allow ssh
sudo ufw allow 'Nginx Full'
sudo ufw enable
```

### 3. SSL/TLS konfigurace
```nginx
# Nginx SSL best practices
ssl_protocols TLSv1.2 TLSv1.3;
ssl_ciphers ECDHE-RSA-AES256-GCM-SHA512:DHE-RSA-AES256-GCM-SHA512;
ssl_prefer_server_ciphers off;
ssl_session_cache shared:SSL:10m;
add_header Strict-Transport-Security "max-age=63072000" always;
```

---

## 📊 Performance Optimalizace

### 1. Database Optimalizace
```sql
-- Indexy pro často používané queries
CREATE INDEX idx_flow_runs_created_at ON flow_runs(created_at);
CREATE INDEX idx_api_keys_provider ON api_keys(provider);
```

### 2. Caching Strategy
```python
# Redis caching pro API responses
import redis
from functools import wraps

redis_client = redis.Redis(host='localhost', port=6379, db=0)

def cache_result(expiration=300):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            cache_key = f"{func.__name__}:{hash(str(args) + str(kwargs))}"
            cached = redis_client.get(cache_key)
            if cached:
                return json.loads(cached)
            
            result = func(*args, **kwargs)
            redis_client.setex(cache_key, expiration, json.dumps(result))
            return result
        return wrapper
    return decorator
```

### 3. Load Balancing
```nginx
# Nginx load balancer
upstream backend {
    server 127.0.0.1:8000;
    server 127.0.0.1:8001;
    server 127.0.0.1:8002;
}

server {
    location /api/ {
        proxy_pass http://backend;
    }
}
```

---

## 🚨 Troubleshooting

### Běžné problémy

#### 1. Port již používán
```bash
# Najít proces na portu
sudo lsof -i :8000
sudo kill -9 PID

# Nebo změnit port
uvicorn app.backend.main:app --port 8001
```

#### 2. Databázové problémy
```bash
# Zkontrolovat databázové připojení
python -c "from app.backend.database.connection import engine; print(engine.execute('SELECT 1').scalar())"

# Reset databáze
alembic downgrade base
alembic upgrade head
```

#### 3. SSL problémy
```bash
# Zkontrolovat SSL certifikát
openssl x509 -in /etc/letsencrypt/live/domain.com/fullchain.pem -text -noout

# Obnovit certifikát
sudo certbot renew --force-renewal
```

---

---

## 🔗 Související dokumentace

- **[Přehled dokumentace](./README.md)** - Hlavní dokumentační rozcestník
- **[Architektura systému](./ARCHITECTURE.md)** - Detailní architektura pro deployment
- **[Development Guide](./DEVELOPMENT.md)** - Lokální development setup
- **[API Dokumentace](./API.md)** - API endpointy a konfigurace

---

## 📞 Podpora

Pro deployment podporu:
- **GitHub Issues**: [ai-hedge-fund/issues](https://github.com/virattt/ai-hedge-fund/issues)
- **Dokumentace**: [README.md](../README.md)
- **API Dokumentace**: [API.md](./API.md)
- **Community**: [GitHub Discussions](https://github.com/virattt/ai-hedge-fund/discussions)

## 🚀 Roadmap

### Prioritní úkoly před produkčním nasazením (Q3 2025)
1. **Security fixes** - Oprava 13 bezpečnostních problémů
2. **Code quality** - Refaktoring 1,397 code issues
3. **Testing** - Zvýšení test coverage z 2.9% na 80%+
4. **Production monitoring** - Implementace Prometheus/Grafana

### Plánované vylepšení (Q4 2025)
- **Auto-scaling** - Kubernetes deployment
- **Advanced monitoring** - APM a distributed tracing
- **Backup strategie** - Automatizované zálohy
- **CI/CD pipeline** - GitHub Actions deployment

---

**Poslední aktualizace**: 3. srpna 2025  
**Verze deployment**: v1.5 (Production-ready beta)  
**Kompatibilní s**: AI Hedge Fund v1.5+
