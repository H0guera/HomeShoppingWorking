from django.core.exceptions import ValidationError

from rest_framework import exceptions
from rest_framework.relations import HyperlinkedRelatedField

from basket.models import Basket, BasketLine

from HomeShopping import settings


def prepare_basket(basket, request):
    store_basket_in_session(basket, request.session)
    return basket


def get_basket(request, prepare=True):
    "Get basket from the request."
    if request.user.is_authenticated:
        basket = get_user_basket(request.user)
    else:
        basket = get_anonymous_basket(request)
        if basket is None:
            basket = Basket.objects.create()
            basket.save()
    return prepare_basket(basket, request) if prepare else basket


def get_basket_id_from_session(request):
    return request.session.get(settings.MY_BASKET_COOKIE_OPEN)


def get_anonymous_basket(request):
    "Get basket from session."

    basket_id = get_basket_id_from_session(request)
    try:
        basket = Basket.objects.get(pk=basket_id)
    except Basket.DoesNotExist:
        basket = None

    return basket


def get_user_basket(user):
    "get basket for a user."

    try:
        basket, __ = Basket.objects.get_or_create(owner=user)
    except Basket.MultipleObjectsReturned:
        # Not sure quite how we end up here with multiple baskets.
        # We merge them and create a fresh one
        old_baskets = list(Basket.open.filter(owner=user))
        basket = old_baskets[0]
        for other_basket in old_baskets[1:]:
            basket.merge(other_basket, add_quantities=False)

    return basket


def editable_baskets():
    return Basket.objects.filter(status__in=Basket.editable_statuses)


def request_allows_access_to_basket(request, basket):
    if basket.can_be_edited:
        if request.user.is_authenticated:
            return request.user == basket.owner

        return request.basket.id == basket.pk

    return False


def request_allows_access_to(request, obj):
    if isinstance(obj, Basket):
        return request_allows_access_to_basket(request, obj)

    basket = request.basket

    if isinstance(obj, BasketLine):
        if obj.basket.id == basket.id:
            return request_allows_access_to_basket(request, basket)

    return False


def store_basket_in_session(basket, session):
    session[settings.MY_BASKET_COOKIE_OPEN] = basket.pk
    session.save()


def parse_basket_from_hyperlink(DATA, format):  # pylint: disable=redefined-builtin
    "Parse basket from relation hyperlink"
    basket_parser = HyperlinkedRelatedField(
        view_name="basket-detail",
        queryset=Basket.objects,
        format=format,
    )
    try:
        basket_uri = DATA.get("basket")
        data_basket = basket_parser.to_internal_value(basket_uri)
    except ValidationError as e:
        raise exceptions.NotAcceptable(e.messages)
    else:
        print(data_basket)
        return data_basket
