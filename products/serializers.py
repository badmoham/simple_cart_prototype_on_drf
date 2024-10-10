from rest_framework import serializers

from products.models import Product


class ProductSerializer(serializers.ModelSerializer):
    """ serializer for Product model """
    class Meta:
        model = Product
        fields = ['id', 'name', 'price', 'stock_quantity']



