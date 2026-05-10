from django.db import models
from django.contrib.auth.hashers import make_password

# para magawa ang table na admins_admin table sa database xampp

class Admin(models.Model):
    rank = models.CharField(max_length=50)
    fullname = models.CharField(max_length=100)
    email = models.EmailField(unique=True)
    password = models.CharField(max_length=128)

    def save(self, *args, **kwargs):
        if not self.password.startswith('pbkdf2_'):
            self.password = make_password(self.password)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.fullname

# para magawa ang table na admins_announcement table sa database xampp

class Announcement(models.Model):
    CATEGORY_CHOICES = [
        ('SAFETY ADVISORY', 'Safety Advisory'),
        ('SYSTEM UPDATE', 'System Update'),
        ('REMINDER', 'Reminder'),
    ]
    category = models.CharField(max_length=50, choices=CATEGORY_CHOICES)
    title = models.CharField(max_length=255)
    description = models.TextField()
    date = models.DateField(auto_now_add=True)

    def __str__(self):
        return self.title

# para magawa ang table na admins_documentation table sa database xampp

class Documentation(models.Model):
    TYPE_CHOICES = [
        ('PHOTO', 'Photo'),
        ('SKETCH', 'Sketch'),
        ('MEDICAL', 'Medical'),
        ('REPORT', 'Report'),
    ]
    doc_id = models.CharField(max_length=20, unique=True, blank=True)
    report = models.ForeignKey('reports.Report', on_delete=models.CASCADE, related_name='documentations')
    type = models.CharField(max_length=20, choices=TYPE_CHOICES)
    description = models.TextField()
    uploaded_by = models.CharField(max_length=100)
    date = models.DateField(auto_now_add=True)
    file = models.FileField(upload_to='documentation/')
    additional_images = models.JSONField(default=list, blank=True)
    
    def save(self, *args, **kwargs):
        if not self.doc_id:
            last_doc = Documentation.objects.all().order_by('id').last()
            if not last_doc:
                self.doc_id = 'DOC-0001'
            else:
                try:
                    doc_int = int(last_doc.doc_id.split('-')[1])
                    self.doc_id = 'DOC-' + str(doc_int + 1).zfill(4)
                except (IndexError, ValueError):
                    self.doc_id = 'DOC-0001'
        super(Documentation, self).save(*args, **kwargs)

    def __str__(self):
        return self.doc_id

# para magawa ang table na admins_audittrail table para sa history ng mga galaw ng admin
class AuditTrail(models.Model):
    ACTION_CHOICES = [
        ('CASE_EDITED', 'Case edited'),
        ('DOC_UPLOADED', 'Document uploaded'),
        ('LOGIN', 'Login'),
        ('CASE_CREATED', 'New case created'),
        ('ACCOUNT_UPDATED', 'Account updated'),
        ('ANNOUNCEMENT_CREATED', 'Announcement created'),
        ('DOC_DELETED', 'Document deleted'),
    ]
    user = models.CharField(max_length=150)
    action = models.CharField(max_length=50, choices=ACTION_CHOICES)
    description = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)

    def __str__(self):
        return f"{self.user} - {self.action} - {self.timestamp}"