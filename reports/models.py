from django.db import models

# para magawa ang table na reports_report table sa database xampp
class Report(models.Model):
    STATUS_CHOICES = [
        ('Pending', 'Pending'),
        ('In Review', 'In Review'),
        ('Closed', 'Closed'),
        ('Resolved', 'Resolved'),
    ]

    SEVERITY_CHOICES = [
        ('Critical', 'Critical'),
        ('High', 'High'),
        ('Medium', 'Medium'),
        ('Low', 'Low'),
    ]

    # Incident Details
    incident_date = models.DateField()
    incident_time = models.TimeField()
    incident_type = models.CharField(max_length=100)
    latitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    longitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    location_address = models.CharField(max_length=255)
    vehicles_involved = models.IntegerField(default=0)

    # Severity Level
    severity = models.CharField(max_length=20, choices=SEVERITY_CHOICES)

    # Description
    description = models.TextField()
    plate_numbers = models.CharField(max_length=255, blank=True, null=True)
    injured_count = models.IntegerField(default=0)

    # Reporter Info
    reporter_name = models.CharField(max_length=100)
    contact_number = models.CharField(max_length=50)
    email_address = models.EmailField(blank=True, null=True)
    reporter_role = models.CharField(max_length=100)

    # Status Tracking
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='Pending')
    incident_number = models.CharField(max_length=50, unique=True, blank=True, null=True)
    reported_images = models.JSONField(default=list, blank=True)
    date_filed = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.incident_number or 'Draft'} - {self.incident_type} at {self.location_address}"

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        if not self.incident_number:
            self.incident_number = f"#INCIDENT-{self.id}"
            super().save(update_fields=['incident_number'])

