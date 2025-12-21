# AWS Deployment Guide - Rafter Backend

Complete guide to deploy your Django application on AWS with PostgreSQL RDS.

## Architecture Overview

```
┌─────────────────┐
│   Route 53      │  (Optional: DNS)
│   (Domain)      │
└────────┬────────┘
         │
┌────────▼────────┐
│  Application    │
│  Load Balancer  │  (Distributes traffic)
└────────┬────────┘
         │
┌────────▼────────┐
│   EC2 Instance  │  (Django + Gunicorn)
│   or ECS/EB     │
└────────┬────────┘
         │
    ┌────┴────┐
    │         │
┌───▼──┐  ┌──▼───┐
│ RDS  │  │  S3  │  (Media/Static)
│(PG)  │  │Bucket│
└──────┘  └──────┘
```

## Prerequisites

✅ AWS Account with IAM user (you have this)
✅ AWS CLI installed
✅ Domain name (optional but recommended)
✅ Git repository (GitHub/GitLab/BitBucket)

---

## Part 1: AWS CLI Setup

### Install AWS CLI (if not installed)
```bash
# macOS
brew install awscli

# Verify installation
aws --version
```

### Configure AWS CLI
```bash
aws configure

# You'll be prompted for:
# AWS Access Key ID: [Your IAM Access Key]
# AWS Secret Access Key: [Your IAM Secret Key]
# Default region name: us-east-1 (or your preferred region)
# Default output format: json
```

### Test AWS Connection
```bash
aws sts get-caller-identity
```

---

## Part 2: Create RDS PostgreSQL Database

### Step 1: Create RDS Instance via AWS Console

1. **Go to RDS Console**:
   - Navigate to: https://console.aws.amazon.com/rds/

2. **Create Database**:
   - Click "Create database"
   - **Engine**: PostgreSQL
   - **Version**: PostgreSQL 16.x (latest)
   - **Templates**: Free tier (for testing) OR Production

3. **Settings**:
   ```
   DB instance identifier: rafter-production-db
   Master username: rafter_admin
   Master password: [Create a strong password]
   ```

4. **Instance Configuration**:
   - **Free Tier**: db.t3.micro (1 vCPU, 1 GB RAM)
   - **Production**: db.t3.small or larger

5. **Storage**:
   - Storage type: General Purpose SSD (gp3)
   - Allocated storage: 20 GB (minimum)
   - Enable storage autoscaling: Yes
   - Maximum storage: 100 GB

6. **Connectivity**:
   - **VPC**: Default VPC
   - **Public access**: Yes (for initial setup, restrict later)
   - **VPC security group**: Create new
   - **Database port**: 5432

7. **Additional Configuration**:
   - Initial database name: `rafter_production`
   - **Backup retention**: 7 days
   - **Enable encryption**: Yes

8. Click "Create database" (takes 5-10 minutes)

### Step 2: Configure Security Group

1. Go to **EC2 Console** → **Security Groups**
2. Find your RDS security group
3. **Edit inbound rules**:
   ```
   Type: PostgreSQL
   Protocol: TCP
   Port: 5432
   Source: Your IP / EC2 security group
   ```

### Step 3: Get RDS Endpoint

```bash
aws rds describe-db-instances \
  --db-instance-identifier rafter-production-db \
  --query 'DBInstances[0].Endpoint.Address' \
  --output text
```

Save this endpoint! You'll need it for `DB_HOST`.

---

## Part 3: Create S3 Bucket for Media/Static Files

### Step 1: Create S3 Bucket

```bash
# Replace with your unique bucket name
aws s3 mb s3://rafter-backend-media-prod --region us-east-1
```

### Step 2: Configure Bucket Policy

Create a file `s3-bucket-policy.json`:
```json
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Sid": "PublicReadGetObject",
            "Effect": "Allow",
            "Principal": "*",
            "Action": "s3:GetObject",
            "Resource": "arn:aws:s3:::rafter-backend-media-prod/*"
        }
    ]
}
```

Apply the policy:
```bash
aws s3api put-bucket-policy \
  --bucket rafter-backend-media-prod \
  --policy file://s3-bucket-policy.json
```

### Step 3: Enable CORS

Create `s3-cors-config.json`:
```json
{
    "CORSRules": [
        {
            "AllowedOrigins": ["*"],
            "AllowedMethods": ["GET", "POST", "PUT", "DELETE", "HEAD"],
            "AllowedHeaders": ["*"],
            "ExposeHeaders": ["ETag"],
            "MaxAgeSeconds": 3000
        }
    ]
}
```

Apply CORS:
```bash
aws s3api put-bucket-cors \
  --bucket rafter-backend-media-prod \
  --cors-configuration file://s3-cors-config.json
```

---

## Part 4: Launch EC2 Instance

### Step 1: Create EC2 Instance

```bash
# Create key pair for SSH access
aws ec2 create-key-pair \
  --key-name rafter-backend-key \
  --query 'KeyMaterial' \
  --output text > rafter-backend-key.pem

chmod 400 rafter-backend-key.pem
```

### Step 2: Launch Instance (via AWS Console)

1. Go to **EC2 Console**
2. Click "Launch Instance"
3. **Name**: `rafter-backend-server`
4. **AMI**: Ubuntu Server 22.04 LTS
5. **Instance type**: t3.small (or t3.medium for production)
6. **Key pair**: Select `rafter-backend-key`
7. **Network**: Allow SSH (22), HTTP (80), HTTPS (443), Custom TCP (8000 for testing)
8. **Storage**: 20 GB gp3
9. Click "Launch instance"

### Step 3: Allocate Elastic IP (optional but recommended)

```bash
# Allocate Elastic IP
aws ec2 allocate-address --domain vpc

# Associate with instance
aws ec2 associate-address \
  --instance-id i-xxxxxxxxxxxxx \
  --allocation-id eipalloc-xxxxxxxxxxxxx
```

---

## Part 5: Deploy Application to EC2

### Step 1: Connect to EC2

```bash
ssh -i rafter-backend-key.pem ubuntu@<YOUR-EC2-PUBLIC-IP>
```

### Step 2: Install Dependencies

```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install Python and PostgreSQL client
sudo apt install -y python3-pip python3-venv python3-dev \
  postgresql-client libpq-dev nginx git

# Install system dependencies
sudo apt install -y build-essential libssl-dev libffi-dev
```

### Step 3: Clone Repository

```bash
# Create app directory
sudo mkdir -p /var/www/rafter-backend
sudo chown $USER:$USER /var/www/rafter-backend

# Clone your repository
cd /var/www/rafter-backend
git clone https://github.com/YOUR-USERNAME/Rafter_Backend_System.git .

# Or upload files via SCP
# scp -i rafter-backend-key.pem -r ./Rafter_Backend_System ubuntu@<EC2-IP>:/var/www/rafter-backend/
```

### Step 4: Set Up Python Environment

```bash
cd /var/www/rafter-backend

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install requirements
pip install --upgrade pip
pip install -r requirements-prod.txt
```

### Step 5: Configure Environment Variables

```bash
# Create .env file
nano .env
```

Add the following (replace with your actual values):
```bash
SECRET_KEY=your-super-secret-key-generate-new-one
DEBUG=False
ALLOWED_HOSTS=your-domain.com,www.your-domain.com,<EC2-PUBLIC-IP>

# Database
DB_ENGINE=django.db.backends.postgresql
DB_NAME=rafter_production
DB_USER=rafter_admin
DB_PASSWORD=your-rds-password
DB_HOST=rafter-production-db.xxxxx.us-east-1.rds.amazonaws.com
DB_PORT=5432

# AWS S3
AWS_ACCESS_KEY_ID=your-access-key
AWS_SECRET_ACCESS_KEY=your-secret-key
AWS_STORAGE_BUCKET_NAME=rafter-backend-media-prod
AWS_S3_REGION_NAME=us-east-1

# Stripe
STRIPE_SECRET_KEY=your-stripe-secret-key
```

### Step 6: Run Migrations

```bash
source venv/bin/activate
python manage.py migrate
python manage.py collectstatic --noinput
python manage.py createsuperuser
```

### Step 7: Test Application

```bash
# Test with Django dev server
python manage.py runserver 0.0.0.0:8000

# Visit: http://<EC2-PUBLIC-IP>:8000
```

---

## Part 6: Configure Gunicorn

### Step 1: Create Gunicorn Config

```bash
nano /var/www/rafter-backend/gunicorn_config.py
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

### Step 2: Create Systemd Service

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

### Step 3: Start Gunicorn

```bash
# Create logs directory
mkdir -p /var/www/rafter-backend/logs

# Start and enable service
sudo systemctl start gunicorn
sudo systemctl enable gunicorn
sudo systemctl status gunicorn
```

---

## Part 7: Configure Nginx

### Step 1: Create Nginx Config

```bash
sudo nano /etc/nginx/sites-available/rafter-backend
```

Add:
```nginx
server {
    listen 80;
    server_name your-domain.com www.your-domain.com;

    client_max_body_size 100M;

    location = /favicon.ico { access_log off; log_not_found off; }

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
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

### Step 2: Enable Site

```bash
sudo ln -s /etc/nginx/sites-available/rafter-backend /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

---

## Part 8: SSL Certificate (Let's Encrypt)

```bash
# Install Certbot
sudo apt install -y certbot python3-certbot-nginx

# Get certificate
sudo certbot --nginx -d your-domain.com -d www.your-domain.com

# Auto-renewal test
sudo certbot renew --dry-run
```

---

## Part 9: Monitoring & Maintenance

### CloudWatch Logs

```bash
# Install CloudWatch agent
wget https://s3.amazonaws.com/amazoncloudwatch-agent/ubuntu/amd64/latest/amazon-cloudwatch-agent.deb
sudo dpkg -i amazon-cloudwatch-agent.deb
```

### Automated Backups

Create cron job:
```bash
crontab -e
```

Add:
```bash
# Backup database daily at 2 AM
0 2 * * * /var/www/rafter-backend/backup_postgresql.sh

# Restart Gunicorn weekly
0 3 * * 0 sudo systemctl restart gunicorn
```

---

## Part 10: Deployment Checklist

### Pre-Deployment
- [ ] All environment variables set
- [ ] RDS instance created and accessible
- [ ] S3 bucket created and configured
- [ ] EC2 instance launched
- [ ] Security groups configured

### Deployment
- [ ] Code deployed to EC2
- [ ] Dependencies installed
- [ ] Migrations run successfully
- [ ] Static files collected
- [ ] Gunicorn running
- [ ] Nginx configured
- [ ] SSL certificate installed

### Post-Deployment
- [ ] Test all API endpoints
- [ ] Verify database connections
- [ ] Check media file uploads
- [ ] Monitor logs for errors
- [ ] Set up CloudWatch monitoring
- [ ] Configure automated backups

---

## Cost Estimate (Monthly)

| Service | Configuration | Cost |
|---------|--------------|------|
| EC2 (t3.small) | 24/7 | ~$15 |
| RDS (db.t3.micro) | 20GB storage | ~$15 |
| S3 | 50GB storage | ~$1.15 |
| Data Transfer | 1TB/month | ~$90 |
| **Total** | | **~$121/month** |

*Free tier eligible services can reduce costs significantly for the first 12 months.*

---

## Troubleshooting

### Common Issues

**502 Bad Gateway**
```bash
# Check Gunicorn status
sudo systemctl status gunicorn
sudo journalctl -u gunicorn -n 50

# Check Nginx error logs
sudo tail -f /var/log/nginx/error.log
```

**Database Connection Error**
```bash
# Test database connection
psql -h <RDS-ENDPOINT> -U rafter_admin -d rafter_production

# Check security group allows your EC2 IP
```

**Static Files Not Loading**
```bash
# Re-collect static files
python manage.py collectstatic --noinput

# Check Nginx permissions
ls -la /var/www/rafter-backend/staticfiles/
```

---

## Quick Commands Reference

```bash
# Restart services
sudo systemctl restart gunicorn
sudo systemctl restart nginx

# View logs
sudo journalctl -u gunicorn -f
sudo tail -f /var/log/nginx/access.log

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

**Deployment Date**: December 21, 2025
**Deployed By**: Rafter Team
**Last Updated**: December 21, 2025
