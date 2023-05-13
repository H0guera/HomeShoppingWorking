from rest_framework.generics import get_object_or_404

from api.permissions import RequestAllowsAccessTo

from basket.models import Basket


class BasketPermissionMixin(object):
    permission_class = (RequestAllowsAccessTo,)

    def check_basket_permission(self, request, basket_pk=None, basket=None):
        if basket is None:
            basket = get_object_or_404(Basket.objects, pk=basket_pk)
        self.check_object_permissions(request, basket)
        return basket
