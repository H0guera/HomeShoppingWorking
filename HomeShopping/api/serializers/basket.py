from django.contrib.auth.models import User

from rest_framework import serializers

from api.serializers.fields import DrillDownHyperlinkedIdentityField
from api.serializers.product import ProductSerializer

from basket.models import Basket, BasketLine


class BasketSerializer(serializers.HyperlinkedModelSerializer):
    lines = serializers.HyperlinkedIdentityField(
        view_name='basket-lines-list',
        many=False,
        read_only=True,
    )
    total_price = serializers.DecimalField(
        decimal_places=2,
        max_digits=12,
        required=False,
        read_only=True,
    )
    owner = serializers.HyperlinkedRelatedField(
        view_name='user-detail',
        required=False,
        allow_null=True,
        queryset=User.objects.all(),
    )

    class Meta:
        model = Basket
        fields = (
            'url',
            'id',
            'total_price',
            'lines',
            'owner',
        )


class BasketLineSerializer(serializers.HyperlinkedModelSerializer):
    url = DrillDownHyperlinkedIdentityField(
        view_name='basket-line-detail',
        extra_url_kwargs={'basket_pk': 'basket.id'},
    )
    product = ProductSerializer(read_only=True)
    price = serializers.DecimalField(
        decimal_places=2,
        max_digits=12,
        source='line_price',
        read_only=True,
    )
    allowed_quantity = serializers.IntegerField(source='stockrecord.net_stock_level', read_only=True)

    def validate(self, attrs):
        line = self.instance
        if attrs['quantity'] > line.available_quantity:
            message = "Cannot buy this quantity."
            raise serializers.ValidationError(message)
        return attrs

    class Meta:
        model = BasketLine
        fields = (
            'url',
            'price',
            'product',
            'quantity',
            'allowed_quantity',
        )
