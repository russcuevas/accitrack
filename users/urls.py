from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('maps/', views.maps_view, name='users_maps'),
]