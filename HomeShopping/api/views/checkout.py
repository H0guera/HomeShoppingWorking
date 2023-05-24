from rest_framework import generics, views, response, status

from api.basket.operations import parse_basket_from_hyperlink, request_allows_access_to_basket
from api.permissions import IsOwner
from api.serializers.checkout import OrderSerializer, OrderLineSerializer, OrderLineAttributeSerializer, \
    CheckoutSerializer
from order.models import Order, OrderLine, OrderLineAttribute


class OrderList(generics.ListAPIView):
    serializer_class = OrderSerializer
    permission_classes = (IsOwner,)

    def get_queryset(self):
        qs = Order.objects.all()
        return qs.filter(user=self.request.user)


class OrderDetail(generics.RetrieveAPIView):
    queryset = Order.objects.all()
    serializer_class = OrderSerializer
    permission_classes = (IsOwner,)


class OrderLineList(generics.ListAPIView):
    queryset = OrderLine.objects.all()
    serializer_class = OrderLineSerializer


class OrderLineDetail(generics.RetrieveAPIView):
    queryset = OrderLine.objects.all()
    serializer_class = OrderLineSerializer


class OrderLineAttributeDetail(generics.RetrieveAPIView):
    queryset = OrderLineAttribute.objects.all()
    serializer_class = OrderLineAttributeSerializer


class CheckoutView(views.APIView):
    order_serializer_class = OrderSerializer
    serializer_class = CheckoutSerializer

    def post(self, request, format=None, *args, **kwargs):
        basket = parse_basket_from_hyperlink(request.data, format)

        if not request_allows_access_to_basket(request, basket):
            return response.Response(
                "Unauthorized",
                status=status.HTTP_401_UNAUTHORIZED,
            )
        c_ser = self.serializer_class(data=request.data, context={"request": request})

        if c_ser.is_valid():
            order = c_ser.save()
            basket.freeze()
            o_ser = self.order_serializer_class(order, context={"request": request})
            resp = response.Response(o_ser.data)
            return resp
        return response.Response(c_ser.errors, status.HTTP_406_NOT_ACCEPTABLE)
