import uuid
from django.conf import settings
from django.db import models


class BookingStatus(models.TextChoices):
    PENDING = "PENDING"
    CONFIRMED = "CONFIRMED"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"


class Booking(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="bookings",
    )
    test = models.ForeignKey(
        "centres.DiagnosticTest",
        on_delete=models.PROTECT,
        related_name="bookings",
    )
    centre = models.ForeignKey(
        "centres.DiagnosticCentre",
        on_delete=models.PROTECT,
        related_name="bookings",
    )
    appointment_datetime = models.DateTimeField()
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(
        max_length=10,
        choices=BookingStatus.choices,
        default=BookingStatus.PENDING,
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "bookings"
        ordering = ["-created_at"]

    def __str__(self):
        return f"Booking {self.id} - {self.status}"
