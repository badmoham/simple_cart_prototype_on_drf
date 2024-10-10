from django.db import models
from django.utils.translation import gettext_lazy as _


class Product(models.Model):
    """ contain products information """

    name = models.CharField(_("product's name"), max_length=64)
    price = models.PositiveBigIntegerField(_("product's price"))
    stock_quantity = models.PositiveIntegerField(_("quantity in stock"))

    def __str__(self):
        return str(self.name)

