from rest_framework import serializers

from exchange.models import Exchange
from exchange.utils import get_or_create_currency


class ExchangeSerializer(serializers.ModelSerializer):
    base_currency = serializers.CharField(source='base_currency.tag')
    quote_currency = serializers.CharField(source='quote_currency.tag')

    class Meta:
        model = Exchange
        fields = ['date', 'base_currency', 'quote_currency', 'price']

    def to_internal_value(self, data):
        internal_value = super().to_internal_value(data)
        internal_value['base_currency'] = get_or_create_currency(tag=internal_value['base_currency']['tag'])
        internal_value['quote_currency'] = get_or_create_currency(tag=internal_value['quote_currency']['tag'])
        return internal_value

