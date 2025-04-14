"""
URL configuration for collegemantra project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include  #  added
from users import views as users_views  # Adjust this import if the home view belongs to cm_app

urlpatterns = [
    path('admin/', admin.site.urls),

    # Main homepage route handled by users
    path('', include('users.urls')),

    # Candidate-related URLs
    path('candidates/', include(('candidates.urls', 'candidates'), namespace='candidates')),

    # College-related URLs
    path('colleges/', include(('colleges.urls', 'colleges'), namespace='colleges')),

    # Home route (if defined in users)
    path('', users_views.home, name='home'),  # This is redundant if already included in users.urls

]
