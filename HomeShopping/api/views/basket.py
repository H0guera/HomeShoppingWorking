from rest_framework import status, generics
from rest_framework.response import Response
from rest_framework.views import APIView

from api.basket.operations import editable_baskets
from api.permissions import RequestAllowsAccessTo
from api.serializers.basket import BasketSerializer, BasketLineSerializer
from api.serializers.product import AddProductSerializer
from api.views.utils import BasketPermissionMixin
from basket.models import BasketLine


class BasketView(APIView):
    serializer_class = BasketSerializer

    def get(self, request, *args, **kwargs):  # pylint: disable=redefined-builtin

        basket = request.basket
        ser = self.serializer_class(basket, context={"request": request})
        return Response(ser.data)


class AddProductView(APIView):
    add_product_serializer_class = AddProductSerializer
    serializer_class = AddProductSerializer
    basket_serializer_class = BasketSerializer

    def validate(self, basket, product, quantity, stockrecord):
        if basket.pk:
            current_quantity = basket.current_quantity(product, stockrecord)
            desired_quantity = current_quantity + quantity
        else:
            desired_quantity = quantity

        if desired_quantity > stockrecord.num_in_stock:
            if stockrecord.num_in_stock < 1:
                message = 'This product is not available to buy now'
                return False, message
            message = "This quantity is not allowed."
            return False, message

    def post(self, request, *args, **kwargs):
        p_ser = self.add_product_serializer_class(data=request.data, context={"request": request})
        if p_ser.is_valid():
            product = p_ser.validated_data['product']
            quantity = p_ser.validated_data['quantity']
            stockrecord = p_ser.validated_data['stockrecord']
            basket_valid, message = self.validate(request.basket, product, quantity, stockrecord)
            if not basket_valid:
                return Response(
                    {"reason": message},
                    status=status.HTTP_406_NOT_ACCEPTABLE,
                )

            request.basket.add_product(product, stockrecord, quantity=quantity)
            ser = self.basket_serializer_class(request.basket, context={"request": request})
            return Response(ser.data)
        return Response({"reason": p_ser.errors}, status=status.HTTP_406_NOT_ACCEPTABLE)


class LineList(BasketPermissionMixin, generics.ListAPIView):
    queryset = BasketLine.objects.all()
    serializer_class = BasketLineSerializer
    permission_classes = (RequestAllowsAccessTo,)
    lookup_field = 'basket'

    def get_queryset(self):
        basket_pk = self.kwargs['pk']
        basket = self.check_basket_permission(self.request, basket_pk=basket_pk)
        return basket.lines.all()


class LineDetail(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = BasketLineSerializer
    queryset = BasketLine.objects.all()
    permission_classes = (RequestAllowsAccessTo,)

    def get_queryset(self):
        basket_pk = self.kwargs.get("basket_pk")
        basket = generics.get_object_or_404(editable_baskets(), pk=basket_pk)
        return basket.lines.all()