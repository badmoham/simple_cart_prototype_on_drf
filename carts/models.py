from django.db import models, transaction
from django.contrib.auth import get_user_model
from django.utils.translation import gettext_lazy as _

from carts.exceptions import LowStockQuantityException


class Cart(models.Model):
    """ contain records of carts """
    user = models.OneToOneField(to=get_user_model(), on_delete=models.CASCADE)
    updated = models.DateTimeField(_('last updated at'), auto_now=True)
    is_dead = models.BooleanField(_('is the cart left out'), default=False)

    def kill(self):
        """ will give back quantities to products and turn the is_dead tp False """
        if self.is_dead:
            return
        with transaction.atomic():
            self.is_dead = True
            items = CartItem.objects.filter(cart=self).prefetch_related()
            for item in items:
                item.products.stock_quantity = models.F('products.stock_quantity') + models.F('quantity')
            self.save()

    def revive(self):
        """
        will retake products in cart from products quantity if possible and switch is_dead
        if is_dead is True
        """
        if self.is_dead:
            return
        with transaction.atomic():
            self.is_dead = False
            items = CartItem.objects.filter(cart=self).prefetch_related()
            for item in items:
                item.products.stock_quantity = models.F('products.stock_quantity') - models.F('quantity')
            self.save()


class CartItem(models.Model):
    """ records of one product in a cart with its quantity """
    cart = models.ForeignKey(to=Cart, on_delete=models.CASCADE, related_name='items_cart')
    products = models.ForeignKey(to='products.Product', on_delete=models.CASCADE, related_name='cart_item_product')
    quantity = models.PositiveIntegerField(_("quantity in this order"))

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['cart', 'products'], name='unique_cart_products')
        ]

    def update_quantity(self, new_quantity: int):
        """ will update quantity of a CartItem and its Product stock_quantity """
        diff = new_quantity - self.quantity
        if self.products.stock_quantity < diff:
            raise LowStockQuantityException(f"requested quantity of product: {self.products} is {new_quantity},"
                                            f" while {self.products.stock_quantity} is available!")
        with transaction.atomic():
            self.products.stock_quantity = models.F('stock_quantity') + diff
            self.quantity = new_quantity
            self.save()


class ServerSetting(models.Model):
    """ contains dynamic settings for serverside appliance """
    name = models.CharField(_('unique name of setting'), unique=True, max_length=32)
    int_value = models.IntegerField(_('integer value of setting'))






