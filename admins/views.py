from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
from django.core.files.storage import FileSystemStorage
from admins.models import Admin, Announcement, Documentation, AuditTrail
from reports.models import Report
from django.contrib.auth.hashers import check_password
from django.contrib import messages

# helper para makuha ang session details ng naka-login na admin tulad ng pangalan at rank dinidisplay yan sa taas right side sa admin dashboard
def get_admin_context(request):
    """Helper to ensure admin session data is consistent"""
    admin_id = request.session.get('admin_id')
    admin_name = request.session.get('admin_name')
    admin_rank = request.session.get('admin_rank')
    
    if admin_id and not admin_rank:
        admin = Admin.objects.filter(id=admin_id).first()
        if admin:
            admin_rank = admin.rank
            request.session['admin_rank'] = admin_rank
            
    return {
        'admin_name': admin_name,
        'admin_rank': admin_rank,
    }

# para i-record sa database ang bawat pag process o galaw na ginagawa ng admin (Audit Trail)
def log_audit(request, action, description):
    user_str = "Unknown User"
    if request.session.get('admin_id'):
        admin_id = request.session.get('admin_id')
        admin = Admin.objects.filter(id=admin_id).first()
        if admin:
            user_str = f"{admin.rank} {admin.fullname}"
    
    # Get IP address
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
        
    AuditTrail.objects.create(
        user=user_str,
        action=action,
        description=description,
        ip_address=ip
    )

# dashboard view kung saan makikita ang overview ng mga reports, statistics, at maps
def dashboard(request):
    if not request.session.get('admin_id'):
        return redirect('/admins/login/')

    reports = Report.objects.all().order_by('-date_filed')
    total_cases = reports.count()
    open_cases = reports.filter(status='Pending').count()
    resolved_cases = reports.filter(status='Resolved').count()
    total_officers = Admin.objects.count()

    from django.db.models import Count
    import json

    valid_reports = reports.filter(status__in=['In Review', 'Resolved'])
    prone_areas = valid_reports.values('location_address').annotate(count=Count('id')).order_by('-count')[:5]

    incident_type_data = list(valid_reports.values('incident_type').annotate(count=Count('id')).order_by('-count'))
    severity_data = list(valid_reports.values('severity').annotate(count=Count('id')).order_by('severity'))

    pending_incidents = list(reports.filter(status='Pending', latitude__isnull=False, longitude__isnull=False).values(
        'incident_number', 'incident_type', 'severity', 'location_address', 'latitude', 'longitude'
    ))
    for p in pending_incidents:
        p['latitude'] = float(p['latitude'])
        p['longitude'] = float(p['longitude'])

    context = get_admin_context(request)
    context.update({
        'reports': reports,
        'total_cases': total_cases,
        'open_cases': open_cases,
        'resolved_cases': resolved_cases,
        'total_officers': total_officers,
        'prone_areas': prone_areas,
        'incident_type_data': json.dumps(incident_type_data),
        'severity_data': json.dumps(severity_data),
        'pending_incidents_data': json.dumps(pending_incidents),
    })

    return render(request, 'admins/dashboard.html', context)

# map view para sa admin para makita ang location ng mga reports at prone areas
def maps_view(request):
    if not request.session.get('admin_id'):
        return redirect('/admins/login/')
        
    from django.db.models import Count, Max
    from django.utils import timezone
    from datetime import timedelta
    import json
    
    now = timezone.localtime(timezone.now())
    today = now.date()
    yesterday = today - timedelta(days=1)
    last_month_start = today - timedelta(days=30)
    last_year_start = today - timedelta(days=365)
    
    def get_period_data(start_date, end_date=None, status_list=['In Review', 'Resolved']):
        qs = Report.objects.filter(
            latitude__isnull=False,
            longitude__isnull=False
        )
        if end_date:
            qs = qs.filter(date_filed__date__range=[start_date, end_date])
        else:
            qs = qs.filter(date_filed__date=start_date)
            
        if status_list:
            qs = qs.filter(status__in=status_list)
            
        # Group for map
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
                r['latest_time'] = r['latest_time'].strftime('%I:%M %p')
                
        return map_data

    # Datasets
    today_active = get_period_data(today, status_list=['In Review'])
    today_resolved = get_period_data(today, status_list=['Resolved'])
    yesterday_data = get_period_data(yesterday)
    month_data = get_period_data(last_month_start, today)
    year_data = get_period_data(last_year_start, today)
    
    # Custom Month/Year Filter
    sel_year = request.GET.get('year')
    sel_month = request.GET.get('month')
    custom_data = []
    is_custom = False
    
    if sel_year and sel_month:
        from datetime import date
        import calendar
        y, m = int(sel_year), int(sel_month)
        last_day = calendar.monthrange(y, m)[1]
        start_date = date(y, m, 1)
        end_date = date(y, m, last_day)
        custom_data = get_period_data(start_date, end_date)
        is_custom = True

    context = get_admin_context(request)
    context.update({
        'today_active_json': json.dumps(today_active),
        'today_resolved_json': json.dumps(today_resolved),
        'yesterday_data_json': json.dumps(yesterday_data),
        'month_data_json': json.dumps(month_data),
        'year_data_json': json.dumps(year_data),
        'custom_data_json': json.dumps(custom_data),
        'is_custom': is_custom,
        'sel_year': sel_year,
        'sel_month': sel_month,
        # Initial prone list
        'top_prone_list': sorted(month_data, key=lambda x: x['count'], reverse=True)[:5]
    })
    return render(request, 'admins/maps.html', context)

# listahan ng mga prone locations o mga lugar na madalas may aksidente
def prone_locations(request):
    if not request.session.get('admin_id'):
        return redirect('/admins/login/')
        
    reports = Report.objects.filter(status__in=['In Review', 'Resolved'])
    from django.db.models import Count
    prone_areas = reports.values('location_address').annotate(count=Count('id')).order_by('-count')
    
    context = get_admin_context(request)
    context.update({'prone_areas': prone_areas})
    
    return render(request, 'admins/prone_locations.html', context)

# para makita ang buong detalye ng isang specific na incident report
def report_detail(request, report_id):
    if not request.session.get('admin_id'):
        return redirect('/admins/login/')
        
    report = get_object_or_404(Report, id=report_id)
    
    context = get_admin_context(request)
    context.update({'report': report})
    
    return render(request, 'admins/report_detail.html', context)

# listahan ng lahat ng incident reports na pumasok sa system
def incident_reports(request):
    if not request.session.get('admin_id'):
        return redirect('/admins/login/')
        
    reports = Report.objects.all().order_by('-date_filed')
    
    context = get_admin_context(request)
    context.update({'reports': reports})
    
    return render(request, 'admins/incident_report.html', context)

# page para makita ang lahat ng mga admin at officer accounts
def accounts(request):
    if not request.session.get('admin_id'):
        return redirect('/admins/login/')
        
    officers = Admin.objects.all().order_by('fullname')
    
    context = get_admin_context(request)
    context.update({'officers': officers})
    return render(request, 'admins/accounts.html', context)

# para i-update ang status ng report (Accept, Resolve, Close, o Cancel)
def update_report_status(request, report_id, action):
    if not request.session.get('admin_id'):
        return redirect('/admins/login/')
        
    report = get_object_or_404(Report, id=report_id)
    
    if action == 'cancel':
        report.delete()
        messages.success(request, 'Report cancelled and deleted from database.')
        return redirect('/admins/dashboard/')

    if action == 'accept':
        report.status = 'In Review'
        messages.success(request, f'Report {report.incident_number} accepted and is now In Review.')
    elif action == 'resolve':
        report.status = 'Resolved'
        messages.success(request, f'Report {report.incident_number} marked as Resolved.')
    elif action == 'close':
        report.status = 'Closed'
        messages.success(request, f'Report {report.incident_number} marked as Closed.')
        
    report.save(update_fields=['status'])
    log_audit(request, 'CASE_EDITED', f"Modified case {report.incident_number} — updated status to '{report.status}'")
    return redirect(f'/admins/report/{report.id}/')

# login page para sa mga admin
def login(request):
    return render(request, 'admins/login.html')

# logic para sa pag-check ng login credentials ng admin
def login_admin(request):
    if request.method == "POST":
        email = request.POST.get("email")
        password = request.POST.get("password")

        try:
            admin = Admin.objects.get(email=email)

            if check_password(password, admin.password):
                # save session
                request.session['admin_id'] = admin.id
                request.session['admin_name'] = admin.fullname
                request.session['admin_rank'] = admin.rank

                log_audit(request, 'LOGIN', f"Logged in from {request.META.get('REMOTE_ADDR')}")
                messages.success(request, f'WELCOME ADMIN: {admin.fullname}', extra_tags='welcome')
                return redirect('/admins/dashboard/')
            else:
                return render(request, 'admins/login.html', {
                    'error': 'Invalid password'
                })

        except Admin.DoesNotExist:
            return render(request, 'admins/login.html', {
                'error': 'User not found'
            })

    return render(request, 'admins/login.html')

# para mag-logout at i-clear ang session ng admin
def logout_admin(request):
    request.session.flush()
    messages.success(request, 'Logout successful')
    return redirect('/admins/login/')

from django.contrib.auth.hashers import make_password

# para magdagdag ng bagong officer account sa system
def add_officer(request):
    if not request.session.get('admin_id'):
        return redirect('/admins/login/')
        
    if request.method == 'POST':
        fullname = request.POST.get('fullname')
        email = request.POST.get('email')
        rank = request.POST.get('rank')
        password = request.POST.get('password')
        
        # Check if email exists
        if Admin.objects.filter(email=email).exists():
            messages.error(request, 'Email already exists.')
            return redirect('/admins/accounts/')
            
        Admin.objects.create(
            fullname=fullname,
            email=email,
            rank=rank,
            password=make_password(password)
        )
        log_audit(request, 'ACCOUNT_UPDATED', f"Created new officer account: {fullname}")
        messages.success(request, 'Officer added successfully.')
    return redirect('/admins/accounts/')

# para i-edit o i-update ang detalye ng existing na officer account
def edit_officer(request, officer_id):
    if not request.session.get('admin_id'):
        return redirect('/admins/login/')
        
    officer = get_object_or_404(Admin, id=officer_id)
    
    if request.method == 'POST':
        officer.fullname = request.POST.get('fullname')
        officer.email = request.POST.get('email')
        officer.rank = request.POST.get('rank')
        
        password = request.POST.get('password')
        if password:
            officer.password = make_password(password)
            
        officer.save()
        messages.success(request, 'Officer updated successfully.')
        
    return redirect('/admins/accounts/')

# listahan ng mga announcements na ginawa para sa user side
def announcement_list(request):
    if not request.session.get('admin_id'):
        return redirect('/admins/login/')
    
    announcements = Announcement.objects.all().order_by('-date')
    context = get_admin_context(request)
    context.update({'announcements': announcements})
    return render(request, 'admins/announcement.html', context)

# para gumawa ng bagong announcement
def add_announcement(request):
    if not request.session.get('admin_id'):
        return redirect('/admins/login/')
        
    if request.method == 'POST':
        category = request.POST.get('category')
        title = request.POST.get('title')
        description = request.POST.get('description')
        
        Announcement.objects.create(
            category=category,
            title=title,
            description=description
        )
        log_audit(request, 'ANNOUNCEMENT_CREATED', f"Created new announcement: {title}")
        messages.success(request, 'Announcement added successfully.')
    return redirect('/admins/announcement/')

# para i-edit ang nagawang announcement
def edit_announcement(request, announcement_id):
    if not request.session.get('admin_id'):
        return redirect('/admins/login/')
        
    announcement = get_object_or_404(Announcement, id=announcement_id)
    
    if request.method == 'POST':
        announcement.category = request.POST.get('category')
        announcement.title = request.POST.get('title')
        announcement.description = request.POST.get('description')
        announcement.save()
        messages.success(request, 'Announcement updated successfully.')
        
    return redirect('/admins/announcement/')

# para magbura ng announcement
def delete_announcement(request, announcement_id):
    if not request.session.get('admin_id'):
        return redirect('/admins/login/')
        
    announcement = get_object_or_404(Announcement, id=announcement_id)
    announcement.delete()
    messages.success(request, 'Announcement deleted successfully.')
    return redirect('/admins/announcement/')

# listahan ng mga documentation files tulad ng photo at sketch para sa bawat case
def documentation_list(request):
    if not request.session.get('admin_id'):
        return redirect('/admins/login/')
    
    docs = Documentation.objects.all().order_by('-date')
    reports = Report.objects.all().order_by('-date_filed')
    context = get_admin_context(request)
    context.update({
        'docs': docs,
        'reports': reports
    })
    return render(request, 'admins/documentation.html', context)

# para mag-upload ng mga documentation files para sa isang incident report
def upload_document(request):
    if not request.session.get('admin_id'):
        return redirect('/admins/login/')
        
    if request.method == 'POST':
        report_id = request.POST.get('case_id')
        doc_type = request.POST.get('type')
        description = request.POST.get('description')
        uploaded_file = request.FILES.get('file')
        additional_files = request.FILES.getlist('additional_images')
        
        admin_id = request.session.get('admin_id')
        admin = Admin.objects.get(id=admin_id)
        
        report = get_object_or_404(Report, id=report_id)
        
        # Save additional images
        image_urls = []
        fs = FileSystemStorage(location='media/documentation/images/')
        for img in additional_files:
            filename = fs.save(img.name, img)
            image_urls.append(f"/media/documentation/images/{filename}")
        
        doc = Documentation(
            report=report,
            type=doc_type,
            description=description,
            uploaded_by=f"{admin.rank} {admin.fullname}",
            file=uploaded_file
        )
        doc.additional_images = image_urls
        doc.save()
        
        log_audit(request, 'DOC_UPLOADED', f"Uploaded {uploaded_file.name} to case {report.incident_number}")
        messages.success(request, 'Document and images uploaded successfully.')
    return redirect('/admins/documentation/')

# para magbura ng documentation file
def delete_document(request, doc_id):
    if not request.session.get('admin_id'):
        return redirect('/admins/login/')
    
    doc = get_object_or_404(Documentation, id=doc_id)
    case_num = doc.report.incident_number
    doc.delete()
    log_audit(request, 'DOC_DELETED', f"Deleted document from case {case_num}")
    messages.success(request, 'Document deleted successfully.')
    return redirect('/admins/documentation/')

# API para makuha ang case details para sa documentation modal
def get_case_details(request, report_id):
    report = get_object_or_404(Report, id=report_id)
    data = {
        'incident_number': report.incident_number,
        'incident_type': report.incident_type,
        'location': report.location_address,
        'date': report.incident_date.strftime('%Y-%m-%d'),
        'reporter': report.reporter_name,
        'status': report.status,
    }
    return JsonResponse(data)

# para makita ang listahan ng Audit Trail o history ng mga ginawa ng admin
def audit_trail_list(request):
    if not request.session.get('admin_id'):
        return redirect('/admins/login/')
    
    audits = AuditTrail.objects.all().order_by('-timestamp')
    context = get_admin_context(request)
    context.update({'audits': audits})
    return render(request, 'admins/audit_trails.html', context)