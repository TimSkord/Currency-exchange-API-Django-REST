from django.db import models


class Currency(models.Model):
    tag = models.CharField(max_length=3)


class Exchange(models.Model):
    date = models.DateField()
    base_currency = models.ForeignKey(Currency, on_delete=models.CASCADE, related_name="base")
    quote_currency = models.ForeignKey(Currency, on_delete=models.CASCADE, related_name="quote")
    price = models.DecimalField(decimal_places=4, max_digits=20)

    class Meta:
        unique_together = ("date", "base_currency", "quote_currency")
