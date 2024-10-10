from rest_framework import permissions, viewsets, mixins

from carts.models import Cart
from carts.serializers import CartSerializer


class CartViewSet(
    mixins.ListModelMixin,
    mixins.CreateModelMixin,
    viewsets.GenericViewSet,
):
    """ API endpoint that allows users to create or view their own cart. """
    queryset = Cart.objects.all()
    serializer_class = CartSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        """ Filter the queryset by the current user """
        return self.queryset.filter(user=self.request.user).prefetch_related('items_cart')

    def perform_create(self, serializer):
        """ Associate the new object with the current user """
        serializer.save(user=self.request.user)

