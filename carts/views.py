from rest_framework import permissions, viewsets, mixins
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

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


class AllUsersCartSumView(APIView):
    """ will return each days carts sum for each user """
    def get(self, request):
        """ get method """
        start_date = request.query_params.get('start_date', None)
        end_date = request.query_params.get('end_date', None)

        result = Cart.get_all_carts_sum(start_date=start_date, end_date=end_date)

        return Response(result, status=status.HTTP_200_OK)

