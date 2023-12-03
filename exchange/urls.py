from django.urls import path

from exchange.views import ExchangeViewSet, ExchangeRate, ExchangeHistoryViewSet

urlpatterns = [
    path('rate/', ExchangeRate.as_view(), name='rate'),
    path('history/', ExchangeHistoryViewSet.as_view({'get': 'list'}), name='exchange-history'),
    path('', ExchangeViewSet.as_view({'post': 'create', 'get': 'list'}), name='exchange-list'),
    path('<str:date>/<str:base_currency>/<str:quote_currency>/', ExchangeViewSet.as_view(
        {'get': 'retrieve', 'put': 'update', 'patch': 'partial_update', 'delete': 'destroy'}), name='exchange-detail'),
]
