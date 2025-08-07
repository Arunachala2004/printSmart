from django.urls import path
from . import views

app_name = 'web'

urlpatterns = [
    # Home and Auth
    path('', views.home, name='home'),
    path('login/', views.login_view, name='login'),
    path('register/', views.register_view, name='register'),
    path('logout/', views.logout_view, name='logout'),
    
    # Dashboard
    path('dashboard/', views.dashboard, name='dashboard'),
    
    # Profile
    path('profile/', views.profile_view, name='profile'),
    
    # Files
    path('files/', views.files_view, name='files'),
    path('files/<uuid:file_id>/', views.file_detail_view, name='file_detail'),
    path('upload/', views.upload_file_view, name='upload_file'),
    path('files/<uuid:file_id>/delete/', views.delete_file_view, name='delete_file'),
    path('files/<uuid:file_id>/print/', views.print_file_view, name='print_file'),
    
    # Print Jobs
    path('print-jobs/', views.print_jobs_view, name='print_jobs'),
    path('print-jobs/<uuid:job_id>/cancel/', views.cancel_print_job, name='cancel_print_job'),
    
    # Printers
    path('printers/', views.printers_view, name='printers'),
    path('printers/<uuid:printer_id>/select/', views.select_printer, name='select_printer'),
    
    # Wallet and Payments
    path('wallet/', views.wallet_view, name='wallet'),
    path('wallet/add-money/', views.add_money, name='add_money'),
    
    # Admin
    path('admin-dashboard/', views.admin_dashboard, name='admin_dashboard'),
]