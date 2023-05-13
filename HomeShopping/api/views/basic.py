from rest_framework import generics

from api.basket.operations import editable_baskets
from api.permissions import RequestAllowsAccessTo
from api.serializers.basket import BasketSerializer


class BasketList(generics.ListAPIView):
    serializer_class = BasketSerializer
    queryset = editable_baskets()

    # permission_classes = (RequestAllowAccessTo,)

    def get_queryset(self):
        basket = self.request.basket
        return self.queryset.filter(id=basket.id)


class BasketDetail(generics.RetrieveAPIView):
    serializer_class = BasketSerializer
    queryset = editable_baskets()
    permission_classes = (RequestAllowsAccessTo,)