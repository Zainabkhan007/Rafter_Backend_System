# AWS Deployment Quick Start Guide

## 🚀 Quick Overview

This is a simplified guide to get your Rafter Backend running on AWS. For detailed instructions, see [AWS_DEPLOYMENT_GUIDE.md](AWS_DEPLOYMENT_GUIDE.md).

---

## Prerequisites Checklist

- [ ] AWS Account with IAM user credentials
- [ ] AWS CLI installed and configured
- [ ] Git repository (push your code first!)
- [ ] Domain name (optional)

---

## Step-by-Step Deployment

### 1️⃣ Configure AWS CLI (5 minutes)

```bash
aws configure
# Enter your IAM credentials when prompted
```

### 2️⃣ Create RDS Database (10 minutes)

**Via AWS Console** (https://console.aws.amazon.com/rds/):

1. Click "Create database"
2. Choose **PostgreSQL 16**
3. Settings:
   - DB identifier: `rafter-production-db`
   - Master username: `rafter_admin`
   - Master password: [Create strong password]
4. Instance: **db.t3.micro** (Free tier) or **db.t3.small**
5. Storage: **20 GB** minimum
6. Connectivity: **Public access = Yes**
7. Additional: Initial database name = `rafter_production`
8. Click "Create database"

**Save these details:**
```
Endpoint: rafter-production-db.xxxxx.region.rds.amazonaws.com
Username: rafter_admin
Password: [your password]
Database: rafter_production
```

### 3️⃣ Configure RDS Security (2 minutes)

1. Go to **EC2** → **Security Groups**
2. Find your RDS security group
3. Edit **Inbound rules** → Add rule:
   - Type: PostgreSQL
   - Port: 5432
   - Source: Anywhere (0.0.0.0/0) *or your EC2 security group*

### 4️⃣ Create S3 Bucket (3 minutes)

```bash
aws s3 mb s3://rafter-backend-media-YOUR-NAME --region us-east-1
```

### 5️⃣ Launch EC2 Instance (10 minutes)

**Via AWS Console** (https://console.aws.amazon.com/ec2/):

1. Click "Launch Instance"
2. Name: `rafter-backend-server`
3. AMI: **Ubuntu Server 22.04 LTS**
4. Instance type: **t3.small** (recommended) or **t3.medium**
5. Create new key pair:
   - Name: `rafter-backend-key`
   - Download the `.pem` file
6. Network settings:
   - Allow SSH (22)
   - Allow HTTP (80)
   - Allow HTTPS (443)
   - Allow Custom TCP (8000) for testing
7. Storage: **20 GB**
8. Click "Launch instance"

**Save these details:**
```
Instance ID: i-xxxxxxxxxxxxx
Public IP: xx.xx.xx.xx
Key file: rafter-backend-key.pem
```

### 6️⃣ Connect to EC2 (2 minutes)

```bash
# Set correct permissions on key file
chmod 400 rafter-backend-key.pem

# Connect to EC2
ssh -i rafter-backend-key.pem ubuntu@YOUR-EC2-IP
```

### 7️⃣ Setup EC2 Environment (10 minutes)

Run on EC2 instance:

```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install dependencies
sudo apt install -y python3-pip python3-venv python3-dev \
  postgresql-client libpq-dev nginx git \
  build-essential libssl-dev libffi-dev

# Create project directory
sudo mkdir -p /var/www/rafter-backend
sudo chown $USER:$USER /var/www/rafter-backend
cd /var/www/rafter-backend

# Clone your repository
git clone YOUR-REPO-URL .

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install Python packages
pip install --upgrade pip
pip install -r requirements-prod.txt
```

### 8️⃣ Configure Environment Variables (5 minutes)

```bash
nano .env
```

Add (replace with your actual values):
```bash
SECRET_KEY=generate-a-new-secret-key-here
DEBUG=False
ALLOWED_HOSTS=your-domain.com,YOUR-EC2-IP

DB_ENGINE=django.db.backends.postgresql
DB_NAME=rafter_production
DB_USER=rafter_admin
DB_PASSWORD=your-rds-password
DB_HOST=your-rds-endpoint.rds.amazonaws.com
DB_PORT=5432

AWS_ACCESS_KEY_ID=your-iam-access-key
AWS_SECRET_ACCESS_KEY=your-iam-secret-key
AWS_STORAGE_BUCKET_NAME=rafter-backend-media-YOUR-NAME
AWS_S3_REGION_NAME=us-east-1

STRIPE_SECRET_KEY=your-stripe-key
```

Save with `Ctrl+X`, then `Y`, then `Enter`.

### 9️⃣ Initialize Django (5 minutes)

```bash
source venv/bin/activate

# Run migrations
python manage.py migrate

# Collect static files
python manage.py collectstatic --noinput

# Create admin user
python manage.py createsuperuser
```

### 🔟 Setup Gunicorn (5 minutes)

Create Gunicorn config:
```bash
nano gunicorn_config.py
```

Add:
```python
bind = "0.0.0.0:8000"
workers = 3
timeout = 120
accesslog = "/var/www/rafter-backend/logs/gunicorn-access.log"
errorlog = "/var/www/rafter-backend/logs/gunicorn-error.log"
loglevel = "info"
```

Create systemd service:
```bash
sudo nano /etc/systemd/system/gunicorn.service
```

Add:
```ini
[Unit]
Description=Gunicorn daemon for Rafter Backend
After=network.target

[Service]
User=ubuntu
Group=www-data
WorkingDirectory=/var/www/rafter-backend
Environment="PATH=/var/www/rafter-backend/venv/bin"
EnvironmentFile=/var/www/rafter-backend/.env
ExecStart=/var/www/rafter-backend/venv/bin/gunicorn \
          --config /var/www/rafter-backend/gunicorn_config.py \
          rafters_food.wsgi:application

[Install]
WantedBy=multi-user.target
```

Start Gunicorn:
```bash
mkdir -p logs
sudo systemctl start gunicorn
sudo systemctl enable gunicorn
sudo systemctl status gunicorn
```

### 1️⃣1️⃣ Setup Nginx (5 minutes)

```bash
sudo nano /etc/nginx/sites-available/rafter-backend
```

Add:
```nginx
server {
    listen 80;
    server_name YOUR-EC2-IP your-domain.com;

    client_max_body_size 100M;

    location /static/ {
        alias /var/www/rafter-backend/staticfiles/;
    }

    location /media/ {
        alias /var/www/rafter-backend/media/;
    }

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    }
}
```

Enable and start:
```bash
sudo ln -s /etc/nginx/sites-available/rafter-backend /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

### 1️⃣2️⃣ Test Your Deployment! 🎉

Visit: `http://YOUR-EC2-IP`

You should see your Django application!

---

## Optional: Add SSL Certificate (5 minutes)

```bash
sudo apt install -y certbot python3-certbot-nginx
sudo certbot --nginx -d your-domain.com
```

---

## Troubleshooting

### Can't connect to database?
```bash
# Test database connection
psql -h YOUR-RDS-ENDPOINT -U rafter_admin -d rafter_production

# Check security group allows EC2 IP
```

### 502 Bad Gateway?
```bash
# Check Gunicorn logs
sudo journalctl -u gunicorn -n 50

# Restart Gunicorn
sudo systemctl restart gunicorn
```

### Static files not loading?
```bash
python manage.py collectstatic --noinput
sudo systemctl restart nginx
```

---

## Quick Commands

```bash
# View logs
sudo journalctl -u gunicorn -f

# Restart services
sudo systemctl restart gunicorn
sudo systemctl restart nginx

# Update code
cd /var/www/rafter-backend
git pull
source venv/bin/activate
pip install -r requirements-prod.txt
python manage.py migrate
python manage.py collectstatic --noinput
sudo systemctl restart gunicorn
```

---

## Estimated Time

- **Total setup time**: ~60 minutes
- **Cost**: ~$15-30/month (depending on traffic)

---

## Next Steps

1. ✅ Test all API endpoints
2. ✅ Upload test data
3. ✅ Configure backups
4. ✅ Set up monitoring
5. ✅ Add custom domain
6. ✅ Enable SSL certificate

---

**Need help?** Check [AWS_DEPLOYMENT_GUIDE.md](AWS_DEPLOYMENT_GUIDE.md) for detailed instructions.

**Deployed successfully?** 🎉 Congratulations! Your Rafter Backend is now live on AWS!
