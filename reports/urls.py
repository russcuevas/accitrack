from django.urls import path
from . import views

urlpatterns = [
    path('submit/', views.submit_report, name='submit_report'),
]
