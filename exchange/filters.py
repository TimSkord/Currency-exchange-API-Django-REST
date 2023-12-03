import django_filters

from .models import Exchange


class ExchangeFilter(django_filters.FilterSet):
    class Meta:
        model = Exchange
        fields = {
            'base_currency__tag': ['exact'],
            'quote_currency__tag': ['exact'],
        }
