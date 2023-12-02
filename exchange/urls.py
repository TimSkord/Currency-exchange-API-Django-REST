from django.urls import path
from rest_framework.routers import SimpleRouter

from exchange.views import ExchangeViewSet, ExchangeRate

router = SimpleRouter()
router.register('', ExchangeViewSet)

urlpatterns = [
    path('rate/', ExchangeRate.as_view())
              ] + router.urls
