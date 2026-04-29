from django.urls import path
from . import views

app_name = 'admins'

urlpatterns = [
    path('dashboard/', views.dashboard, name='dashboard'),
    path('accounts/', views.accounts, name='accounts'),
    path('login/', views.login, name='login'),
    path('login_admin/', views.login_admin, name='login_admin'),
    path('logout/', views.logout_admin, name='logout'), 
    path('update_report_status/<int:report_id>/<str:action>/', views.update_report_status, name='update_report_status'),
    path('report/<int:report_id>/', views.report_detail, name='report_detail'),
    path('incident_reports/', views.incident_reports, name='incident_reports'),
    path('prone/locations/', views.prone_locations, name='prone_locations'),
    path('accounts/add/', views.add_officer, name='add_officer'),
    path('accounts/edit/<int:officer_id>/', views.edit_officer, name='edit_officer'),
]