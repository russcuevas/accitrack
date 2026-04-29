from django.shortcuts import render, redirect
from django.contrib import messages
from .models import Report
from django.core.files.storage import FileSystemStorage
from django.utils import timezone

def submit_report(request):
    if request.method == 'POST':
        # Retrieve form data
        incident_date = request.POST.get('incident_date')
        
        # Auto-generate current time in Asia/Manila
        try:
            import zoneinfo
            tz = zoneinfo.ZoneInfo('Asia/Manila')
        except ImportError:
            import pytz
            tz = pytz.timezone('Asia/Manila')
            
        current_time = timezone.now().astimezone(tz).time()
        incident_time = current_time.strftime('%H:%M:%S')

        incident_type = request.POST.get('incident_type')
        if incident_type == 'Other':
            incident_type = request.POST.get('other_incident_type')
            
        latitude = request.POST.get('latitude')
        longitude = request.POST.get('longitude')
        location_address = request.POST.get('location_address')
        vehicles_involved = request.POST.get('vehicles_involved') or 0
        severity = request.POST.get('severity')
        description = request.POST.get('description')
        plate_numbers = request.POST.get('plate_numbers')
        injured_count = request.POST.get('injured_count') or 0
        reporter_name = request.POST.get('reporter_name')
        contact_number = request.POST.get('contact_number')
        email_address = request.POST.get('email_address')
        reporter_role = request.POST.get('reporter_role')

        # Clean empty lat/lon if they were not selected
        if not latitude: latitude = None
        if not longitude: longitude = None

        report = Report.objects.create(
            incident_date=incident_date,
            incident_time=incident_time,
            incident_type=incident_type,
            latitude=latitude,
            longitude=longitude,
            location_address=location_address,
            vehicles_involved=vehicles_involved,
            severity=severity,
            description=description,
            plate_numbers=plate_numbers,
            injured_count=injured_count,
            reporter_name=reporter_name,
            contact_number=contact_number,
            email_address=email_address,
            reporter_role=reporter_role,
            status='Pending'
        )

        # Handle Image Uploads
        images = request.FILES.getlist('evidence_images')
        fs = FileSystemStorage(location='media/report_images/')
        saved_images = []
        for image in images:
            filename = fs.save(image.name, image)
            file_url = fs.url(f'report_images/{filename}')
            saved_images.append(file_url)

        if saved_images:
            report.reported_images = saved_images
            report.save(update_fields=['reported_images'])

        messages.success(request, f'Report submitted successfully! Your case reference is {report.incident_number}.')
        return redirect('/#report-form')

    return redirect('/')
