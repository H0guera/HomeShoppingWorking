import operator

from django.core.exceptions import ValidationError

from rest_framework import relations, serializers

from api.serializers.exceptions import FieldError
from product.models import ProductAttribute


attribute_details = operator.itemgetter('code', 'value')


class DrillDownHyperlinkedMixin:
    def __init__(self, *args, **kwargs):
        try:
            self.extra_url_kwargs = kwargs.pop('extra_url_kwargs')
        except KeyError:
            msg = "DrillDownHyperlink Fields require an 'extra_url_kwargs' argument"
            raise ValueError(msg)

        super().__init__(*args, **kwargs)

    def get_extra_url_kwargs(self, obj):
        return {
            key: operator.attrgetter(path)(obj)
            for key, path in self.extra_url_kwargs.items()
        }

    def get_url(self, obj, view_name, request, format):  # pylint: disable=redefined-builtin
        """
        Given an object, return the URL that hyperlinks to the object.
        May raise a `NoReverseMatch` if the `view_name` and `lookup_field`
        attributes are not configured to correctly match the URL conf.
        """
        if hasattr(obj, 'pk') and obj.pk in (None, ''):
            return None

        lookup_value = getattr(obj, self.lookup_field)
        kwargs = {self.lookup_url_kwarg: lookup_value}
        kwargs.update(self.get_extra_url_kwargs(obj))
        return self.reverse(view_name, kwargs=kwargs, request=request, format=format)


class DrillDownHyperlinkedIdentityField(
    DrillDownHyperlinkedMixin,
    relations.HyperlinkedIdentityField,
):
    pass


class DrillDownHyperlinkedRelatedField(
    DrillDownHyperlinkedMixin,
    relations.HyperlinkedRelatedField,
):
    def use_pk_only_optimization(self):
        # we always want the full object so the mixin can filter on the attributes
        # specified with get_extra_url_kwargs
        return False


class AttributeValueField(serializers.Field):
    def __init__(self, **kwargs):
        # this field always needs the full object
        kwargs['source'] = '*'
        kwargs['error_messages'] = {
            'no_such_option': "{code}: Option {value} does not exist.",
            'invalid': "Wrong type, {error}.",
            'attribute_validation_error':
                "Error assigning `{value}` to {code}, {error}.",
            'attribute_required': "Attribute {code} is required.",
            'attribute_missing':
                "No attribute exist with code={code}, "
                "please define it in the product_class first.",

            'child_without_parent':
                "Can not find attribute if product_class is empty and "
                "parent is empty as well, child without parent?",
        }
        super(AttributeValueField, self).__init__(**kwargs)

    def get_value(self, dictionary):
        if getattr(self.root, 'partial', False):
            product = self.root.instance
            updated_dictionary = dict(dictionary, product=product)
            return updated_dictionary
        return dictionary

    def to_internal_value(self, data):
        assert 'product' in data or 'product_class' in data or 'parent' in data

        try:
            code, value = attribute_details(data)
            internal_value = value

            if 'product_class' in data and data['product_class'] is not None and data['product_class'] != '':
                attribute = ProductAttribute.objects.get(code=code, product_class__slug=data.get('product_class'))
            elif 'parent' in data and data['parent'] is not None:
                attribute = ProductAttribute.objects.get(code=code, product_class__product__id=data.get('parent'))
            elif 'product' in data:
                attribute = ProductAttribute.objects.get(
                    code=code,
                    product_class=data.get('product').get_product_class(),
                )

            if attribute.required and value is None:
                self.fail('attribute_required', code=code)

            try:
                attribute.validate_value(internal_value)
            except TypeError as e:
                self.fail(
                    'attribute_validation_error',
                    code=code,
                    value=internal_value,
                    error=e,
                )
            except ValidationError as e:
                self.fail(
                    'attribute_validation_error',
                    code=code,
                    value=internal_value,
                    error=",".join(e.messages),
                )
            return {'value': internal_value, 'attribute': attribute}
        except ProductAttribute.DoesNotExist:
            self.fail('attribute_missing', **data)
        except KeyError as e:
            (field_name,) = e.args
            raise FieldError(
                detail={field_name: self.error_messages['required']}, code='required',
            )

    def to_representation(self, value):
        return value.value
