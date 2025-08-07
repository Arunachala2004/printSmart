#!/usr/bin/env python3
print("Python is working!")
print("Testing Django import...")

try:
    import django
    print(f"Django version: {django.get_version()}")
    
    # Test basic Django setup
    import os
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'printsmart_backend.settings')
    django.setup()
    
    print("Django setup successful!")
    
    # Test model imports
    from users.models import User
    from files.models import File
    from print_jobs.models import PrintJob
    print("Model imports successful!")
    
    # Test URL resolution
    from django.urls import reverse
    try:
        home_url = reverse('web:home')
        print(f"Home URL resolved: {home_url}")
    except Exception as e:
        print(f"URL resolution error: {e}")
    
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()
