#!/usr/bin/env python
import os
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'printsmart_backend.settings')
django.setup()

def test_dashboard_urls():
    """Test all dashboard-related URLs"""
    from django.urls import reverse
    from django.test import Client
    from users.models import User
    
    try:
        # Create test client
        client = Client()
        
        # Get admin user
        user = User.objects.get(username='admin')
        
        # Login
        client.force_login(user)
        
        # Test dashboard URL
        dashboard_url = reverse('web:dashboard')
        response = client.get(dashboard_url)
        
        if response.status_code == 200:
            print("✅ Dashboard loads successfully!")
            print(f"Dashboard URL: {dashboard_url}")
        else:
            print(f"❌ Dashboard failed with status {response.status_code}")
            print(f"Response content: {response.content[:500]}")
        
        # Test URL patterns
        urls_to_test = [
            'web:home',
            'web:files', 
            'web:printers',
            'web:print_jobs',
            'web:wallet',
            'web:upload_file',
        ]
        
        print("\nTesting URL patterns:")
        for url_name in urls_to_test:
            try:
                url = reverse(url_name)
                print(f"✅ {url_name}: {url}")
            except Exception as e:
                print(f"❌ {url_name}: {e}")
        
        print("\n🎉 Dashboard test completed!")
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    test_dashboard_urls()
