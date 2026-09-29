from django.contrib import admin

from .models import Booking


@admin.register(Booking)
class BookingAdmin(admin.ModelAdmin):
    list_display = ["id", "user", "test", "centre", "status", "appointment_datetime"]
    list_filter = ["status"]
    readonly_fields = ["id", "created_at", "updated_at"]
