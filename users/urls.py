from django.urls import path
from . import views

# url paths para sa user side yung nasa URLs like http://127.0.0.1:8000/maps/
urlpatterns = [
    path('', views.home, name='home'),
    path('maps/', views.maps_view, name='users_maps'),
]