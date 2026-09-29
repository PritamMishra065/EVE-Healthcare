from django.db.models import Count
from rest_framework import viewsets, permissions

from .models import DiagnosticCentre, DiagnosticTest
from .serializers import (
    DiagnosticCentreSerializer,
    DiagnosticCentreListSerializer,
    DiagnosticTestSerializer,
)


class DiagnosticCentreViewSet(viewsets.ReadOnlyModelViewSet):
    permission_classes = [permissions.AllowAny]
    filterset_fields = ["location"]
    search_fields = ["name", "location"]
    ordering_fields = ["name", "created_at"]

    def get_queryset(self):
        if self.action == "list":
            return DiagnosticCentre.objects.annotate(test_count=Count("tests"))
        return DiagnosticCentre.objects.prefetch_related("tests")

    def get_serializer_class(self):
        if self.action == "list":
            return DiagnosticCentreListSerializer
        return DiagnosticCentreSerializer


class DiagnosticTestViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = DiagnosticTestSerializer
    permission_classes = [permissions.AllowAny]
    filterset_fields = ["centre", "is_active"]
    search_fields = ["name"]
    ordering_fields = ["name", "price"]

    def get_queryset(self):
        return DiagnosticTest.objects.filter(is_active=True)
