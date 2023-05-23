from copy import deepcopy

from rest_framework import serializers
from rest_framework.fields import empty

from api.serializers.exceptions import FieldError
from api.serializers.fields import AttributeValueField, DrillDownHyperlinkedIdentityField
from api.serializers.utils import UpdateListSerializer
from product.models import ProductClass, ProductAttribute, ProductAttributeValue, Product, ProductCategory, StockRecord


class CategorySerializer(serializers.ModelSerializer):
    url = serializers.HyperlinkedIdentityField(view_name='category-detail')

    class Meta:
        model = ProductCategory
        fields = '__all__'


class ProductAttributeListSerializer(UpdateListSerializer):
    def select_existing_item(self, manager, datum):
        try:
            return manager.get(product_class=datum['product_class'], code=datum['code'])
        except manager.model.DoesNotExist:
            pass
        except manager.model.MultipleObjectsReturned:
            pass
        return None


class ProductAttributeSerializer(serializers.HyperlinkedModelSerializer):
    url = serializers.HyperlinkedIdentityField(view_name='admin-productattr-detail')
    product_class = serializers.SlugRelatedField(
        slug_field='slug',
        queryset=ProductClass.objects.get_queryset(),
        write_only=True,
        required=False,
    )

    class Meta:
        list_serializer_class = ProductAttributeListSerializer
        model = ProductAttribute
        fields = '__all__'

    def create(self, validated_data):
        instance = super(ProductAttributeSerializer, self).create(validated_data)
        return self.update(instance, validated_data)

    def update(self, instance, validated_data):
        updated_instance = super(ProductAttributeSerializer, self).update(instance, validated_data)
        return updated_instance


class ProductAttributeValueListSerializer(UpdateListSerializer):
    def get_value(self, dictionary):
        values = super().get_value(dictionary)
        if values is empty:
            return values
        product_class = dictionary.get('product_class')
        parent = dictionary.get('parent')
        return [
            dict(value, product_class=product_class, parent=parent) for value in values
        ]

    def select_existing_item(self, manager, datum):
        try:
            return manager.get(attribute=datum['attribute'])
        except manager.model.DoesNotExist:
            pass
        except manager.model.MultipleObjectsReturned:
            pass
        return None


class ProductAttributeValueSerializer(serializers.ModelSerializer):
    product = serializers.PrimaryKeyRelatedField(
        queryset=Product.objects,
        required=False,
    )
    code = serializers.CharField(
        source='attribute.code',
        read_only=True,
    )
    value = AttributeValueField()

    name = serializers.CharField(
        source='attribute.name',
        required=False,
        read_only=True,
    )

    def to_internal_value(self, data):
        try:
            internal_value = super(ProductAttributeValueSerializer, self).to_internal_value(data)
            internal_value['product_class'] = data.get('product_class')
            return internal_value
        except FieldError as e:
            raise serializers.ValidationError(e.detail)

    def save(self, **kwargs):
        data = deepcopy(kwargs)
        data.update(self.validated_data)
        return self.update_or_create(data)

    def update_or_create(self, validated_data):
        product = validated_data['product']
        attribute = validated_data['attribute']
        value = validated_data['value']
        attribute.save_value(product=product, value=value)
        return product.attribute_values.get(attribute=attribute)

    create = update_or_create

    def update(self, instance, validated_data):
        data = deepcopy(validated_data)
        return self.update_or_create(data)

    class Meta:
        list_serializer_class = ProductAttributeValueListSerializer
        model = ProductAttributeValue
        fields = ('name', 'code', 'value', 'product')


class ProductStockRecordSerializer(serializers.ModelSerializer):
    url = DrillDownHyperlinkedIdentityField(
        view_name="product-stockrecord-detail",
        extra_url_kwargs={"product_pk": "product_id"},
    )

    class Meta:
        model = StockRecord
        fields = '__all__'


class BaseProductSerializer(serializers.ModelSerializer):
    attributes = ProductAttributeValueSerializer(
        many=True,
        source='attribute_values',
        required=False,
    )
    product_class = serializers.SlugRelatedField(
        slug_field='slug',
        queryset=ProductClass.objects,
        allow_null=True,
    )

    class Meta:
        model = Product


class ChildProductSerializer(BaseProductSerializer):
    "Serializer for child products"
    url = serializers.HyperlinkedIdentityField(view_name="product-detail")
    parent = serializers.HyperlinkedRelatedField(
        view_name="product-detail",
        queryset=Product.objects.filter(structure=Product.PARENT),
    )

    class Meta:
        model = Product
        fields = '__all__'


class ProductSerializer(BaseProductSerializer):
    url = serializers.HyperlinkedIdentityField(view_name="product-detail")
    children = ChildProductSerializer(many=True, required=False)
    stockrecords = ProductStockRecordSerializer(many=True, required=False)

    class Meta(BaseProductSerializer.Meta):
        fields = '__all__'


class AddProductSerializer(serializers.Serializer):
    quantity = serializers.IntegerField(required=True)
    product = serializers.HyperlinkedRelatedField(
        view_name="product-detail",
        queryset=Product.objects,
        required=True,
    )
    stockrecord = serializers.HyperlinkedRelatedField(
        view_name='product-stockrecord-detail',
        queryset=StockRecord.objects,
    )

    def validate(self, attrs):
        if attrs['product'].id != attrs['stockrecord'].product_id:
            raise serializers.ValidationError('Incorrect stockrecord')
        return attrs
