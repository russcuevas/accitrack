from django.urls import path
from . import views

# ito ay para sa report side yung URL ay http://127.0.0.1:8000/submit/ pero di na ito nakikita kasi pag ka submit direct uli sa home hide lang
urlpatterns = [
    path('submit/', views.submit_report, name='submit_report'),
]
