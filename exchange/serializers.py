from rest_framework import serializers

from exchange.models import Currency, Exchange


class CurrencySerializer(serializers.ModelSerializer):
    class Meta:
        model = Currency
        fields = ['tag']


class ExchangeSerializer(serializers.ModelSerializer):
    base_currency = CurrencySerializer()
    quote_currency = CurrencySerializer()

    class Meta:
        model = Exchange
        fields = ['date', 'base_currency', 'quote_currency', 'price']

    def create(self, validated_data):
        base_currency_data = validated_data.pop('base_currency')
        quote_currency_data = validated_data.pop('quote_currency')
        base_currency, _ = Currency.objects.get_or_create(**base_currency_data)
        quote_currency, _ = Currency.objects.get_or_create(**quote_currency_data)
        exchange = Exchange.objects.create(
            base_currency=base_currency,
            quote_currency=quote_currency,
            **validated_data
        )

        return exchange
