from django.contrib import admin

# Register your models here.
# Add the correct import for Student if needed
from .models import Candidate
admin.site.register(Candidate)
