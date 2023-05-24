import json
from re import match

from django.contrib.auth.models import User
from django.http import SimpleCookie
from django.test import TestCase
from django.urls import NoReverseMatch, reverse

from product.models import ProductClass, Product, ProductCategory, StockRecord, ProductAttribute


class APITest(TestCase):

    def setUp(self) -> None:
        User.objects.create_user(
            id=1, username='admin',
            email='admin@admin.adm',
            password='admin',
            is_staff=True,
            is_superuser=True,
        )

        user = User.objects.create_user(
            id=2,
            username='nobody',
            email='nobody@nobody.nbd',
            password='nobody',

        )
        user.is_stuff = False
        user.is_superuser = False
        user.save()

        user = User.objects.create_user(id=3, username='somebody', email='somebody@somebody.smb', password='somebody')
        user.is_stuff = False
        user.is_superuser = False
        user.save()

    def login(self, username, password):
        result = self.client.login(username=username, password=password)
        self.assertTrue(result, "%s should be able to log in" % username)
        return True

    def hlogin(self, username, password, session_id):
        response = self.post(
            'api-login', session_id, username=username, password=password)
        response.assertEqual(response.status_code, 200, "%s should be able to login via the api" % username)

    def api_call(self, url_name, method, session_id=None, authenticated=False, **data):
        try:
            url = reverse(url_name)
        except NoReverseMatch:
            url = url_name
        method = getattr(self.client, method.lower())
        kwargs = {"content_type": "application/json"}
        if session_id is not None:
            auth_type = 'AUTH' if authenticated else 'ANON'
            kwargs["HTTP_SESSION_ID"] = "SID:%s:testserver:%s" % (auth_type, session_id)

        response = None
        if data:
            response = method(url, json.dumps(data), **kwargs)
        else:
            response = method(url, **kwargs)

        if session_id is not None:
            self.client.cookies = SimpleCookie()

        return response

    def get(self, url, session_id=None, authenticated=False):
        method = 'GET'
        return self.api_call(url, method, session_id, authenticated)

    def post(self, url, session_id=None, authenticated=False, **data):
        method = 'POST'
        return self.api_call(url, method, session_id=session_id, authenticated=authenticated, **data)

    def put(self, url, session_id=None, authenticated=False, **data):
        method = 'PUT'
        return self.api_call(url, method, session_id=session_id, authenticated=authenticated, **data)

    def patch(self, url, session_id=None, authenticated=False, **data):
        method = 'PATCH'
        return self.api_call(url, method, session_id=session_id, authenticated=authenticated, **data)

    def delete(self, url, session_id=None, authenticated=False):
        method = 'DELETE'
        return self.api_call(url, method, session_id, authenticated)

    def tearDown(self):
        User.objects.get(username='admin').delete()
        User.objects.get(username='nobody').delete()

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.product_class = ProductClass.objects.create(name='t-shirts', slug='t-shirts')
        cls.product_class2 = ProductClass.objects.create(name='sneaker', slug='sneaker')
        cls.attribute = ProductAttribute.objects.create(
            name='size',
            code='size',
            type='text',
            product_class=cls.product_class,
        )
        cls.attribute = ProductAttribute.objects.create(
            name='color',
            code='color',
            type='text',
            product_class=cls.product_class,
            required=True,
        )
        cls.attribute = ProductAttribute.objects.create(
            name='size',
            code='size',
            type='integer',
            product_class=cls.product_class2,
        )
        cls.category = ProductCategory.objects.create(title='Male', slug='male')
        cls.standalone_product = Product.objects.create(
            title='standalone_product',
            article='standalone_product',
            category=cls.category,
            product_class=cls.product_class,
        )
        cls.parent_product = Product.objects.create(
            structure='parent',
            title='parent_product',
            article='parent_product',
            category=cls.category,
            product_class=cls.product_class,
        )
        cls.child_product = Product.objects.create(
            structure='child',
            title='child_product',
            article='child_product',
            parent=cls.parent_product,
        )
        cls.stockrecord = StockRecord.objects.create(
            partner_sku='partner1',
            product=cls.standalone_product,
            num_in_stock=10,
            price=10,
            owner=User.objects.create(id=4, username='partner', password='partner', email='partner@partn.er'),
        )
        cls.stockrecord = StockRecord.objects.create(
            partner_sku='partner2',
            product=cls.standalone_product,
            num_in_stock=5,
            price=5,
            owner=User.objects.create(id=5, username='partner2', password='partner2', email='partner2@partn.er'),
        )

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()

    @property
    def response(self):
        return self._response

    @response.setter
    def response(self, response):
        self._response = ParsedResponse(response, self)


class ParsedResponse(object):
    def __init__(self, response, testcase):
        self.response = response
        self.t = testcase

    @property
    def response(self):
        return self._response

    @response.setter
    def response(self, response):
        self._response = response
        self.status_code = response.status_code
        try:
            self.body = response.data
        except Exception:
            self.body = None

    def __getattr__(self, name):
        return getattr(self._response, name)

    def __getitem__(self, name):
        return self.body[name]

    def __len__(self):
        return len(self.body)

    def assertStatusEqual(self, code, message=None):
        self.t.assertEqual(self.status_code, code, message)

    def assertValueEqual(self, value_name, value, message=None):
        self.t.assertEqual(self[value_name], value, message)

    def assertObjectIdEqual(self, value_name, value, message=None):
        pattern = r".*?%s.*?/(?P<object_id>\d+)/?" % reverse('api-root')
        match_object = match(pattern, self[value_name])
        if match_object:
            object_id = int(match_object.groupdict()['object_id'])
        else:
            object_id = None
        self.t.assertEqual(object_id, value, message)

    def __str__(self):
        return str(self._response)
