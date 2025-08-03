"""
URL configuration for PrintSmart backend project.

This module defines the main URL patterns for the PrintSmart backend API.
All API endpoints are prefixed with /api/ and organized by functionality.
"""

from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.http import JsonResponse
from rest_framework.decorators import api_view
from rest_framework.response import Response


@api_view(['GET'])
def api_root(request):
    """
    API Root endpoint providing available endpoints information.
    """
    return Response({
        'message': 'Welcome to PrintSmart Backend API',
        'version': '1.0.0',
        'endpoints': {
            'authentication': '/api/auth/',
            'users': '/api/users/',
            'files': '/api/files/',
            'print_jobs': '/api/print-jobs/',
            'payments': '/api/payments/',
            'admin_panel': '/admin/',
        },
        'documentation': '/api/docs/',
        'status': 'operational'
    })


def health_check(request):
    """
    Health check endpoint for monitoring.
    """
    return JsonResponse({
        'status': 'healthy',
        'service': 'PrintSmart Backend',
        'timestamp': '2025-08-02T23:07:00Z'
    })


urlpatterns = [
    # Admin panel
    path('admin/', admin.site.urls),
    
    # API root
    path('api/', api_root, name='api-root'),
    
    # Health check
    path('health/', health_check, name='health-check'),
    
    # API endpoints (to be implemented)
    # path('api/auth/', include('users.urls')),
    # path('api/users/', include('users.api_urls')),
    # path('api/files/', include('files.urls')),
    # path('api/print-jobs/', include('print_jobs.urls')),
    # path('api/payments/', include('payments.urls')),
]

# Serve media files in development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
