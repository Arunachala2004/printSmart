from django.urls import path
from . import views

app_name = 'print_jobs'

urlpatterns = [
    path('', views.job_list, name='list'),
    path('create/', views.create_job, name='create'),
    path('<uuid:job_id>/', views.job_detail, name='detail'),
    path('<uuid:job_id>/cancel/', views.cancel_job, name='cancel'),
    path('<uuid:job_id>/status/', views.job_status_update, name='status_update'),
]
