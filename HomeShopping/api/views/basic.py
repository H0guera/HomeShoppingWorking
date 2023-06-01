from django.db.models import Prefetch
from rest_framework import generics

from api.basket.operations import editable_baskets
from api.permissions import RequestAllowsAccessTo
from api.serializers.basket import BasketSerializer
from basket.models import BasketLine


class BasketList(generics.ListAPIView):
    serializer_class = BasketSerializer
    queryset = editable_baskets()

    def get_queryset(self):
        basket = self.request.basket
        return self.queryset.filter(id=basket.id)


class BasketDetail(generics.RetrieveAPIView):
    serializer_class = BasketSerializer
    queryset = editable_baskets().select_related('owner').prefetch_related(Prefetch(
            'lines', queryset=BasketLine.objects.all().select_related('stockrecord')))
    permission_classes = (RequestAllowsAccessTo,)
