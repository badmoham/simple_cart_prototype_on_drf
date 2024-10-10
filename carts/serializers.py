from django.db import transaction, IntegrityError
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
    items = CartItemSerializer(many=True)

    class Meta:
        model = Cart
        fields = ['id', 'user', 'updated', 'is_dead', 'items']
        read_only_fields = ['user', 'updated', 'is_dead']

    def create(self, validated_data):
        items = validated_data.pop('items')
        try:
            with transaction.atomic():
                cart, created = Cart.objects.get_or_create(user=validated_data['user'])
                if not created:
                    cart.revive()
                for item in items:
                    if CartItem.objects.filter(cart=cart, products=item).exists():
                        old_cart_item = CartItem.objects.filter(cart=cart, products=item).get()
                        old_cart_item.update_quantity(item.quantity)
                    else:
                        CartItem.objects.create(cart=cart, **item)
                return cart
        except LowStockQuantityException as lsq:
            raise serializers.ValidationError({"error": str(lsq)}, code="product_low_on_stock")
        except IntegrityError as ie:
            raise serializers.ValidationError({"error": "not enough stock on product"}, code='not_enough_stock')







