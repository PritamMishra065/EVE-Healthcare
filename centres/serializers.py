from rest_framework import serializers

from .models import DiagnosticCentre, DiagnosticTest


class DiagnosticTestSerializer(serializers.ModelSerializer):
    class Meta:
        model = DiagnosticTest
        fields = ["id", "name", "description", "price", "is_active", "created_at"]


class DiagnosticCentreSerializer(serializers.ModelSerializer):
    tests = DiagnosticTestSerializer(many=True, read_only=True)

    class Meta:
        model = DiagnosticCentre
        fields = ["id", "name", "location", "tests", "created_at"]


class DiagnosticCentreListSerializer(serializers.ModelSerializer):
    test_count = serializers.IntegerField(read_only=True)

    class Meta:
        model = DiagnosticCentre
        fields = ["id", "name", "location", "test_count", "created_at"]
