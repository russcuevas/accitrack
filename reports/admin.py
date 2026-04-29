from django.contrib import admin
from .models import Report

@admin.register(Report)
class ReportAdmin(admin.ModelAdmin):
    list_display = ('incident_number', 'incident_date', 'incident_type', 'status', 'reporter_name')
