from decimal import Decimal
from django.test import TestCase
from django.contrib.auth import get_user_model
from django.utils import timezone
from rest_framework.test import APIClient
from rest_framework import status

from centres.models import DiagnosticCentre, DiagnosticTest
from .models import Booking, BookingStatus

User = get_user_model()


class BookingTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            email="patient@example.com", username="patient", password="Pass123!"
        )
        self.other_user = User.objects.create_user(
            email="other@example.com", username="other", password="Pass123!"
        )
        self.centre = DiagnosticCentre.objects.create(name="Centre A", location="Delhi")
        self.centre_b = DiagnosticCentre.objects.create(name="Centre B", location="Mumbai")
        self.test = DiagnosticTest.objects.create(
            name="CBC", centre=self.centre, price=Decimal("500.00")
        )
        self.inactive_test = DiagnosticTest.objects.create(
            name="Old Test", centre=self.centre, price=Decimal("300.00"), is_active=False
        )
        self.client.force_authenticate(user=self.user)
        self.future = (timezone.now() + timezone.timedelta(days=1)).isoformat()

    def test_create_booking(self):
        resp = self.client.post("/api/bookings/", {
            "test": str(self.test.id),
            "centre": str(self.centre.id),
            "appointment_datetime": self.future,
        })
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)
        self.assertEqual(resp.data["status"], "PENDING")
        self.assertEqual(resp.data["amount"], "500.00")

    def test_create_booking_past_datetime(self):
        past = (timezone.now() - timezone.timedelta(days=1)).isoformat()
        resp = self.client.post("/api/bookings/", {
            "test": str(self.test.id),
            "centre": str(self.centre.id),
            "appointment_datetime": past,
        })
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)

    def test_create_booking_test_wrong_centre(self):
        resp = self.client.post("/api/bookings/", {
            "test": str(self.test.id),
            "centre": str(self.centre_b.id),
            "appointment_datetime": self.future,
        })
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)

    def test_create_booking_inactive_test(self):
        resp = self.client.post("/api/bookings/", {
            "test": str(self.inactive_test.id),
            "centre": str(self.centre.id),
            "appointment_datetime": self.future,
        })
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)

    def test_list_own_bookings_only(self):
        Booking.objects.create(
            user=self.user, test=self.test, centre=self.centre,
            appointment_datetime=self.future, amount=Decimal("500.00"),
        )
        Booking.objects.create(
            user=self.other_user, test=self.test, centre=self.centre,
            appointment_datetime=self.future, amount=Decimal("500.00"),
        )
        resp = self.client.get("/api/bookings/")
        self.assertEqual(resp.data["count"], 1)

    def test_cancel_booking(self):
        booking = Booking.objects.create(
            user=self.user, test=self.test, centre=self.centre,
            appointment_datetime=self.future, amount=Decimal("500.00"),
        )
        resp = self.client.post(f"/api/bookings/{booking.id}/cancel/")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resp.data["status"], "CANCELLED")

    def test_cancel_already_failed(self):
        booking = Booking.objects.create(
            user=self.user, test=self.test, centre=self.centre,
            appointment_datetime=self.future, amount=Decimal("500.00"),
            status=BookingStatus.FAILED,
        )
        resp = self.client.post(f"/api/bookings/{booking.id}/cancel/")
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)

    def test_unauthenticated_cannot_book(self):
        self.client.force_authenticate(user=None)
        resp = self.client.post("/api/bookings/", {
            "test": str(self.test.id),
            "centre": str(self.centre.id),
            "appointment_datetime": self.future,
        })
        self.assertEqual(resp.status_code, status.HTTP_401_UNAUTHORIZED)
