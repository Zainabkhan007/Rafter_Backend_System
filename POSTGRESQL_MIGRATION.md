# PostgreSQL Migration Guide

## ✅ Migration Completed Successfully

Your Rafter Backend has been successfully migrated from SQLite to PostgreSQL!

## Database Information

- **Database Name**: `rafter_db`
- **User**: `rafter_user`
- **Password**: `rafter_password_2024`
- **Host**: `localhost`
- **Port**: `5432`

## Migration Summary

### Data Migrated
- **592** Parents
- **49** Staff
- **1,512** Students
- **6** Primary Schools
- **14** Secondary Schools
- **2,279** Orders
- **4,692** Transactions
- **3,428** Menus
- **196** Menu Items

**Total: 17,841 objects** successfully migrated!

## PostgreSQL Service Management

### Start PostgreSQL
```bash
brew services start postgresql@16
```

### Stop PostgreSQL
```bash
brew services stop postgresql@16
```

### Restart PostgreSQL
```bash
brew services restart postgresql@16
```

### Check Status
```bash
brew services list | grep postgresql
```

## Database Management

### Connect to Database
```bash
psql rafter_db
```

### Connect as specific user
```bash
psql -U rafter_user -h localhost rafter_db
```

### Common PostgreSQL Commands
```sql
\l              -- List all databases
\dt             -- List all tables
\d table_name   -- Describe table structure
\du             -- List all users
\q              -- Quit
```

## Backup & Restore

### Create Backup
```bash
./backup_postgresql.sh
```
Backups are saved in `./backups/` directory and automatically compressed.

### Restore from Backup
```bash
./restore_postgresql.sh ./backups/rafter_db_backup_YYYYMMDD_HHMMSS.sql.gz
```

### Manual Backup
```bash
pg_dump -U rafter_user -h localhost rafter_db > backup.sql
```

### Manual Restore
```bash
psql -U rafter_user -h localhost rafter_db < backup.sql
```

## Django Management

### Run Migrations
```bash
source venv/bin/activate
python manage.py migrate
```

### Create Superuser
```bash
python manage.py createsuperuser
```

### Run Server
```bash
python manage.py runserver
```

## Troubleshooting

### Permission Issues
If you encounter permission errors:
```bash
psql rafter_db << 'EOF'
GRANT ALL ON SCHEMA public TO rafter_user;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO rafter_user;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO rafter_user;
EOF
```

### Connection Issues
1. Check if PostgreSQL is running:
   ```bash
   brew services list | grep postgresql
   ```

2. Check PostgreSQL logs:
   ```bash
   tail -f /opt/homebrew/var/log/postgresql@16.log
   ```

### Reset Database
```bash
psql postgres << 'EOF'
DROP DATABASE rafter_db;
CREATE DATABASE rafter_db;
GRANT ALL PRIVILEGES ON DATABASE rafter_db TO rafter_user;
EOF
```

Then run migrations:
```bash
python manage.py migrate
```

## Performance Tips

### Enable Query Logging (Development Only)
Add to `settings.py`:
```python
LOGGING = {
    'version': 1,
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
        },
    },
    'loggers': {
        'django.db.backends': {
            'handlers': ['console'],
            'level': 'DEBUG',
        },
    },
}
```

### Add Database Indexes
For frequently queried fields, add indexes in models:
```python
class MyModel(models.Model):
    field = models.CharField(max_length=100, db_index=True)
```

### Connection Pooling (Production)
Consider using `django-db-connection-pool` or `pgbouncer` for production.

## Security Recommendations

### For Production:
1. **Change the default password**:
   ```sql
   ALTER USER rafter_user WITH PASSWORD 'your_secure_password';
   ```

2. **Update settings.py** to use environment variables:
   ```python
   DATABASES = {
       'default': {
           'ENGINE': 'django.db.backends.postgresql',
           'NAME': os.getenv('DB_NAME', 'rafter_db'),
           'USER': os.getenv('DB_USER', 'rafter_user'),
           'PASSWORD': os.getenv('DB_PASSWORD'),
           'HOST': os.getenv('DB_HOST', 'localhost'),
           'PORT': os.getenv('DB_PORT', '5432'),
       }
   }
   ```

3. **Create `.env` file** (add to `.gitignore`):
   ```
   DB_NAME=rafter_db
   DB_USER=rafter_user
   DB_PASSWORD=your_secure_password
   DB_HOST=localhost
   DB_PORT=5432
   ```

4. **Restrict network access** to PostgreSQL in `postgresql.conf`

## Old SQLite Database

The original SQLite database (`db.sqlite3`) has been preserved. You can:
- Keep it as a backup
- Delete it to save space
- Archive it for compliance purposes

**Do NOT delete it until you've verified everything works correctly!**

## Benefits of PostgreSQL

✅ **Better Performance**: Handles concurrent connections much better than SQLite
✅ **ACID Compliance**: Full transaction support
✅ **Advanced Features**: JSON fields, full-text search, etc.
✅ **Scalability**: Ready for production workloads
✅ **Better Data Integrity**: Proper foreign key constraints
✅ **Concurrent Writes**: Multiple users can write simultaneously

## Next Steps

1. ✅ Test all API endpoints
2. ✅ Verify transactions are working
3. ✅ Test order creation and cancellation
4. ✅ Check admin panel functionality
5. ⚠️ Set up regular backups (cron job)
6. ⚠️ Update production environment variables
7. ⚠️ Configure connection pooling for production

## Support

If you encounter any issues:
1. Check PostgreSQL logs
2. Verify database permissions
3. Ensure PostgreSQL service is running
4. Check Django settings configuration

---

**Migration completed on**: December 2, 2025
**PostgreSQL version**: 16.11
**Django version**: 5.2.8
