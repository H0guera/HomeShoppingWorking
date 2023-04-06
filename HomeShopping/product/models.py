from django.core.validators import MinValueValidator
from django.db import models
from django.utils.functional import cached_property


class Product(models.Model):
    STANDALONE, PARENT, CHILD = 'standalone', 'parent', 'child'
    STRUCTURE_CHOICES = (
        (STANDALONE, 'Stand-alone product'),
        (PARENT, 'Parent product'),
        (CHILD, 'Child product'),
    )
    structure = models.CharField(
        max_length=10,
        choices=STRUCTURE_CHOICES,
        default=STANDALONE,
    )
    title = models.CharField(max_length=255)
    article = models.CharField(max_length=255, unique=True, blank=True)
    price = models.FloatField(validators=(MinValueValidator(limit_value=0.01),))
    description = models.TextField(blank=True)
    categories = models.ForeignKey(
        'product.ProductCategory',
        null=True,
        on_delete=models.SET_NULL)
    attributes = models.ManyToManyField(
        'ProductAttribute',
        through='ProductAttributeValue',
    )
    parent = models.ForeignKey(
        'self',
        blank=True,
        null=True,
        on_delete=models.CASCADE,
        related_name='children',
    )
    product_class = models.ForeignKey(
        'ProductClass',
        null=True,
        blank=True,
        on_delete=models.PROTECT,
    )

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        if not self.id:
            self.article = f"{self.title}{(self.categories.product_set.count()) + 1}"
        super().save(*args, **kwargs)

    def get_product_class(self):
        """
        Return a product's item class. Child products inherit their parent's.
        """
        if self.is_child:
            return self.parent.product_class
        else:
            return self.product_class

    @property
    def allowed_quantity(self):
        if self.stockrecords.exists():
            return self.stockrecords.get(product=self.id).net_stock_level
        return 0

    @property
    def is_child(self):
        return self.structure == self.CHILD


class ProductClass(models.Model):
    name = models.CharField(max_length=128)
    track_stock = models.BooleanField(default=True)

    def __str__(self):
        return self.name

    @property
    def has_attributes(self):
        return self.attributes.exists()


class ProductCategory(models.Model):
    title = models.CharField(max_length=255)

    def __str__(self):
        return self.title


class ProductAttribute(models.Model):
    product_class = models.ForeignKey(
        'ProductClass',
        blank=True,
        on_delete=models.CASCADE,
        related_name="attributes",
        null=True)
    name = models.CharField(max_length=128)
    # Attribute types
    TEXT = "text"
    INTEGER = "integer"
    TYPE_CHOICES = (
        (TEXT, "Text"),
        (INTEGER, "Integer"),
    )
    type = models.CharField(
        choices=TYPE_CHOICES,
        default=TYPE_CHOICES[0][0],
        max_length=20)

    def __str__(self):
        return self.name


class ProductAttributeValue(models.Model):
    attribute = models.ForeignKey('ProductAttribute', on_delete=models.CASCADE)
    product = models.ForeignKey('product', on_delete=models.CASCADE, related_name='attribute_values')

    value_text = models.TextField(blank=True, null=True)
    value_integer = models.IntegerField(blank=True, null=True, db_index=True)

    def _get_value(self):
        value = getattr(self, 'value_%s' % self.attribute.type)
        if hasattr(value, 'all'):
            value = value.all()
        return value

    def _set_value(self, new_value):
        attr_name = 'value_%s' % self.attribute.type
        setattr(self, attr_name, new_value)
        return

    value = property(_get_value, _set_value)

    def __str__(self):
        return self.summary()

    def summary(self):
        """
        Gets a string representation of both the attribute and it's value,
        used e.g in product summaries.
        """
        return "%s: %s" % (self.attribute.name, self.value_as_text)

    @property
    def value_as_text(self):
        """
        Returns a string representation of the attribute's value. To customise
        e.g. image attribute values, declare a _image_as_text property and
        return something appropriate.
        """
        property_name = '_%s_as_text' % self.attribute.type
        return getattr(self, property_name, self.value)


class StockRecord(models.Model):
    product = models.ForeignKey(
        'product',
        on_delete=models.CASCADE,
        related_name="stockrecords",
        verbose_name="product",
    )

    num_in_stock = models.PositiveIntegerField(
        "Number in stock", blank=True, null=True)

    low_stock_threshold = models.PositiveIntegerField(
        "Low Stock Threshold", blank=True, null=True)

    date_created = models.DateTimeField("Date created", auto_now_add=True)
    date_updated = models.DateTimeField("Date updated", auto_now=True,
                                        db_index=True)

    def __str__(self):
        return self.product.title

    @property
    def net_stock_level(self):
        if self.num_in_stock is None:
            return 0
        return self.num_in_stock
