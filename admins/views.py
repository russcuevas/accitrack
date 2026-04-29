from django.shortcuts import render, redirect, get_object_or_404
from admins.models import Admin
from reports.models import Report
from django.contrib.auth.hashers import check_password
from django.contrib import messages

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

def prone_locations(request):
    if not request.session.get('admin_id'):
        return redirect('/admins/login/')
        
    reports = Report.objects.filter(status__in=['In Review', 'Resolved'])
    from django.db.models import Count
    prone_areas = reports.values('location_address').annotate(count=Count('id')).order_by('-count')
    
    context = get_admin_context(request)
    context.update({'prone_areas': prone_areas})
    
    return render(request, 'admins/prone_locations.html', context)

def report_detail(request, report_id):
    if not request.session.get('admin_id'):
        return redirect('/admins/login/')
        
    report = get_object_or_404(Report, id=report_id)
    
    context = get_admin_context(request)
    context.update({'report': report})
    
    return render(request, 'admins/report_detail.html', context)

def incident_reports(request):
    if not request.session.get('admin_id'):
        return redirect('/admins/login/')
        
    reports = Report.objects.all().order_by('-date_filed')
    
    context = get_admin_context(request)
    context.update({'reports': reports})
    
    return render(request, 'admins/incident_report.html', context)

def accounts(request):
    if not request.session.get('admin_id'):
        return redirect('/admins/login/')
        
    officers = Admin.objects.all().order_by('fullname')
    
    context = get_admin_context(request)
    context.update({'officers': officers})
    return render(request, 'admins/accounts.html', context)

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
    return redirect(f'/admins/report/{report.id}/')

def login(request):
    return render(request, 'admins/login.html')

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

def logout_admin(request):
    request.session.flush()
    messages.success(request, 'Logout successful')
    return redirect('/admins/login/')

from django.contrib.auth.hashers import make_password

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
        messages.success(request, 'Officer added successfully.')
    return redirect('/admins/accounts/')

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