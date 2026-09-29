from django.utils import timezone
from rest_framework import serializers

from centres.models import DiagnosticTest
from .models import Booking


class BookingCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Booking
        fields = ["id", "test", "centre", "appointment_datetime"]

    def validate_appointment_datetime(self, value):
        if value <= timezone.now():
            raise serializers.ValidationError("Appointment must be in the future.")
        return value

    def validate(self, data):
        test = data["test"]
        centre = data["centre"]
        if test.centre_id != centre.id:
            raise serializers.ValidationError(
                {"test": "This test is not available at the selected centre."}
            )
        if not test.is_active:
            raise serializers.ValidationError(
                {"test": "This test is currently unavailable."}
            )
        return data

    def create(self, validated_data):
        validated_data["user"] = self.context["request"].user
        validated_data["amount"] = validated_data["test"].price
        return super().create(validated_data)


class BookingSerializer(serializers.ModelSerializer):
    test_name = serializers.CharField(source="test.name", read_only=True)
    centre_name = serializers.CharField(source="centre.name", read_only=True)

    class Meta:
        model = Booking
        fields = [
            "id", "user", "test", "test_name", "centre", "centre_name",
            "appointment_datetime", "amount", "status", "created_at", "updated_at",
        ]
        read_only_fields = ["user", "amount", "status"]
