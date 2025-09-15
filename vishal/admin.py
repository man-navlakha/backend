# your_app/admin.py

from django.contrib import admin
from .models import HiringRequest

# This line tells Django to show the HiringRequest model in the admin panel
admin.site.register(HiringRequest)