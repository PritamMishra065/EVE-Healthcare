from decimal import Decimal
from django.test import TestCase
from django.contrib.auth import get_user_model
from django.utils import timezone
from rest_framework.test import APIClient
from rest_framework import status

from centres.models import DiagnosticCentre, DiagnosticTest
from bookings.models import Booking, BookingStatus
from .models import Payment, PaymentStatus, WebhookEvent

User = get_user_model()


class PaymentTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            email="pay@example.com", username="payer", password="Pass123!"
        )
        self.centre = DiagnosticCentre.objects.create(name="Centre", location="Delhi")
        self.test = DiagnosticTest.objects.create(
            name="CBC", centre=self.centre, price=Decimal("500.00")
        )
        self.booking = Booking.objects.create(
            user=self.user, test=self.test, centre=self.centre,
            appointment_datetime=timezone.now() + timezone.timedelta(days=1),
            amount=Decimal("500.00"),
        )
        self.client.force_authenticate(user=self.user)

    def test_initiate_payment(self):
        resp = self.client.post("/api/payments/", {"booking_id": str(self.booking.id)})
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)
        self.assertIn(resp.data["status"], ["SUCCESS", "FAILED"])
        self.booking.refresh_from_db()
        expected = BookingStatus.CONFIRMED if resp.data["status"] == "SUCCESS" else BookingStatus.FAILED
        self.assertEqual(self.booking.status, expected)

    def test_payment_for_non_pending_booking(self):
        self.booking.status = BookingStatus.CONFIRMED
        self.booking.save()
        resp = self.client.post("/api/payments/", {"booking_id": str(self.booking.id)})
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)

    def test_payment_invalid_booking(self):
        resp = self.client.post("/api/payments/", {
            "booking_id": "00000000-0000-0000-0000-000000000000"
        })
        self.assertEqual(resp.status_code, status.HTTP_404_NOT_FOUND)

    def test_payment_other_users_booking(self):
        other = User.objects.create_user(email="o@e.com", username="o", password="Pass123!")
        booking = Booking.objects.create(
            user=other, test=self.test, centre=self.centre,
            appointment_datetime=timezone.now() + timezone.timedelta(days=1),
            amount=Decimal("500.00"),
        )
        resp = self.client.post("/api/payments/", {"booking_id": str(booking.id)})
        self.assertEqual(resp.status_code, status.HTTP_404_NOT_FOUND)


class WebhookTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        user = User.objects.create_user(
            email="wh@example.com", username="whuser", password="Pass123!"
        )
        centre = DiagnosticCentre.objects.create(name="Centre", location="Delhi")
        test = DiagnosticTest.objects.create(
            name="CBC", centre=centre, price=Decimal("500.00")
        )
        self.booking = Booking.objects.create(
            user=user, test=test, centre=centre,
            appointment_datetime=timezone.now() + timezone.timedelta(days=1),
            amount=Decimal("500.00"),
        )
        self.payment = Payment.objects.create(
            booking=self.booking, transaction_id="txn_test123",
            amount=Decimal("500.00"), status=PaymentStatus.FAILED,
        )

    def test_webhook_success(self):
        resp = self.client.post("/api/payments/webhook/", {
            "event_id": "evt_001",
            "transaction_id": "txn_test123",
            "status": "SUCCESS",
        })
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.payment.refresh_from_db()
        self.assertEqual(self.payment.status, "SUCCESS")
        self.booking.refresh_from_db()
        self.assertEqual(self.booking.status, BookingStatus.CONFIRMED)

    def test_webhook_idempotency(self):
        self.client.post("/api/payments/webhook/", {
            "event_id": "evt_dup",
            "transaction_id": "txn_test123",
            "status": "SUCCESS",
        })
        resp = self.client.post("/api/payments/webhook/", {
            "event_id": "evt_dup",
            "transaction_id": "txn_test123",
            "status": "SUCCESS",
        })
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertIn("already processed", resp.data["detail"])
        self.assertEqual(WebhookEvent.objects.count(), 1)

    def test_webhook_unknown_transaction(self):
        resp = self.client.post("/api/payments/webhook/", {
            "event_id": "evt_unknown",
            "transaction_id": "txn_nonexistent",
            "status": "SUCCESS",
        })
        self.assertEqual(resp.status_code, status.HTTP_404_NOT_FOUND)

    def test_webhook_invalid_payload(self):
        resp = self.client.post("/api/payments/webhook/", {
            "event_id": "evt_bad",
        })
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)

    def test_webhook_invalid_status(self):
        resp = self.client.post("/api/payments/webhook/", {
            "event_id": "evt_inv",
            "transaction_id": "txn_test123",
            "status": "INVALID",
        })
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)
