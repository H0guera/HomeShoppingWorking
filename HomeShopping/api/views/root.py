import collections

from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework.reverse import reverse


def PUBLIC_APIS(r, f):
    return [
        ("login", reverse("api-login", request=r, format=f)),
        ("basket", reverse("api-basket", request=r, format=f)),
        ("add-product", reverse("add-product", request=r, format=f)),
        ("baskets", reverse("baskets-list", request=r, format=f)),
        ("categories", reverse("category-list", request=r, format=f)),
        ("checkout", reverse("api-checkout", request=r, format=f)),
        ("orders", reverse("order-list", request=r, format=f)),
        ("products", reverse("product-list", request=r, format=f)),
    ]


def ADMIN_APIS(r, f):
    return [
        ("productclasses", reverse("admin-product-class-list", request=r, format=f)),
        ("products", reverse("admin-product-list", request=r, format=f)),
        ("categories", reverse("admin-categories-list", request=r, format=f)),
        ("users", reverse("admin-user-list", request=r, format=f)),
    ]


@api_view(("GET",))
def api_root(request, format=None, *args, **kwargs):  # pylint: disable=redefined-builtin
    """
    GET:
    Display all available urls.
    Since some urls have specific permissions, you might not be able to access
    them all.
    """
    apis = PUBLIC_APIS(request, format)

    if request.user.is_staff:
        apis += [("admin", collections.OrderedDict(ADMIN_APIS(request, format)))]

    return Response(collections.OrderedDict(apis))
