from django.urls import path
from . import views

app_name = 'users'  # This sets the namespace for your app

urlpatterns = [
    path('', views.home, name='home'),
    path('about/', views.about, name='about'),
    path('important-dates/', views.important_dates, name='important_dates'),
    path('seat_matrix/', views.seat_matrix, name='seat_matrix'),
    path('announcements/', views.announcements, name='announcements'),
    path('register/', views.option, name='register'),  # Named 'register'
    path('contact/', views.contact, name='contact'),
]