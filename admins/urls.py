from django.urls import path
from . import views

app_name = 'admins'

# mga url paths para sa admin portal tulad ng dashboard, accounts, at reports
urlpatterns = [
    path('dashboard/', views.dashboard, name='dashboard'),
    path('maps/', views.maps_view, name='maps'),
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
    path('announcement/', views.announcement_list, name='announcement_list'),
    path('announcement/add/', views.add_announcement, name='add_announcement'),
    path('announcement/edit/<int:announcement_id>/', views.edit_announcement, name='edit_announcement'),
    path('announcement/delete/<int:announcement_id>/', views.delete_announcement, name='delete_announcement'),
    path('documentation/', views.documentation_list, name='documentation_list'),
    path('documentation/upload/', views.upload_document, name='upload_document'),
    path('documentation/delete/<int:doc_id>/', views.delete_document, name='delete_document'),
    path('documentation/get_case/<int:report_id>/', views.get_case_details, name='get_case_details'),
    path('audit_trail/', views.audit_trail_list, name='audit_trail_list'),
]