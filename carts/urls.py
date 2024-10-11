from django.urls import include, path
from rest_framework import routers

from carts.views import CartViewSet, AllUsersCartSumView

router = routers.DefaultRouter()
router.register('cart', CartViewSet)


urlpatterns = [
    path('', include(router.urls)),
    path('report/', AllUsersCartSumView.as_view(), name="all_users_cart_sum_view"),
]