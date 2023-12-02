from datetime import datetime

from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.viewsets import ModelViewSet
from exchange.filters import ExchangeFilter
from exchange.models import Exchange
from exchange.serializers import ExchangeSerializer
from exchange.utils import calculate_rate


class ExchangeViewSet(ModelViewSet):
    queryset = Exchange.objects.all()
    serializer_class = ExchangeSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_class = ExchangeFilter


class ExchangeRate(APIView):

    def get(self, request):
        base_currency_tag = request.GET.get('base_currency__tag')
        quote_currency_tag = request.GET.get('quote_currency__tag')
        date = request.GET.get('date')
        rate = calculate_rate(base_currency_tag, quote_currency_tag, date)
        return Response({'rate': rate})
