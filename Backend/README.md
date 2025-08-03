# PrintSmart Backend

A comprehensive Django backend system for print management with file processing, payment integration, and user management.

## 🚀 Quick Setup

### Option 1: PowerShell (Recommended for Windows)

```powershell
.\setup.ps1
```

### Option 2: Batch Script

```cmd
setup.bat
```

### Option 3: Manual Python Setup

```bash
python setup_project.py
```

## 📋 Prerequisites

- Python 3.8+ installed
- Git installed
- PostgreSQL (optional, defaults to SQLite for development)
- Redis (optional, for Celery task queue)

## 🏗️ Project Structure

```
printsmart_backend/
├── printsmart_backend/          # Main project settings
├── users/                       # User management app
├── files/                       # File upload & processing
├── print_jobs/                  # Print job management
├── payments/                    # Payment integration
├── core/                        # Shared utilities
├── media/                       # Uploaded files
├── static/                      # Static files
├── templates/                   # HTML templates
├── logs/                        # Application logs
├── requirements.txt             # Dependencies
├── .env                         # Environment variables
└── manage.py                    # Django management
```

## 🔧 Configuration

1. **Update .env file** with your settings:

   ```env
   SECRET_KEY=your-secret-key
   RAZORPAY_KEY_ID=your-key
   RAZORPAY_KEY_SECRET=your-secret
   DATABASE_PASSWORD=your-db-password
   ```

2. **Database Setup** (Optional):

   ```bash
   # For PostgreSQL
   createdb printsmart_db
   ```

3. **Create Superuser**:

   ```bash
   python manage.py createsuperuser
   ```

## 🚀 Running the Application

### Development Server

```bash
python manage.py runserver
```

### With Celery (for background tasks)

```bash
# Terminal 1: Redis server
redis-server

# Terminal 2: Celery worker
celery -A printsmart_backend worker --loglevel=info

# Terminal 3: Django server
python manage.py runserver
```

## 📚 API Documentation

### Authentication Endpoints

- `POST /api/auth/register/` - User registration
- `POST /api/auth/login/` - User login
- `POST /api/auth/refresh/` - Refresh JWT token
- `POST /api/auth/logout/` - User logout

### File Management

- `POST /api/files/upload/` - Upload files
- `GET /api/files/` - List user files
- `PUT /api/files/{id}/edit/` - Edit file (rotate, crop, etc.)
- `DELETE /api/files/{id}/` - Delete file

### Print Jobs

- `POST /api/print/submit/` - Submit print job
- `GET /api/print/jobs/` - List user print jobs
- `GET /api/print/status/{id}/` - Check print job status

### Payments

- `POST /api/payments/initiate/` - Initiate payment
- `POST /api/payments/verify/` - Verify payment callback
- `GET /api/payments/history/` - Payment history

### Admin Endpoints

- `GET /api/admin/dashboard/` - Admin dashboard stats
- `GET /api/admin/jobs/` - All print jobs
- `PUT /api/admin/jobs/{id}/status/` - Update job status
- `GET /api/admin/users/` - User management

## 🔒 Security Features

- JWT-based authentication
- Password hashing with bcrypt
- File type validation
- Size limit enforcement
- Role-based access control
- HTTPS enforcement in production
- CORS configuration

## 📁 File Processing

### Supported Formats

- **PDF**: PyMuPDF for processing
- **DOCX**: python-docx for handling
- **Images**: Pillow for JPG, PNG processing

### Features

- File validation and virus scanning
- Thumbnail generation
- Page manipulation (rotate, delete, crop)
- Format conversion
- Print-ready optimization

## 💳 Payment Integration

### Razorpay Features

- Secure payment processing
- Webhook verification
- Token-based system
- Payment history tracking
- Refund management

## 🖨️ Print Management

### Features

- Multiple printer support
- Job queuing system
- Status tracking
- Print preferences (color, copies, pages)
- Network printer integration

### Windows Print Integration

```python
import win32print
import win32api

# List available printers
printers = [printer[2] for printer in win32print.EnumPrinters(2)]

# Print file
win32api.ShellExecute(0, "print", filename, None, ".", 0)
```

## 📊 Monitoring & Logging

### Logging Configuration

- Structured logging with levels
- File rotation
- Error tracking
- User activity logs
- System performance metrics

### Optional Monitoring

- Prometheus metrics
- Grafana dashboards
- Health check endpoints

## 🧪 Testing

```bash
# Run all tests
python manage.py test

# Run with coverage
pip install coverage
coverage run --source='.' manage.py test
coverage report
coverage html
```

## 📦 Deployment

### Production Settings

1. Set `DEBUG=False`
2. Configure allowed hosts
3. Set up PostgreSQL
4. Configure static file serving
5. Set up SSL/HTTPS
6. Configure logging

### Docker Deployment (Optional)

```dockerfile
FROM python:3.9
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
CMD ["gunicorn", "printsmart_backend.wsgi:application"]
```

## 🤝 Contributing

1. Fork the repository
2. Create feature branch
3. Make changes
4. Add tests
5. Submit pull request

## 📝 License

This project is licensed under the MIT License.

## 🆘 Troubleshooting

### Common Issues

1. **Virtual Environment Issues**:

   ```powershell
   Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
   ```

2. **Package Installation Errors**:

   ```bash
   pip install --upgrade pip setuptools wheel
   ```

3. **Database Migration Issues**:

   ```bash
   python manage.py makemigrations --empty appname
   python manage.py migrate --fake
   ```

4. **Static Files Not Loading**:

   ```bash
   python manage.py collectstatic --clear
   ```

### Support

For issues and questions:

- Check the logs in `logs/` directory
- Review Django debug output
- Check database connectivity
- Verify environment variables

## 🔄 Development Workflow

1. **Daily Development**:

   ```bash
   # Activate environment
   venv\Scripts\activate

   # Update dependencies
   pip install -r requirements.txt

   # Run migrations
   python manage.py migrate

   # Start server
   python manage.py runserver
   ```

2. **Adding New Features**:

   ```bash
   # Create new app
   python manage.py startapp newapp

   # Add to INSTALLED_APPS in settings.py
   # Create models, views, URLs
   # Make and run migrations
   python manage.py makemigrations
   python manage.py migrate
   ```

3. **Database Changes**:

   ```bash
   # After model changes
   python manage.py makemigrations
   python manage.py migrate

   # Reset migrations (development only)
   python manage.py migrate appname zero
   rm appname/migrations/0*.py
   python manage.py makemigrations appname
   python manage.py migrate
   ```

---

Built with ❤️ using Django REST Framework
