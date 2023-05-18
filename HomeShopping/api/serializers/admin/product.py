from django.db import transaction
from rest_framework import serializers

from api.serializers.product import ProductAttributeSerializer, BaseProductSerializer
from api.serializers.utils import UpdateListSerializer, UpdateRelationMixin
from product.models import ProductClass, StockRecord, Product, ProductCategory


class AdminCategorySerializer(serializers.ModelSerializer):
    url = serializers.HyperlinkedIdentityField(view_name='admin-categories-detail')

    class Meta:
        model = ProductCategory
        fields = '__all__'


class AdminProductClassSerializer(serializers.ModelSerializer, UpdateRelationMixin):
    url = serializers.HyperlinkedIdentityField(view_name='admin-product-class-detail')
    attributes = ProductAttributeSerializer(many=True, required=False)

    class Meta:
        model = ProductClass
        fields = '__all__'

    def create(self, validated_data):
        attributes = validated_data.pop('attributes', None)
        with transaction.atomic():
            self.instance = instance = super(AdminProductClassSerializer, self).create(validated_data)
            return self.update(instance, dict(validated_data=validated_data, attributes=attributes))

    def update(self, instance, validated_data):
        attributes = validated_data.pop('attributes', None)
        with transaction.atomic():
            updated_instance = super(AdminProductClassSerializer, self).update(instance, validated_data)
            self.update_relation("attributes", updated_instance.attributes, attributes)
            return updated_instance


class AdminStockRecordListSerializer(UpdateListSerializer):
    def select_existing_item(self, manager, datum):
        try:
            return manager.get(product=datum['product'], partner_sku=datum['partner_sku'])
        except manager.model.DoesNotExist:
            pass
        except manager.model.MultipleObjectsReturned:
            pass
        return None


class AdminStockRecordsSerializer(serializers.ModelSerializer):
    url = serializers.HyperlinkedIdentityField(view_name='admin-stockrecord-detail')
    product = serializers.PrimaryKeyRelatedField(required=False, queryset=Product.objects)
    partner_sku = serializers.CharField(validators=[], required=True)

    class Meta:
        list_serializer_class = AdminStockRecordListSerializer
        model = StockRecord
        fields = '__all__'

    def validate(self, attrs):
        if not attrs.get('partner_sku', None):
            raise serializers.ValidationError('A partner sku field is required')
        elif attrs.get('partner_sku') == '':
            raise serializers.ValidationError('A partner sku field cant be blank')
        return attrs


class AdminProductSerializer(BaseProductSerializer, UpdateRelationMixin):
    url = serializers.HyperlinkedIdentityField(view_name='admin-product-detail')
    stockrecords = AdminStockRecordsSerializer(required=False, many=True)
    category = serializers.SlugRelatedField(slug_field='slug', queryset=ProductCategory.objects, required=False)
    class Meta(BaseProductSerializer.Meta):
        fields = '__all__'

    def create(self, validated_data):
        attribute_values = validated_data.pop('attribute_values', None)
        stockrecords = validated_data.pop('stockrecords', None)
        with transaction.atomic():
            self.instance = instance = super().create(validated_data)
            return self.update(
                instance,
                dict(validated_data, attribute_values=attribute_values, stockrecords=stockrecords)
            )

    def update(self, instance, validated_data):
        attribute_values = validated_data.pop('attribute_values', None)
        stockrecords = validated_data.pop('stockrecords', None)
        with transaction.atomic():
            instance = super().update(instance, validated_data)
            product_class = instance.get_product_class()
            self.update_relation('attributes', instance.attribute_values, attribute_values)
            self.update_relation('stockrecords', instance.stockrecords, stockrecords)

            if self.partial:
                for attribute_value in instance.attribute_values.exclude(
                        attribute__product_class=product_class
                ):
                    attribute_value.delete()

        return instance._meta.model.objects.get(pk=instance.pk)





