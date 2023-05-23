from django.core.signing import BadSignature, Signer
from django.utils.functional import SimpleLazyObject, empty

from basket.models import Basket

from HomeShopping import settings


class BasketMiddleware:
    def __init__(self, get_response):
        self._get_response = get_response

    def __call__(self, request):
        request.cookies_to_delete = []
        request._basket_cache = None

        def load_full_basket():
            """
            Return the basket after applying offers.
            """
            basket = self.get_basket(request)

            return basket

        def load_basket_hash():
            """
            Load the basket and return the basket hash
            Note that we don't apply offers or check that every line has a
            stockrecord here.
            """
            basket = self.get_basket(request)
            if basket.id:
                return self.get_basket_hash(basket.id)

        request.basket = SimpleLazyObject(load_full_basket)
        request.basket_hash = SimpleLazyObject(load_basket_hash)

        response = self._get_response(request)
        return self.process_response(request, response)

    def process_response(self, request, response):
        # Delete any surplus cookies
        cookies_to_delete = getattr(request, 'cookies_to_delete', [])
        for cookie_key in cookies_to_delete:
            response.delete_cookie(cookie_key)

        if not hasattr(request, 'basket'):
            return response

        # If the basket was never initialized we can safely return
        if (isinstance(request.basket, SimpleLazyObject) and request.basket._wrapped is empty):
            return response

        cookie_key = self.get_cookie_key(request)
        # Check if we need to set a cookie. If the cookies is already available
        # but is set in the cookies_to_delete list then we need to re-set it.
        has_basket_cookie = (cookie_key in request.COOKIES and cookie_key not in cookies_to_delete)
        # If a basket has had products added to it, but the user is anonymous
        # then we need to assign it to a cookie
        if (request.basket.id and not request.user.is_authenticated
                and not has_basket_cookie):
            cookie = self.get_basket_hash(request.basket.id)
            response.set_cookie(
                cookie_key, cookie,
                max_age=settings.MY_BASKET_COOKIE_LIFETIME,
                secure=settings.MY_BASKET_COOKIE_SECURE,
                httponly=True)
        return response

    def get_cookie_key(self, request):
        """
        Returns the cookie name to use for storing a cookie basket.
        The method serves as a useful hook in multi-site scenarios where
        different baskets might be needed.
        """
        return settings.MY_BASKET_COOKIE_OPEN

        # Helper methods

    def get_basket(self, request):
        """
        Return the open basket for this request
        """
        if request._basket_cache is not None:
            return request._basket_cache

        num_baskets_merged = 0
        manager = Basket.open
        cookie_key = self.get_cookie_key(request)
        cookie_basket = self.get_cookie_basket(cookie_key, request)
        if hasattr(request, 'user') and request.user.is_authenticated:
            # Signed-in user: if they have a cookie basket too, it means
            # that they have just signed in and we need to merge their cookie
            # basket into their user basket, then delete the cookie.
            try:
                basket, __ = manager.get_or_create(owner=request.user)
            except Basket.MultipleObjectsReturned:
                # Not sure quite how we end up here with multiple baskets.
                # We merge them and create a fresh one
                old_baskets = list(manager.filter(owner=request.user))
                basket = old_baskets[0]
                for other_basket in old_baskets[1:]:
                    self.merge_baskets(basket, other_basket)
                    num_baskets_merged += 1

            # Assign user onto basket to prevent further SQL queries when
            # basket.owner is accessed.
            basket.owner = request.user

            if cookie_basket:
                self.merge_baskets(basket, cookie_basket)
                num_baskets_merged += 1
                request.cookies_to_delete.append(cookie_key)

        elif cookie_basket:
            # Anonymous user with a basket tied to the cookie
            basket = cookie_basket
        else:
            # Anonymous user with no basket - instantiate a new basket
            # instance.  No need to save yet.
            basket = Basket()

        # Cache basket instance for the during of this request
        request._basket_cache = basket

        return basket

    def merge_baskets(self, master, slave):
        master.merge(slave, add_quantities=False)

    def get_cookie_basket(self, cookie_key, request):  # manager):
        # """
        # Looks for a basket which is referenced by a cookie.
        # If a cookie key is found with no matching basket, then we add
        # it to the list to be deleted.
        # """
        basket = None
        if cookie_key in request.COOKIES:
            basket_hash = request.COOKIES[cookie_key]
            try:
                basket_id = Signer().unsign(basket_hash)
                basket = Basket.objects.get(pk=basket_id, owner=None,
                                            status=Basket.OPEN)
            except (BadSignature, Basket.DoesNotExist):
                request.cookies_to_delete.append(cookie_key)
        return basket

    def get_basket_hash(self, basket_id):
        return Signer().sign(basket_id)
