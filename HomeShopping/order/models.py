from django.conf.global_settings import AUTH_USER_MODEL
from django.db import models

from phonenumber_field.modelfields import PhoneNumberField


class ShippingAddress(models.Model):
    first_name = models.CharField(max_length=255, blank=True)
    last_name = models.CharField(max_length=255, blank=True)
    line1 = models.CharField(max_length=255)
    line2 = models.CharField(max_length=255, blank=True)
    phone = PhoneNumberField(
        blank=True,
        help_text="In case we need to call you about your order",
    )
    notes = models.TextField(
        blank=True,
        verbose_name="Instructions",
        help_text="Tell us anything we should know when delivering your order.",
    )

    def __str__(self):
        return f'{self.first_name}, {self.last_name}, {self.line1}'

    @property
    def order(self):
        """
        Return the order linked to this shipping address
        """
        return self.order_set.first()


class Order(models.Model):
    number = models.CharField(max_length=128, db_index=True, unique=True)
    total = models.DecimalField(decimal_places=2, max_digits=12)
    guest_email = models.EmailField(blank=True)
    date_placed = models.DateTimeField(db_index=True, auto_now_add=True)
    basket = models.ForeignKey(
        'basket.Basket',
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
    )
    user = models.ForeignKey(
        AUTH_USER_MODEL,
        related_name='orders',
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
    )
    shipping_address = models.ForeignKey(
        'ShippingAddress', null=True, blank=True,
        verbose_name="Shipping Address",
        on_delete=models.SET_NULL,
    )

    def __str__(self):
        return "#%s" % (self.number,)

    @property
    def is_anonymous(self):
        # It's possible for an order to be placed by a customer who then
        # deletes their profile.  Hence, we need to check that a guest email is
        # set.
        return self.user is None and bool(self.guest_email)

    @property
    def email(self):
        if not self.user:
            return self.guest_email
        return self.user.email


class OrderLine(models.Model):
    quantity = models.PositiveIntegerField(default=1)
    order = models.ForeignKey(
        'Order',
        on_delete=models.CASCADE,
        related_name='lines',
        verbose_name="Order",
    )
    stockrecord = models.ForeignKey(
        'product.StockRecord',
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        verbose_name="Stock record",
    )
    product = models.ForeignKey(
        'product.Product',
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        verbose_name="Product",
    )


class OrderLineAttribute(models.Model):
    type = models.CharField(max_length=128)
    value = models.CharField(max_length=128)
    line = models.ForeignKey(
        'OrderLine',
        on_delete=models.CASCADE,
        related_name='attributes',
    )

    def __str__(self):
        return "%s = %s" % (self.type, self.value)
