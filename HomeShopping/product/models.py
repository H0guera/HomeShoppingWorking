from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator, RegexValidator
from django.db import models


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
    title = models.CharField(max_length=255, blank=True)
    article = models.CharField(max_length=255, unique=True, blank=True)

    description = models.TextField(blank=True)
    category = models.ForeignKey(
        'product.ProductCategory',
        blank=True,
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

    def clean(self):
        getattr(self, '_clean_%s' % self.structure)()

    def _clean_standalone(self):
        if not self.title:
            raise ValidationError(f'Title is required for {self.structure} product')
        if not self.product_class:
            raise ValidationError(f'A product class is required for {self.structure} product')
        if self.parent_id:
            raise ValidationError(f'Parent is forbidden for {self.structure} product')

    def _clean_parent(self):
        self._clean_standalone()

    def _clean_child(self):
        if not self.parent_id:
            raise ValidationError(f'Parent is required for {self.structure} product')
        if self.parent_id and not self.parent.is_parent:
            raise ValidationError("You can only assign child products to parent products.")
        if self.product_class:
            raise ValidationError(f'A product class is forbidden for {self.structure} product')
        if self.category:
            raise ValidationError(f'Categories is forbidden for {self.structure} product')

    def save(self, *args, **kwargs):
        # if not self.id:
        #     self.article = f"{self.title}"
        #     if self.is_child:
        #         self.article = f"{self.parent.article}{self.parent.id + 1}"
        self.clean()
        super().save(*args, **kwargs)

    def get_product_class(self):
        """
        Return a product's item class. Child products inherit their parent's.
        """
        if self.is_child:
            return self.parent.product_class
        else:
            return self.product_class

    def get_title(self):
        """
        Return a product's title or it's parent's title if it has no title
        """
        title = self.title
        if not title and self.parent_id:
            title = self.parent.title
        return title

    @property
    def allowed_quantity(self):
        if self.stockrecords.exists():
            return self.stockrecords.get(product=self.id).net_stock_level
        return 0

    @property
    def is_child(self):
        return self.structure == self.CHILD

    @property
    def is_parent(self):
        return self.structure == self.PARENT

    @property
    def has_stockrecords(self):
        """
        Test if this product has any stockrecords
        """
        return self.stockrecords.exists()


class ProductClass(models.Model):
    name = models.CharField(max_length=128)
    track_stock = models.BooleanField(default=True)
    slug = models.SlugField(
        max_length=128,
        unique=True,
        db_index=True,
    )

    def __str__(self):
        return self.name

    @property
    def has_attributes(self):
        return self.attributes.exists()


class ProductCategory(models.Model):
    title = models.CharField(max_length=55, unique=True)
    slug = models.SlugField(max_length=55, unique=True)

    def __str__(self):
        return self.title


class ProductAttribute(models.Model):
    name = models.CharField(max_length=128)
    code = models.SlugField(
        max_length=128,
        validators=[
            RegexValidator(
                regex=r'^[a-zA-Z_][0-9a-zA-Z_]*$',
                message=
                    "Code can only contain the letters a-z, A-Z, digits, "
                    "and underscores, and can't start with a digit."
            ),
        ],
    )
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

    required = models.BooleanField(default=False)
    product_class = models.ForeignKey(
        'ProductClass',
        blank=True,
        on_delete=models.CASCADE,
        related_name="attributes",
        null=True,
    )

    class Meta:
        unique_together = ('code', 'product_class')

    def __str__(self):
        return self.name

    def _save_value(self, value_obj, value):
        if value is None or value == '':
            value_obj.delete()
            return
        if value != value_obj.value:
            value_obj.value = value
            value_obj.save()

    def save_value(self, product, value):
        try:
            value_obj = product.attribute_values.get(attribute=self)
        except ProductAttributeValue.DoesNotExist:
            if value is None:
                return
            value_obj = ProductAttributeValue.objects.create(attribute=self, product=product)
        self._save_value(value_obj, value)

    def validate_value(self, value):
        validator = getattr(self, '_validate_%s' % self.type)
        validator(value)

    def _validate_text(self, value):
        if not isinstance(value, str):
            raise ValidationError('Must be str')

    def _validate_integer(self, value):
        if not isinstance(value, int):
            raise ValidationError('Must be integer')


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

    class Meta:
        unique_together = ('attribute', 'product')

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
    partner_sku = models.CharField(max_length=55, unique=True)
    price = models.FloatField(validators=(MinValueValidator(limit_value=0.01),))
    num_in_stock = models.PositiveIntegerField(
        "Number in stock", blank=True, null=True)

    low_stock_threshold = models.PositiveIntegerField(
        "Low Stock Threshold", blank=True, null=True)

    date_created = models.DateTimeField("Date created", auto_now_add=True)
    date_updated = models.DateTimeField("Date updated", auto_now=True,
                                        db_index=True)

    def __str__(self):
        return self.product.title

    def save(self, *args, **kwargs):
        self.clean()
        super().save(*args, **kwargs)

    def clean(self):
        if self.product.is_parent:
            raise ValidationError(f'Stockrecords is forbidden for parent product')

    @property
    def net_stock_level(self):
        if self.num_in_stock is None:
            return 0
        return self.num_in_stock
