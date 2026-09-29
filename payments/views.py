import logging
import random
import uuid

from django.db import IntegrityError, transaction
from drf_spectacular.utils import extend_schema
from rest_framework import status, permissions
from rest_framework.response import Response
from rest_framework.views import APIView

from bookings.models import Booking, BookingStatus
from .models import Payment, PaymentStatus, WebhookEvent
from .serializers import PaymentInitiateSerializer, PaymentSerializer, WebhookSerializer

logger = logging.getLogger(__name__)


class PaymentInitiateView(APIView):
    """
    Simulated payment endpoint.
    Accepts a booking_id, creates a payment with a random SUCCESS/FAILED outcome,
    and updates the booking status accordingly.
    """

    @extend_schema(request=PaymentInitiateSerializer, responses={201: PaymentSerializer})
    def post(self, request):
        serializer = PaymentInitiateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        booking_id = serializer.validated_data["booking_id"]

        try:
            booking = Booking.objects.get(id=booking_id, user=request.user)
        except Booking.DoesNotExist:
            return Response(
                {"detail": "Booking not found."},
                status=status.HTTP_404_NOT_FOUND,
            )

        if booking.status != BookingStatus.PENDING:
            return Response(
                {"detail": f"Cannot pay for a booking with status {booking.status}."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        simulated_status = random.choice([PaymentStatus.SUCCESS, PaymentStatus.FAILED])
        transaction_id = f"txn_{uuid.uuid4().hex[:16]}"

        with transaction.atomic():
            payment = Payment.objects.create(
                booking=booking,
                transaction_id=transaction_id,
                amount=booking.amount,
                status=simulated_status,
            )
            booking.status = (
                BookingStatus.CONFIRMED
                if simulated_status == PaymentStatus.SUCCESS
                else BookingStatus.FAILED
            )
            booking.save(update_fields=["status", "updated_at"])

        logger.info(
            "Payment %s for booking %s: %s",
            transaction_id, booking_id, simulated_status,
        )
        return Response(PaymentSerializer(payment).data, status=status.HTTP_201_CREATED)


class PaymentWebhookView(APIView):
    """
    Idempotent webhook endpoint for payment status updates.
    Uses event_id to ensure duplicate events are safely ignored.
    """
    permission_classes = [permissions.AllowAny]
    authentication_classes = []

    @extend_schema(request=WebhookSerializer, responses={200: None})
    def post(self, request):
        serializer = WebhookSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        event_id = serializer.validated_data["event_id"]
        transaction_id = serializer.validated_data["transaction_id"]
        payment_status = serializer.validated_data["status"]

        try:
            with transaction.atomic():
                WebhookEvent.objects.create(event_id=event_id)

                try:
                    payment = Payment.objects.select_for_update().get(
                        transaction_id=transaction_id
                    )
                except Payment.DoesNotExist:
                    logger.warning("Webhook for unknown transaction: %s", transaction_id)
                    return Response(
                        {"detail": "Transaction not found."},
                        status=status.HTTP_404_NOT_FOUND,
                    )

                payment.status = payment_status
                payment.save(update_fields=["status"])

                booking = payment.booking
                booking.status = (
                    BookingStatus.CONFIRMED
                    if payment_status == PaymentStatus.SUCCESS
                    else BookingStatus.FAILED
                )
                booking.save(update_fields=["status", "updated_at"])

                logger.info(
                    "Webhook processed: event=%s txn=%s status=%s",
                    event_id, transaction_id, payment_status,
                )
        except IntegrityError:
            logger.info("Duplicate webhook event ignored: %s", event_id)
            return Response(
                {"detail": "Event already processed."},
                status=status.HTTP_200_OK,
            )

        return Response({"detail": "Webhook processed."}, status=status.HTTP_200_OK)
