from rest_framework.routers import SimpleRouter

from exchange.views import ExchangeViewSet

router = SimpleRouter()
router.register('', ExchangeViewSet)

urlpatterns = [

              ] + router.urls
