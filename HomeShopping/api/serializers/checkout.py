from rest_framework import serializers, exceptions

from api.serializers.fields import DrillDownHyperlinkedRelatedField
from api.serializers.mixins import OrderPlacementMixin
from api.serializers.product import ProductSerializer
from basket.models import Basket
from order.models import ShippingAddress, OrderLineAttribute, OrderLine, Order
from product.models import StockRecord


class ShippingAddressSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = ShippingAddress
        fields = '__all__'


class InlineShippingAddressSerializer(serializers.ModelSerializer):
    class Meta:
        model = ShippingAddress
        fields = "__all__"


class OrderLineAttributeSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = OrderLineAttribute
        fields = ('url', 'value')


class OrderLineSerializer(serializers.HyperlinkedModelSerializer):
    url = serializers.HyperlinkedIdentityField(view_name="orderline-detail")
    stockrecord = DrillDownHyperlinkedRelatedField(
        view_name="product-stockrecord-detail",
        extra_url_kwargs={"product_pk": "product_id"},
        queryset=StockRecord.objects.all(),
    )
    product = ProductSerializer(read_only=True)
    attributes = OrderLineAttributeSerializer(
        many=True,
        required=False,
    )

    class Meta:
        model = OrderLine
        fields = '__all__'


class OrderSerializer(serializers.HyperlinkedModelSerializer):
    owner = serializers.HyperlinkedRelatedField(
        view_name="user-detail",
        read_only=True,
        source="user",
    )
    shipping_address = InlineShippingAddressSerializer(many=False, required=False)
    email = serializers.EmailField(read_only=True)
    lines = OrderLineSerializer(many=True)

    class Meta:
        model = Order
        fields = '__all__'


class CheckoutSerializer(serializers.Serializer, OrderPlacementMixin):
    basket = serializers.HyperlinkedRelatedField(
        view_name="basket-detail",
        queryset=Basket.objects,
    )
    guest_email = serializers.EmailField(allow_blank=True, required=False)
    total = serializers.DecimalField(decimal_places=2, max_digits=12, required=False)
    shipping_address = ShippingAddressSerializer(many=False, required=False)

    @property
    def request(self):
        return self.context["request"]

    def validate(self, attrs):
        request = self.request
        if request.user.is_anonymous:
            if not attrs.get("guest_email"):
                # Always require the guest email field if the user is anonymous
                message = "Guest email is required for anonymous checkouts"
                raise serializers.ValidationError(message)

        basket = attrs.get("basket")
        if basket.num_items() <= 0:
            message = "Cannot checkout with empty basket"
            raise serializers.ValidationError(message)
        total = basket.total_price

        attrs["order_total"] = total
        return attrs

    def create(self, validated_data):
        try:
            basket = validated_data['basket']
            order_number = self.generate_order_number(basket)
            request = self.request
            if 'shipping_address' in validated_data:
                shipping_address = ShippingAddress(**validated_data["shipping_address"])
            else:
                shipping_address = None
            return self.place_order(
                basket=basket,
                order_number=order_number,
                user=request.user,
                shipping_address=shipping_address,
                order_total=validated_data.get('order_total'),
                guest_email=validated_data.get('guest_email') or '',
            )
        except ValueError as e:
            raise exceptions.NotAcceptable(str(e))
