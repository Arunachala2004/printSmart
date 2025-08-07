"""
URL configuration for PrintSmart backend project.

This module defines the main URL patterns for the PrintSmart backend.
"""

from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.http import JsonResponse


def health_check(request):
    """
    Health check endpoint for monitoring.
    """
    return JsonResponse({
        'status': 'healthy',
        'service': 'PrintSmart Backend',
        'timestamp': '2025-08-06T00:00:00Z'
    })


urlpatterns = [
    # Admin panel
    path('admin/', admin.site.urls),
    
    # Web frontend
    path('', include('web.urls')),
    
    # Payments
    path('payments/', include('payments.urls')),
    
    # Print Jobs
    path('print-jobs/', include('print_jobs.urls')),
    
    # Health check
    path('health/', health_check, name='health-check'),
]

# Serve media files in development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
