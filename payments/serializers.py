from rest_framework import serializers

from .models import Payment


class PaymentInitiateSerializer(serializers.Serializer):
    booking_id = serializers.UUIDField()


class PaymentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Payment
        fields = ["id", "booking", "transaction_id", "amount", "status", "created_at"]


class WebhookSerializer(serializers.Serializer):
    event_id = serializers.CharField(max_length=100)
    transaction_id = serializers.CharField(max_length=100)
    status = serializers.ChoiceField(choices=["SUCCESS", "FAILED"])
