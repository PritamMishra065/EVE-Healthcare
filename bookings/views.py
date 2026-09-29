import logging

from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response

from .models import Booking, BookingStatus
from .serializers import BookingSerializer, BookingCreateSerializer

logger = logging.getLogger(__name__)


class BookingViewSet(viewsets.ModelViewSet):
    serializer_class = BookingSerializer
    filterset_fields = ["status"]
    ordering_fields = ["created_at", "appointment_datetime"]
    http_method_names = ["get", "post", "head", "options"]

    def get_queryset(self):
        if getattr(self, "swagger_fake_view", False):
            return Booking.objects.none()
        return Booking.objects.filter(user=self.request.user).select_related("test", "centre")

    def get_serializer_class(self):
        if self.action == "create":
            return BookingCreateSerializer
        return BookingSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        booking = serializer.save()
        logger.info("Booking created: %s by user %s", booking.id, request.user.id)
        return Response(
            BookingSerializer(booking).data,
            status=status.HTTP_201_CREATED,
        )

    @action(detail=True, methods=["post"])
    def cancel(self, request, pk=None):
        booking = self.get_object()
        if booking.status not in (BookingStatus.PENDING, BookingStatus.CONFIRMED):
            return Response(
                {"detail": f"Cannot cancel a booking with status {booking.status}."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        booking.status = BookingStatus.CANCELLED
        booking.save(update_fields=["status", "updated_at"])
        logger.info("Booking cancelled: %s", booking.id)
        return Response(BookingSerializer(booking).data)
