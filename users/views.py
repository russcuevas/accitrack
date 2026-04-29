from django.shortcuts import render
from reports.models import Report
from django.db.models import Q

def home(request):
    total_incidents = Report.objects.count()
    pending_incidents = Report.objects.filter(status='Pending').count()
    active_incidents = Report.objects.filter(status='In Review').count()
    resolved_incidents = Report.objects.filter(status='Resolved').count()
    
    search_query = request.GET.get('q', '')
    searched_reports = []
    
    if search_query:
        searched_reports = Report.objects.filter(
            Q(incident_number__icontains=search_query) | 
            Q(location_address__icontains=search_query)
        ).order_by('-date_filed')
    
    context = {
        'total_incidents': total_incidents,
        'pending_incidents': pending_incidents,
        'active_incidents': active_incidents,
        'resolved_incidents': resolved_incidents,
        'search_query': search_query,
        'searched_reports': searched_reports,
    }
    return render(request, 'users/home.html', context)