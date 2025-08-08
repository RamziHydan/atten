# Django Attendance Platform - Production Deployment Checklist

Use this checklist to ensure your deployment is secure and production-ready.

## Pre-Deployment Checklist

### Security Configuration
- [ ] **Generate new SECRET_KEY** - Never use the default development key
- [ ] **Set DEBUG=False** - Critical for security
- [ ] **Configure ALLOWED_HOSTS** - Add your domain(s)
- [ ] **Review CSRF_TRUSTED_ORIGINS** - Add trusted domains
- [ ] **Enable security middleware** - Already configured in settings
- [ ] **Use HTTPS in production** - Uncomment SSL settings if available

### Database Configuration
- [ ] **Choose production database** - SQLite (default) or MySQL/PostgreSQL
- [ ] **Set database credentials** - Use environment variables
- [ ] **Run migrations** - `python manage.py migrate`
- [ ] **Create superuser** - `python manage.py createsuperuser`
- [ ] **Seed test data** (optional) - `python manage.py seed_all --clear-all`

### Static Files
- [ ] **Install WhiteNoise** - Already added to requirements.txt
- [ ] **Configure static files** - Already configured in settings
- [ ] **Collect static files** - `python manage.py collectstatic --noinput`
- [ ] **Test static file serving** - Check CSS/JS loads correctly

### Environment Variables
- [ ] **Copy .env.example to .env** - Fill in actual values
- [ ] **Set SECRET_KEY** - Generate new secure key
- [ ] **Set DEBUG=False** - Never True in production
- [ ] **Set ALLOWED_HOSTS** - Your domain(s)
- [ ] **Set database credentials** (if not using SQLite)

## PythonAnywhere Specific

### Account Setup
- [ ] **PythonAnywhere account** - Free or paid tier
- [ ] **Upload code** - Via Git or file upload
- [ ] **Create virtual environment** - Python 3.10 recommended
- [ ] **Install dependencies** - `pip install -r requirements.txt`

### Web App Configuration
- [ ] **Create web app** - Manual configuration, Python 3.10
- [ ] **Set source code path** - `/home/yourusername/attendance-platform`
- [ ] **Set working directory** - Same as source code path
- [ ] **Configure WSGI file** - Use provided template
- [ ] **Set static files mapping** - `/static/` → `/home/yourusername/attendance-platform/staticfiles/`
- [ ] **Set media files mapping** - `/media/` → `/home/yourusername/attendance-platform/mediafiles/`

### Testing
- [ ] **Reload web app** - Click reload button
- [ ] **Test homepage** - Should load without errors
- [ ] **Test login** - Use test accounts
- [ ] **Test different user roles** - Super admin, owner, HR, employee
- [ ] **Test core functionality** - Check-in/out, reports, management
- [ ] **Check error logs** - Review for any issues

## Post-Deployment

### Monitoring
- [ ] **Set up error monitoring** - Check logs regularly
- [ ] **Monitor performance** - Page load times, database queries
- [ ] **Set up backups** - Database and media files
- [ ] **Document admin procedures** - For ongoing maintenance

### User Management
- [ ] **Change default passwords** - All test accounts
- [ ] **Create real user accounts** - For actual users
- [ ] **Set up proper permissions** - Role-based access
- [ ] **Train users** - On platform usage

### Maintenance
- [ ] **Schedule regular updates** - Dependencies and security patches
- [ ] **Set up monitoring** - Uptime and performance
- [ ] **Plan backup strategy** - Regular database backups
- [ ] **Document procedures** - For common tasks

## Test Accounts Available

After running `python manage.py seed_all --clear-all`, these accounts will be available:

### Super Admin
- **Username:** `superadmin`
- **Password:** `admin123`
- **Access:** Full system access, all companies

### Company Owners
- **TechCorp Solutions:** `owner1` / `owner123`
- **Global Innovations Inc:** `owner2` / `owner123`
- **Access:** Company-wide management

### HR Managers
- **TechCorp Main Branch:** `hr1_1` / `hr123`
- **Global Innovations Main Branch:** `hr2_1` / `hr123`
- **Access:** Branch-specific employee management

### Employees
- **TechCorp Employee:** `emp1_1` / `emp123`
- **Global Innovations Employee:** `emp2_1` / `emp123`
- **Access:** Check-in/out functionality only

## Troubleshooting Common Issues

### Static Files Not Loading
```bash
python manage.py collectstatic --noinput
```
Check static files configuration in PythonAnywhere web tab.

### Database Errors
```bash
python manage.py migrate
python manage.py check --deploy
```

### Import Errors
- Verify virtual environment is activated
- Check all dependencies are installed
- Verify Python path in WSGI file

### Permission Errors
- Check file permissions
- Verify working directory configuration
- Ensure virtual environment has correct permissions

## Security Best Practices

1. **Never commit secrets** - Use environment variables
2. **Regular updates** - Keep Django and dependencies updated
3. **Monitor logs** - Check for suspicious activity
4. **Use HTTPS** - Enable SSL/TLS when possible
5. **Strong passwords** - Enforce password policies
6. **Regular backups** - Automate database backups
7. **Access control** - Review user permissions regularly

## Performance Optimization

1. **Database indexing** - Add indexes for frequently queried fields
2. **Query optimization** - Use select_related and prefetch_related
3. **Caching** - Implement Redis/Memcached if needed
4. **Static file optimization** - Use CDN for large deployments
5. **Database choice** - Consider PostgreSQL/MySQL for better performance

## Support Resources

- **Django Documentation:** https://docs.djangoproject.com/
- **PythonAnywhere Help:** https://help.pythonanywhere.com/
- **Django Deployment Checklist:** https://docs.djangoproject.com/en/stable/howto/deployment/checklist/

---

**Remember:** Always test thoroughly in a staging environment before deploying to production!
