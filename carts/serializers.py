from django.db import transaction, IntegrityError
from django.utils import timezone
from rest_framework import serializers

from carts.exceptions import LowStockQuantityException
from carts.models import Cart, CartItem


class CartItemSerializer(serializers.ModelSerializer):
    """ serializer for CartItem model """
    class Meta:
        model = CartItem
        fields = ['id', 'products', 'quantity']


class CartSerializer(serializers.ModelSerializer):
    """ serializer for Cart model """
    items_cart = CartItemSerializer(many=True)

    class Meta:
        model = Cart
        fields = ['id', 'user', 'updated', 'is_dead', 'items_cart']
        read_only_fields = ['user', 'updated', 'is_dead']

    def create(self, validated_data):
        items = validated_data.pop('items_cart')
        try:
            return CartItem.create_cart_items_and_subtract_from_stock(user=validated_data['user'], items=items)
        except LowStockQuantityException as lsq:
            raise serializers.ValidationError({"error": str(lsq)}, code="product_low_on_stock")
        except IntegrityError as ie:
            raise serializers.ValidationError({"error": "not enough stock on product"}, code='not_enough_stock')







