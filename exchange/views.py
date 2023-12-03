from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import mixins
from rest_framework.generics import get_object_or_404
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.viewsets import ModelViewSet, GenericViewSet

from exchange.filters import ExchangeFilter
from exchange.models import Exchange
from exchange.serializers import ExchangeSerializer
from exchange.utils import calculate_rate


class ExchangeHistoryViewSet(mixins.ListModelMixin, GenericViewSet):
    queryset = Exchange.objects.all()
    serializer_class = ExchangeSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_class = ExchangeFilter


class ExchangeViewSet(ModelViewSet):
    queryset = Exchange.objects.all()
    serializer_class = ExchangeSerializer

    def get_object(self):
        queryset = self.filter_queryset(self.get_queryset())
        filter_kwargs = {
            'date': self.kwargs['date'],
            'base_currency__tag': self.kwargs['base_currency'],
            'quote_currency__tag': self.kwargs['quote_currency'],
        }
        obj = get_object_or_404(queryset, **filter_kwargs)
        self.check_object_permissions(self.request, obj)
        return obj


class ExchangeRate(APIView):

    def get(self, request):
        base_currency_tag = request.GET.get('base_currency__tag')
        quote_currency_tag = request.GET.get('quote_currency__tag')
        date = request.GET.get('date')
        rate = calculate_rate(base_currency_tag, quote_currency_tag, date)
        return Response({
            'date': date,
            'base_currency': base_currency_tag,
            'quote_currency': quote_currency_tag,
            'rate': rate
        })
