from decimal import Decimal

from django.contrib.auth.models import User
from django.core.exceptions import ObjectDoesNotExist, PermissionDenied
from django.db import models
from django.utils.timezone import now

from basket.managers import OpenBasketManager


class Basket(models.Model):
    owner = models.ForeignKey(User, blank=True, null=True, on_delete=models.CASCADE)

    OPEN, MERGED, SAVED, FROZEN, SUBMITTED = (
        "Open", "Merged", "Saved", "Frozen", "Submitted")
    STATUS_CHOICES = (
        (OPEN, "Open - currently active"),
        (FROZEN, "Frozen - the basket cannot be modified"),
        (SUBMITTED, "Submitted - has been ordered at the checkout"),
    )
    status = models.CharField(
        max_length=128,
        default=OPEN,
        choices=STATUS_CHOICES,
    )
    editable_statuses = (OPEN,)

    objects = models.Manager()
    open = OpenBasketManager()

    date_submitted = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f'{self.status}s basket {self.pk}'

    def freeze(self):
        """
        Freezes the basket so it cannot be modified.
        """
        self.status = self.FROZEN
        self.save()

    def thaw(self):
        """
        Unfreezes a basket so it can be modified again
        """
        self.status = self.OPEN
        self.save()

    def submit(self):
        """
        Mark this basket as submitted
        """
        self.status = self.SUBMITTED
        self.date_submitted = now()
        self.save()

    def add_product(self, product, stockrecord, quantity=1):
        if not self.id:
            self.save()
        defaults = {
            'quantity': quantity,
        }
        line, created = self.lines.get_or_create(product=product, stockrecord=stockrecord, defaults=defaults)
        if not created:
            line.quantity = max(0, line.quantity + quantity)
            line.save()
        return line, created

    def merge_line(self, line, add_quantities):
        try:
            existing_line = self.lines.get(product=line.product, stockrecord=line.stockrecord)
        except ObjectDoesNotExist:
            line.basket = self
            line.save()
        else:
            if add_quantities:
                existing_line.quantity += line.quantity
            else:
                existing_line.quantity = max(existing_line.quantity, line.quantity)
            existing_line.save()
            line.delete()
        finally:
            self._lines = None

    def merge(self, basket, add_quantities=True):
        for line_to_merge in basket.lines.all():
            self.merge_line(line_to_merge, add_quantities)

        basket.save()

    def current_quantity(self, product, stockrecord):
        try:
            return self.lines.get(product_id=product, stockrecord=stockrecord).quantity
        except ObjectDoesNotExist:
            return 0

    def num_items(self):
        return sum(line.quantity for line in self.lines.all())

    def _total_price(self, property):
        total = Decimal('0.00')
        for line in self.lines.all():
            try:
                total += int(getattr(line, property))
            except ObjectDoesNotExist:
                # Handle situation where the product may have been deleted
                pass
        return total

    @property
    def total_price(self):
        if self.pk:
            return self._total_price('line_price')

    @property
    def is_submitted(self):
        return self.status == self.SUBMITTED

    @property
    def can_be_edited(self):
        """
        Test if a basket can be edited
        """
        return self.status in self.editable_statuses


class BasketLine(models.Model):
    stockrecord = models.ForeignKey(
        'product.StockRecord',
        related_name='basket_lines',
        on_delete=models.CASCADE,
    )
    basket = models.ForeignKey(
        'Basket',
        on_delete=models.CASCADE,
        related_name='lines',
    )
    quantity = models.PositiveIntegerField(default=1)
    product = models.ForeignKey('product.Product', on_delete=models.CASCADE, related_name='basket_lines')

    def save(self, *args, **kwargs):
        if not self.basket.can_be_edited:
            raise PermissionDenied(
                "You cannot modify a %s basket" % (
                    self.basket.status.lower(),))
        return super().save(*args, **kwargs)

    @property
    def line_price(self):
        return self.quantity * self.stockrecord.price

    @property
    def available_quantity(self):
        return self.stockrecord.num_in_stock
