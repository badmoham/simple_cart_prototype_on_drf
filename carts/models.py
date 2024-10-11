from collections import defaultdict

from django.db import models, transaction
from django.db.models import Sum
from django.contrib.auth import get_user_model
from django.db.models.functions import JSONObject
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from carts.exceptions import LowStockQuantityException


class Cart(models.Model):
    """ contain records of carts """
    user = models.OneToOneField(to=get_user_model(), on_delete=models.CASCADE)
    updated = models.DateTimeField(_('last updated at'), auto_now=True, db_index=True)
    is_dead = models.BooleanField(_('is the cart left out'), default=False, db_index=True)

    def kill(self):
        """ will give back quantities to products and turn the is_dead tp False """
        if self.is_dead:
            return
        with transaction.atomic():
            self.is_dead = True
            items = CartItem.objects.filter(cart=self).prefetch_related()
            for item in items:
                item.add_from_stock()
            self.save()

    def revive(self):
        """
        will retake products in cart from products quantity if possible and switch is_dead
        if is_dead is True
        """
        if not self.is_dead:
            return
        with transaction.atomic():
            self.is_dead = False
            items = CartItem.objects.filter(cart=self).prefetch_related()
            for item in items:
                item.subtract_from_stock()
            self.save()

    @staticmethod
    def get_all_carts_sum(start_date=None, end_date=None) -> dict:
        """ will return aggregate sum for all carts for a given interval """
        filters = {}
        if start_date is not None:
            filters['cart__updated__gte'] = start_date
        if end_date is not None:
            filters['cart__updated__lte'] = end_date

        all_carts = CartItem.objects.filter(**filters).values(
            'cart__updated__date'
        ).annotate(
            data=JSONObject(
                username=models.F('cart__user__username'),
                total_amount=Sum(models.F('products__price') * models.F('quantity'))
            )
        ).order_by('-data__total_amount').values_list('cart__updated__date', 'data')

        data = defaultdict(lambda: [])
        for upd, cart_data in all_carts:
            data[upd.strftime('%Y-%m-%d')].append(cart_data)

        return dict(data)


class CartItem(models.Model):
    """ records of one product in a cart with its quantity """
    cart = models.ForeignKey(to=Cart, on_delete=models.CASCADE, related_name='items_cart')
    products = models.ForeignKey(to='products.Product', on_delete=models.CASCADE, related_name='cart_item_product')
    quantity = models.PositiveIntegerField(_("quantity in this order"))

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['cart', 'products'], name='unique_cart_products')
        ]

    @staticmethod
    def create_cart_items_and_subtract_from_stock(user, items):
        with transaction.atomic():
            cart, created = Cart.objects.get_or_create(user=user)
            if not created:
                cart.updated = timezone.now()
                cart.save(update_fields=["updated"])
                cart.revive()
            for item in items:
                if CartItem.objects.filter(cart=cart, products=item["products"]).exists():
                    old_cart_item = CartItem.objects.filter(cart=cart, products=item["products"]).get()
                    old_cart_item.update_quantity(item['quantity'])
                else:
                    cart_item = CartItem.objects.create(cart=cart, **item)
                    cart_item.subtract_from_stock()

            return cart


    def update_quantity(self, new_quantity: int):
        """ will update quantity of a CartItem and its Product stock_quantity """
        diff = new_quantity - self.quantity
        if self.products.stock_quantity < diff:
            raise LowStockQuantityException(f"requested quantity of product: {self.products} is {new_quantity},"
                                            f" while {self.products.stock_quantity} is available!")
        with transaction.atomic():
            self.products.stock_quantity = models.F('stock_quantity') - diff
            self.quantity = new_quantity
            self.save()
            self.products.save()

    def subtract_from_stock(self):
        """ will subtract item quantity from product stock quantity """
        self.products.stock_quantity = models.F("stock_quantity") - self.quantity
        self.products.save(update_fields=["stock_quantity"])

    def add_from_stock(self):
        """ will add item quantity to product stock quantity """
        self.products.stock_quantity = models.F("stock_quantity") + self.quantity
        self.products.save(update_fields=["stock_quantity"])


class ServerSetting(models.Model):
    """ contains dynamic settings for serverside appliance """
    name = models.CharField(_('unique name of setting'), unique=True, max_length=32)
    int_value = models.IntegerField(_('integer value of setting'))
