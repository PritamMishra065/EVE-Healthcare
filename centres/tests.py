from decimal import Decimal
from django.test import TestCase
from rest_framework.test import APIClient
from rest_framework import status

from .models import DiagnosticCentre, DiagnosticTest


class CentreTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.centre = DiagnosticCentre.objects.create(
            name="Test Centre", location="Mumbai"
        )
        self.test1 = DiagnosticTest.objects.create(
            name="CBC", centre=self.centre, price=Decimal("500.00")
        )
        DiagnosticTest.objects.create(
            name="Inactive Test", centre=self.centre,
            price=Decimal("100.00"), is_active=False,
        )

    def test_list_centres(self):
        resp = self.client.get("/api/centres/")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resp.data["count"], 1)

    def test_retrieve_centre_with_tests(self):
        resp = self.client.get(f"/api/centres/{self.centre.id}/")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resp.data["name"], "Test Centre")
        self.assertEqual(len(resp.data["tests"]), 2)

    def test_list_active_tests_only(self):
        resp = self.client.get("/api/centres/tests/")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resp.data["count"], 1)
        self.assertEqual(resp.data["results"][0]["name"], "CBC")

    def test_search_centres(self):
        resp = self.client.get("/api/centres/?search=Mumbai")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resp.data["count"], 1)

    def test_centre_not_found(self):
        resp = self.client.get("/api/centres/00000000-0000-0000-0000-000000000000/")
        self.assertEqual(resp.status_code, status.HTTP_404_NOT_FOUND)
