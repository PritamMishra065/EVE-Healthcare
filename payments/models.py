import uuid
from django.db import models


class PaymentStatus(models.TextChoices):
    SUCCESS = "SUCCESS"
    FAILED = "FAILED"


class Payment(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    booking = models.ForeignKey(
        "bookings.Booking",
        on_delete=models.PROTECT,
        related_name="payments",
    )
    transaction_id = models.CharField(max_length=100, unique=True)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=10, choices=PaymentStatus.choices)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "payments"
        ordering = ["-created_at"]

    def __str__(self):
        return f"Payment {self.transaction_id} - {self.status}"


class WebhookEvent(models.Model):
    """Tracks processed webhook events to ensure idempotency."""
    event_id = models.CharField(max_length=100, primary_key=True)
    processed_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "webhook_events"
