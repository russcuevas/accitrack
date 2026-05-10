
from django.shortcuts import render
from reports.models import Report
from admins.models import Announcement
from django.db.models import Q, Count, Max
from django.utils import timezone
from datetime import timedelta, date
import json


# home page para idisplay data sa user side yung mga nangyayaring aksidente at mga announcements 
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
    
    announcements = Announcement.objects.all().order_by('-date')[:3]
    all_announcements = Announcement.objects.all().order_by('-date')
    
    context = {
        'total_incidents': total_incidents,
        'pending_incidents': pending_incidents,
        'active_incidents': active_incidents,
        'resolved_incidents': resolved_incidents,
        'search_query': search_query,
        'searched_reports': searched_reports,
        'announcements': announcements,
        'all_announcements': all_announcements,
    }
    return render(request, 'users/home.html', context)


# map view para idisplay sa user side yung mga nangyayaring aksidente at mga prone areas
def maps_view(request):
    now = timezone.localtime(timezone.now())
    today = now.date()
    yesterday = today - timedelta(days=1)
    last_month_start = today - timedelta(days=30)
    last_year_start = today - timedelta(days=365)

    def get_period_data(start_date, end_date=None, status_list=['In Review', 'Resolved']):
        qs = Report.objects.filter(latitude__isnull=False, longitude__isnull=False)
        if end_date:
            qs = qs.filter(date_filed__date__range=[start_date, end_date])
        else:
            qs = qs.filter(date_filed__date=start_date)
        if status_list:
            qs = qs.filter(status__in=status_list)
        map_data = list(qs.values('location_address').annotate(
            count=Count('id'),
            lat=Max('latitude'),
            lng=Max('longitude'),
            latest_type=Max('incident_type'),
            latest_time=Max('incident_time')
        ))
        for r in map_data:
            r['lat'] = float(r['lat'])
            r['lng'] = float(r['lng'])
            if r.get('latest_time'):
                r['latest_time'] = r['latest_time'].strftime('%I:%M %p') if hasattr(r['latest_time'], 'strftime') else str(r['latest_time'])
        return map_data

    today_active = get_period_data(today, status_list=['In Review'])
    today_resolved = get_period_data(today, status_list=['Resolved'])
    yesterday_data = get_period_data(yesterday)
    month_data = get_period_data(last_month_start, today)
    year_data = get_period_data(last_year_start, today)

    sel_year = request.GET.get('year')
    sel_month = request.GET.get('month')
    custom_data = []
    is_custom = False
    if sel_year and sel_month:
        import calendar
        y, m = int(sel_year), int(sel_month)
        last_day = calendar.monthrange(y, m)[1]
        start_date = date(y, m, 1)
        end_date = date(y, m, last_day)
        custom_data = get_period_data(start_date, end_date)
        is_custom = True

    context = {
        'today_active_json': json.dumps(today_active),
        'today_resolved_json': json.dumps(today_resolved),
        'yesterday_data_json': json.dumps(yesterday_data),
        'month_data_json': json.dumps(month_data),
        'year_data_json': json.dumps(year_data),
        'custom_data_json': json.dumps(custom_data),
        'is_custom': is_custom,
        'sel_year': sel_year,
        'sel_month': sel_month,
        'top_prone_list': sorted(month_data, key=lambda x: x['count'], reverse=True)[:5]
    }
    return render(request, 'users/maps.html', context)