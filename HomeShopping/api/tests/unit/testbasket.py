from django.urls import reverse

from api.tests.utils import APITest

from basket.models import Basket


class TestBasket(APITest):

    def test_retrieve_basket(self):
        # anonymous
        self.response = self.get('api-basket')
        self.response.assertStatusEqual(200)
        self.response.assertValueEqual('owner', None)

        # authenticated
        self.login('nobody', 'nobody')
        self.response = self.get('api-basket')
        self.response.assertStatusEqual(200)
        self.response.assertObjectIdEqual("owner", 2)
        basket_id = self.response['id']

        self.response = self.get('api-basket')
        self.response.assertStatusEqual(200)
        self.response.assertValueEqual('id', basket_id)

        self.login('admin', 'admin')
        self.response = self.get('api-basket')
        self.response.assertStatusEqual(200)
        self.response.assertObjectIdEqual("owner", 1)
        basket_id = self.response['id']

        self.response = self.get('api-basket')
        self.response.assertStatusEqual(200)
        self.response.assertValueEqual('id', basket_id)

        self.assertEqual(Basket.objects.all().count(), 2)

    def test_basket_read_permissions(self):
        self.login('nobody', 'nobody')
        self.response = self.get('api-basket')
        self.response.assertStatusEqual(200)

        basket_url = self.response['url']
        basket_lines = self.response['lines']

        self.response = self.get(basket_url)
        self.response.assertStatusEqual(200)

        self.response = self.get(basket_lines)
        self.response.assertStatusEqual(200)

        # create basket for somebody else
        basket = Basket.objects.create(owner_id=3)
        self.assertEqual(str(basket.owner), 'somebody')
        self.assertEqual(basket.pk, 2)

        # try to access somebody else's basket
        url = reverse('basket-detail', args=(2,))
        self.response = self.get(url)
        self.response.assertStatusEqual(403, "Script kiddies should fail to collect other users carts.")

        url = reverse('basket-lines-list', args=(2,))
        self.response = self.get(url)
        self.response.assertStatusEqual(403, "Script kiddies should fail to collect other users cart items.")

    def test_add_product_anonymous(self):
        # let's try to add product with wrong stockrecord
        self.response = self.post(
            'add-product',
            product="http://testserver/api/products/3/",
            quantity=1,
            stockrecord="http://testserver/api/products/1/stockrecords/1/",
        )
        self.response.assertStatusEqual(406)
        self.response.assertValueEqual('reason',  {'non_field_errors': ["Incorrect stockrecord"]})
        # basket is not saved for anonymous user
        self.response = self.get('api-basket')
        self.response.assertStatusEqual(200)
        self.response.assertValueEqual('id', None)
        self.response = self.post(
            'add-product',
            product='http://testserver/api/products/1/',
            quantity=4,
            stockrecord='http://testserver/api/products/1/stockrecords/1/',
        )
        self.response.assertStatusEqual(200)

        # check basket was created without owner
        self.response = self.get('api-basket')
        self.response.assertStatusEqual(200)
        self.response.assertValueEqual('id', 1)
        self.response.assertValueEqual('owner', None)

        lines = self.response['lines']
        # check our lines
        self.response = self.get(lines)
        self.response.assertStatusEqual(200)
        line0 = self.response.body[0]
        self.assertEqual(line0['product']['id'], 1)
        self.assertEqual(line0['quantity'], 4)

    def test_add_product_authenticated(self):
        self.login('nobody', 'nobody')
        self.response = self.post(
            'add-product',
            product='http://testserver/api/products/1/',
            quantity=4,
            stockrecord='http://testserver/api/products/1/stockrecords/1/',
        )
        self.response.assertStatusEqual(200)

        self.response = self.get('api-basket')
        self.response.assertStatusEqual(200)
        self.response.assertObjectIdEqual('owner', 2)

        lines = self.response['lines']
        self.response = self.get(lines)
        self.response.assertStatusEqual(200)
        line0 = self.response.body[0]
        self.assertEqual(line0['product']['id'], 1)
        self.assertEqual(line0['quantity'], 4)

    def test_basket_line_permissions(self):
        self.login('nobody', 'nobody')
        self.response = self.post(
            'add-product',
            product='http://testserver/api/products/1/',
            quantity=4,
            stockrecord='http://testserver/api/products/1/stockrecords/1/',
        )
        self.response = self.get('api-basket')
        self.response = self.get(self.response['lines'])
        self.response.assertStatusEqual(200)
        line0 = self.response.body[0]
        line0url = line0['url']

        self.response = self.get(line0url)
        self.response.assertStatusEqual(200)
        self.response.assertValueEqual('url', line0url)
        self.response.assertValueEqual('quantity', 4)

        self.login('somebody', 'somebody')
        self.response = self.get(line0url)
        self.response.assertStatusEqual(403)

    def test_total_price(self):
        self.response = self.post(
            'add-product',
            product='http://testserver/api/products/1/',
            quantity=4,
            stockrecord='http://testserver/api/products/1/stockrecords/1/',
        )
        self.response = self.get('api-basket')
        self.response.assertStatusEqual(200)
        self.response.assertValueEqual('total_price', '40.00')

    def test_add_product_above_stock(self):
        with self.subTest("Single request"):
            self.response = self.post(
                'add-product',
                product='http://testserver/api/products/1/',
                quantity=11,
                stockrecord='http://testserver/api/products/1/stockrecords/1/',
            )
            self.response.assertStatusEqual(406)
            self.response.assertValueEqual('reason', 'This quantity is not allowed.')

        with self.subTest("Sequential requests"):
            self.response = self.post(
                'add-product',
                product='http://testserver/api/products/1/',
                quantity=3,
                stockrecord='http://testserver/api/products/1/stockrecords/1/',
            )
            self.response.assertStatusEqual(200)

            self.response = self.post(
                'add-product',
                product='http://testserver/api/products/1/',
                quantity=8,
                stockrecord='http://testserver/api/products/1/stockrecords/1/',
            )
            self.response.assertStatusEqual(406)
            self.response.assertValueEqual('reason', 'This quantity is not allowed.')

    def test_adjust_basket_line_quantity(self):
        self.response = self.post(
            'add-product',
            product='http://testserver/api/products/1/',
            quantity=3,
            stockrecord='http://testserver/api/products/1/stockrecords/1/',
        )
        self.response.assertStatusEqual(200)

        self.response = self.get('api-basket')
        self.response.assertStatusEqual(200)

        self.response = self.get(self.response['lines'])
        basket_line_url = self.response[0]['url']

        self.response = self.get(basket_line_url)
        self.response = self.patch(basket_line_url, quantity=2)
        self.response.assertStatusEqual(200)

        # see if it's updated
        self.response = self.get(basket_line_url)
        self.response.assertStatusEqual(200)
        self.response.assertValueEqual("quantity", 2)

    def test_merge_baskets_updates_users_basket_lines(self):

        self.login('nobody', 'nobody')
        self.response = self.post(
            'add-product',
            product='http://testserver/api/products/1/',
            quantity=3,
            stockrecord='http://testserver/api/products/1/stockrecords/1/',
        )
        self.response.assertStatusEqual(200)

        self.delete('api-login')

        self.response = self.post(
            'add-product',
            product='http://testserver/api/products/1/',
            quantity=6,
            stockrecord='http://testserver/api/products/1/stockrecords/1/',
        )
        self.response.assertStatusEqual(200)

        self.login('nobody', 'nobody')
        self.response = self.get('api-basket')
        self.response.assertStatusEqual(200)
        self.response = self.get(self.response['lines'])
        line0 = self.response[0]
        self.assertEqual(line0['quantity'], 6)
        # anonymous's basket lines was deleted
        self.assertEqual(Basket.objects.get(pk=2).lines.count(), 0)

    def test_merge_baskets_adds_lines(self):

        self.response = self.post(
            'add-product',
            product='http://testserver/api/products/1/',
            quantity=4,
            stockrecord='http://testserver/api/products/1/stockrecords/1/',
        )
        self.response.assertStatusEqual(200)
        self.response = self.get('api-basket')
        self.response.assertStatusEqual(200)
        self.response.assertValueEqual('total_price', '40.00')

        self.login('nobody', 'nobody')
        self.response = self.get('api-basket')
        self.response.assertStatusEqual(200)
        self.response.assertValueEqual('total_price', '40.00')

    def test_merge_basket_doesnt_merge_users_basket(self):
        self.login('nobody', 'nobody')
        self.response = self.post(
            'add-product',
            product='http://testserver/api/products/1/',
            quantity=2,
            stockrecord='http://testserver/api/products/1/stockrecords/1/',
        )
        self.response.assertStatusEqual(200)

        self.response = self.get('api-basket')
        self.response.assertStatusEqual(200)
        self.response.assertValueEqual('total_price', '20.00')

        self.login('somebody', 'somebody')
        self.response = self.get('api-basket')
        self.response.assertStatusEqual(200)
        self.response.assertValueEqual('total_price', '0.00')

    def test_add_a_product_with_different_stockrecords(self):
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

        lines_url = self.response['lines']
        self.response = self.get(lines_url)
        self.response.assertStatusEqual(200)

        first_line = self.response[0]
        second_line = self.response[1]
        self.assertEqual(first_line['quantity'], 2)
        self.assertEqual(first_line['price'], '20.00')
        self.assertEqual(second_line['quantity'], 2)
        self.assertEqual(second_line['price'], '10.00')
