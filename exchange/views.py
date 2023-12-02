from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.viewsets import ModelViewSet

from exchange.filters import ExchangeFilter
from exchange.models import Exchange
from exchange.serializers import ExchangeSerializer


class ExchangeViewSet(ModelViewSet):
    queryset = Exchange.objects.all()
    serializer_class = ExchangeSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_class = ExchangeFilter
