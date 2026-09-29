from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views import DiagnosticCentreViewSet, DiagnosticTestViewSet

centre_router = DefaultRouter()
centre_router.register("", DiagnosticCentreViewSet, basename="centre")

test_router = DefaultRouter()
test_router.register("", DiagnosticTestViewSet, basename="test")

urlpatterns = [
    path("tests/", include(test_router.urls)),
    path("", include(centre_router.urls)),
]
