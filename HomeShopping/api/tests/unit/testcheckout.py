from decimal import Decimal

from django.contrib.auth.models import User
from django.test.client import RequestFactory
from django.urls import reverse

from basket.models import Basket
from order.models import Order, ShippingAddress
from api.serializers.checkout import CheckoutSerializer
from api.tests.utils import APITest


class CheckoutTest(APITest):

    def _get_common_payload(self, basket_url):
        return {
            "basket": basket_url,
            "guest_email": "foo@example.com",
            "total": "50.0",
            "shipping_address": {
                "first_name": "Henk",
                "last_name": "Van den Heuvel",
                "line1": "Roemerlaan 44",
                "notes": "Niet STUK MAKEN OK!!!!",
                "phone_number": "+31 26 370 4887",
            },
        }

    def test_checkout_serializer_validation(self):
        self.login('nobody', 'nobody')

        # first create a basket and a checkout payload
        self.response = self.post(
            'add-product',
            product='http://testserver/api/products/1/',
            quantity=3,
            stockrecord='http://testserver/api/products/1/stockrecords/1/',
        )
        self.response.assertStatusEqual(200)
        self.response = self.get('api-basket')
        payload = self._get_common_payload(self.response['url'])

        # create a request and user for the serializer
        rf = RequestFactory()
        request = rf.post("/checkout", **payload)
        request.user = User.objects.get(username="nobody")

        serializer = CheckoutSerializer(data=payload, context={'request': request})
        self.assertTrue(serializer.is_valid())
        self.assertEqual(serializer.validated_data['total'], Decimal('50.00'))
        self.assertEqual(serializer.validated_data['order_total'], Decimal('30.00'))

    def test_checkout(self):
        self.login('nobody', 'nobody')
        response = self.get('api-basket')
        basket = response.data

        payload = self._get_common_payload(basket['url'])
        self.response = self.post('api-checkout', **payload)
        self.response.assertStatusEqual(406)
        # when basket is empty, checkout should raise an error
        self.response.assertValueEqual(
            'non_field_errors',
            ["Cannot checkout with empty basket"],
        )

        self.response = self.post(
            'add-product',
            product='http://testserver/api/products/1/',
            quantity=1,
            stockrecord='http://testserver/api/products/1/stockrecords/1/',
        )
        self.response.assertStatusEqual(200)

#        let's try to change total price for order
        payload['order_total'] = 50
        self.response = self.post('api-checkout', **payload)
        self.response.assertStatusEqual(200)
        self.response.assertValueEqual('email', 'nobody@nobody.nbd')
#        order's total price is correct
        self.response.assertValueEqual('total', '10.00')
        self.assertEqual(
            Basket.objects.get(pk=1).status,
            'Frozen',
            "Basket should be frozen after placing order and before payment",
        )
        self.response = self.get('order-list')
        self.response.assertStatusEqual(200)

    def test_anonymous_checkout(self):
        self.response = self.post(
            'add-product',
            product='http://testserver/api/products/1/',
            quantity=2,
            stockrecord='http://testserver/api/products/1/stockrecords/1/',
        )
        self.response.assertStatusEqual(200)

        self.response = self.get('api-basket')
        self.response.assertStatusEqual(200)

        # No guest email specified should say 406
        payload = self._get_common_payload(self.response['url'])
        del payload['guest_email']

        self.response = self.post('api-checkout', **payload)
        print(self.response.data)
        self.response.assertValueEqual(
            'non_field_errors',
            ["Guest email is required for anonymous checkouts"],
        )
        self.response.assertStatusEqual(406)
        self.assertEqual(ShippingAddress.objects.count(), 0)

        # An empty email address should say this as well
        payload['guest_email'] = ''
        response = self.post('api-checkout', **payload)
        self.assertEqual(response.status_code, 406)

        self.response = self.get('api-basket')
        self.response.assertStatusEqual(200)

        payload = self._get_common_payload(self.response['url'])
        self.response = self.post('api-checkout', **payload)
        self.response.assertStatusEqual(200)
        self.response.assertValueEqual('email', 'foo@example.com')
        self.assertEqual(
            Basket.objects.get(pk=1).status,
            'Frozen',
            "Basket should be frozen after placing order and before payment",
        )
        self.assertEqual(ShippingAddress.objects.count(), 1)

    def test_checkout_creates_an_order(self):
        """After checkout has been done, a user should have gained an order object."""
        # first create an anonymous order
        self.test_anonymous_checkout()
        self.assertEqual(Order.objects.all().count(), 1)

        self.login('nobody', 'nobody')
        self.test_checkout()
        self.response = self.get('order-list')
        self.response.assertStatusEqual(200)
        self.assertEqual(len(self.response), 1, "An order should have been created.")
        order_line = self.response[0]['lines']
        self.assertEqual(len(order_line), 1)

        order_line_url = order_line[0]['url']
        self.response = self.get(order_line_url)
        self.response.assertStatusEqual(200)
        self.response.assertValueEqual('quantity', 1)

    def test_checkout_permissions(self):
        """Prove that someone cannot check out someone else's cart by mistake."""
        self.login('nobody', 'nobody')
        self.response = self.get('api-basket')
        basket = self.response.data
        nobody_basket_url = basket['url']

        self.client.logout()

        self.login('somebody', 'somebody')
        self.response = self.post(
            'add-product',
            product='http://testserver/api/products/1/',
            quantity=2,
            stockrecord='http://testserver/api/products/1/stockrecords/1/',
        )
        self.response.assertStatusEqual(200)

        # So let's checkout with nobody's basket WHAHAAAHAHA!
        payload = self._get_common_payload(nobody_basket_url)

        self.response = self.post('api-checkout', **payload)
        self.response.assertStatusEqual(401)
        self.assertEqual(self.response.data, "Unauthorized")

    def test_basket_immutable_after_checkout(self):
        """Prove that the cart can not be changed after checkout."""
        self.login('nobody', 'nobody')
        self.response = self.get('api-basket')
        basket = self.response.data

        self.response = self.post(
            'add-product',
            product='http://testserver/api/products/1/',
            quantity=2,
            stockrecord='http://testserver/api/products/1/stockrecords/1/',
        )

        payload = self._get_common_payload(basket['url'])
        self.response = self.post('api-checkout', **payload)
        self.response.assertStatusEqual(200)
        self.assertEqual(
            Basket.objects.get(pk=basket["id"]).status,
            'Frozen',
            "Basket should be frozen after placing order and before payment",
        )

        url = reverse('basket-detail', args=(basket['id'],))

        self.response = self.client.get(url)
        self.response.assertStatusEqual(404)  # Frozen basket can not be accessed

    def test_checkout_a_product_with_different_stockrecords(self):
        self.login('nobody', 'nobody')
        self.response = self.post(
            'add-product',
            product='http://testserver/api/products/1/',
            quantity=2,
            stockrecord='http://testserver/api/products/1/stockrecords/1/',
        )
        self.response.assertStatusEqual(200)
        self.response = self.post(
            'add-product',
            product='http://testserver/api/products/1/',
            quantity=2,
            stockrecord='http://testserver/api/products/1/stockrecords/2/',
        )
        self.response.assertStatusEqual(200)
        self.response = self.get('api-basket')
        self.response.assertStatusEqual(200)

        basket_url = self.response['url']
        payload = self._get_common_payload(basket_url)
        self.response = self.post('api-checkout', **payload)
        self.response.assertStatusEqual(200)
        self.response.assertValueEqual('total', '30.00')

    def test_stockrecords_after_checkout(self):
        self.test_checkout_a_product_with_different_stockrecords()

        self.response = self.get('http://testserver/api/products/1/stockrecords/1/')
        self.response.assertValueEqual('num_in_stock', 8)

        self.response = self.get('http://testserver/api/products/1/stockrecords/2/')
        self.response.assertValueEqual('num_in_stock', 3)
