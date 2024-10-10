from django.urls import include, path
from rest_framework import routers

from carts.views import CartViewSet

router = routers.DefaultRouter()
router.register('cart', CartViewSet)


urlpatterns = [
    path('', include(router.urls)),
]