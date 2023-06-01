import decimal

from django.urls import reverse

from api.serializers.admin.product import AdminStockRecordsSerializer, AdminProductSerializer
from api.tests.utils import APITest
from product.models import Product, ProductClass


class ProductTest(APITest):

    def test_get(self):
        url = reverse('product-list')
        self.response = self.get(url)
        self.response.assertStatusEqual(200)
        self.assertEqual(len(self.response.data), 3)
        product = self.response.body[0]
        default_fields = ['id', 'url']
        for field in default_fields:
            self.assertIn(field, product)

    def test_product_list_filter(self):
        standalone_products_url = '%s?structure=standalone' % reverse('product-list')
        self.response = self.get(standalone_products_url)
        self.response.assertStatusEqual(200)
        self.assertEqual(len(self.response.body), 1)

        parent_products_url = '%s?structure=parent' % reverse('product-list')
        self.response = self.get(parent_products_url)
        self.response.assertStatusEqual(200)
        self.assertEqual(len(self.response.body), 1)

        child_products_url = '%s?structure=child' % reverse('product-list')
        self.response = self.get(child_products_url)
        self.response.assertStatusEqual(200)
        self.assertEqual(len(self.response.body), 1)

        koe_products_url = '%s?structure=koe' % reverse("product-list")
        self.response = self.get(koe_products_url)
        self.response.assertStatusEqual(200)
        self.assertEqual(len(self.response.body), 0)

    def test_product_detail(self):
        "Check product details"
        self.response = self.get(reverse('product-detail', args=(1,)))
        self.response.assertStatusEqual(200)
        default_fields = (
            'url',
            'id',
            'title',
            'structure',
            'description',
            'attributes',
            'category',
            'product_class',
            'children',
        )
        for field in default_fields:
            self.assertIn(field, self.response.body)

        self.response.assertValueEqual('title', 'standalone_product')


class _ProductSerializerTest(APITest):
    def assertErrorStartsWith(self, ser, name, errorstring):
        self.assertTrue(
            ser.errors[name][0].startswith(errorstring),
            "Error '%s' does not start with '%s" % (ser.errors[name][0], errorstring),
        )


class AdminStockRecordSerializerTest(_ProductSerializerTest):
    def test_stockrecord_create_and_update(self):
        "The AdminStockRecordSerializer should be able to save stuff"
        self.login('admin', 'admin')
        self.response = self.get(reverse('api-root'))
        request = self.response.wsgi_request
        ser = AdminStockRecordsSerializer(
            data={
                "product": 1,
                "partner_sku": "henk",
                "price": 20,
                "num_in_stock": 34,
            },
            context={"request":  request},
        )
        self.assertTrue(ser.is_valid(), "There where errors %s" % ser.errors)
        obj = ser.save()
        self.assertEqual(obj.product.get_title(), 'standalone_product')
        self.assertEqual(obj.price, decimal.Decimal('20.00'))
        self.assertEqual(obj.owner.username, 'admin')
        # update
        ser = AdminStockRecordsSerializer(
            data={
                "partner_sku": "henk",
                "price": 15,
                "num_in_stock": 15,
            },
            instance=obj,
            context={"request": request},
        )
        self.assertTrue(ser.is_valid(), "There where errors %s" % ser.errors)
        obj = ser.save()
        self.assertEqual(obj.product.get_title(), 'standalone_product')
        self.assertEqual(obj.price, decimal.Decimal('15.00'))
        self.assertEqual(obj.num_in_stock, 15)
        self.assertEqual(obj.owner.username, 'admin')


class AdminProductSerializerTest(_ProductSerializerTest):
    def test_create_product_with_stockrecords(self):
        "Products should be created by the serializer if needed"
        self.login('admin', 'admin')
        self.response = self.get(reverse('api-root'))
        request = self.response.wsgi_request
        ser = AdminProductSerializer(
            data={
                "product_class": "t-shirts",
                "title": "test",
                "stockrecords": [
                    {
                        "partner_sku": "grisha",
                        "num_in_stock": 5,
                        "price": "53.67",
                    },
                ],
            },
            context={"request": request},
        )
        self.assertTrue(ser.is_valid(), "Something wrong %s" % ser.errors)
        obj = ser.save()
        self.assertEqual(obj.pk, 4, "Should be new object, with a high pk")
        self.assertEqual(obj.product_class.slug, 't-shirts')
        self.assertEqual(obj.stockrecords.count(), 1)
        self.assertEqual(obj.title, 'test')

    def test_modify_product(self):
        "We should a able to change product fields."
        product = Product.objects.get(pk=1)

        ser = AdminProductSerializer(
            data={
                "description": "Henk",
            },
            instance=product,
            partial=True,
        )
        self.assertTrue(ser.is_valid(), "Something wrong %s" % ser.errors)
        obj = ser.save()
        self.assertEqual(obj.pk, 1, "product should be the same as passed as instance")
        self.assertEqual(obj.description, 'Henk')

    def test_add_attribute_to_product(self):
        product = Product.objects.get(pk=1)

        self.assertEqual(product.product_class.slug, 't-shirts')
        x = product.product_class.attributes.get(code='size')
        self.assertEqual(x.type, 'text')

        ser = AdminProductSerializer(
            data={
                "attributes": [
                    {"code": "size", "value": "large"},
                    {"code": "color", "value": "green"},
                ],
            },
            instance=product,
            partial=True,
        )
        self.assertTrue(ser.is_valid(), "Something wrong %s" % ser.errors)
        obj = ser.save()
        self.assertEqual(obj.pk, 1, "product should be the same as passed as instance")
        self.assertEqual(obj.product_class.slug, 't-shirts')
        return obj

    def test_modify_product_error(self):
        """When modifying an attribute, enough information should be passed to be
        able to identify the attribute. An error message should indicate
        missing information"""
        product = Product.objects.get(pk=1)

        ser = AdminProductSerializer(
            data={
                "attributes": [{"name": "Text", "value": "go go"}],
            },
            instance=product,
            partial=True,
        )
        self.assertFalse(ser.is_valid(), "Should fail because of missing code")
        self.assertDictEqual(
            ser.errors, {'attributes': [{"code": "This field is required."}]},
        )

    def test_switch_product_class(self):
        """When the product class is switched, the product should only have
        attributes from the new product class."""
        product = self.test_add_attribute_to_product()
        self.assertEqual(product.attribute_values.count(), 2)

        ser = AdminProductSerializer(
            data={
                "product_class": "sneaker",
                "attributes": [{"code": "size", "value": 40}],
            },
            instance=product,
            partial=True,
        )
        self.assertTrue(ser.is_valid(), "Something wrong %s" % ser.errors)
        obj = ser.save()
        self.assertEqual(obj.pk, 1)
        self.assertEqual(obj.product_class.slug, 'sneaker')
        self.assertEqual(product.attribute_values.count(), 1)
        self.assertEqual(product.attribute_values.first().value, 40)

    def test_add_stockrecords_and_update(self):
        "Stockrecords should be added when new."
        product = Product.objects.get(pk=3)
        self.assertEqual(product.stockrecords.count(), 0)
        # we need to request for owner's hidden field
        self.login('admin', 'admin')
        self.response = self.get(reverse('api-root'))
        request = self.response.wsgi_request

        ser = AdminProductSerializer(
            data={
                "stockrecords": [
                    {
                        "partner_sku": "grisha",
                        "num_in_stock": 5,
                        "price": "53.67",
                    },
                ],
            },
            instance=product,
            context={'request': request},
            partial=True,
        )

        self.assertTrue(ser.is_valid(), "Something wrong %s" % ser.errors)
        obj = ser.save()
        self.assertEqual(obj.stockrecords.count(), 1)

        ser = AdminProductSerializer(
            data={
                "stockrecords": [
                    {
                        "partner_sku": "grisha",
                        "num_in_stock": 15,
                    },
                ],
            },
            instance=obj,
            context={'request': request},
            partial=True,
        )

        self.assertTrue(ser.is_valid(), "Something wrong %s" % ser.errors)
        obj = ser.save()
        self.assertEqual(obj.stockrecords.count(), 1)
        self.assertEqual(obj.stockrecords.first().num_in_stock, 15)

    def test_add_category(self):
        product = Product.objects.get(pk=1)
        ser = AdminProductSerializer(
                data={
                    "category": "male",
                },
                instance=product,
                partial=True,
            )

        self.assertTrue(ser.is_valid(), "Something wrong %s" % ser.errors)
        obj = ser.save()
        self.assertEqual(obj.category.title, 'Male')


class TestProductAdmin(APITest):
    default_data = {
        "title": "testproduct",
        "article": "testproduct",
        "product_class": "t-shirts",
        "stockrecords": [
            {
                "partner_sku": "testsku",
                "num_in_stock": 10,
                "price": 10,
            },
        ],
        "category": "male",
        "attributes": [
            {
               "code": "size",
               "value": "Large",
            },
            {
                "code": "color",
                "value": "green",
            },
        ],
    }

    def test_post_product(self):
        self.assertEqual(Product.objects.count(), 3)
        self.login('admin', 'admin')

        data = self.default_data.copy()
        self.response = self.post('admin-product-list', **data)
        self.response.assertStatusEqual(201)
        self.assertEqual(Product.objects.count(), 4)

        data = self.default_data.copy()
        data['structure'] = 'parent'
        data['title'] = 'testparent'
        data['article'] = 'testparent'
        data.pop('stockrecords')
        self.response = self.post('admin-product-list', **data)
        self.response.assertStatusEqual(201)
        self.assertEqual(Product.objects.count(), 5)

    def test_patch_product(self):
        self.login('admin', 'admin')
        url = reverse('admin-product-detail', args=(1,))
        self.response = self.patch(
            url,
            **{
                "stockrecords": [
                    {
                        "partner_sku": "testsku",
                        "num_in_stock": 10,
                        "price": 10,
                    },
                ],
                "attributes": [
                    {
                        "code": "size",
                        "value": "Large",
                    },
                    {
                        "code": "color",
                        "value": "green",
                    },
                ],
            },
        )
        self.response.assertStatusEqual(200)

    def test_patch_child(self):
        self.login('admin', 'admin')
        url = reverse('admin-product-detail', args=(3,))
        self.response = self.patch(
            url,
            **{
                "stockrecords": [
                    {
                        "partner_sku": "testsku",
                        "num_in_stock": 10,
                        "price": 10,
                    },
                ],
                "attributes": [
                    {
                        "code": "size",
                        "value": "Large",
                    },
                    {
                        "code": "color",
                        "value": "green",
                    },
                ],
            },
        )
        self.response.assertStatusEqual(200)

    def test_child_error(self):
        self.login('admin', 'admin')
        url = reverse('admin-product-detail', args=(3,))
        self.response = self.patch(
            url,
            **{
                "attributes": [
                    {
                        "code": "size",
                        "value": 1,
                    },
                ],
            },
        )
        self.response.assertStatusEqual(400)
        error = str(self.response['attributes'][0]['value'][0])
        self.assertEqual(
            error,
            "Error assigning `1` to size, Must be str.",
        )


class TestProductClass(APITest):
    def test_post_product_class(self):
        self.login('admin', 'admin')
        self.assertEqual(ProductClass.objects.count(), 2)
        data = {
            "name": "testpc",
            "slug": "testpc",
        }
        self.response = self.post('admin-product-class-list', **data)
        self.response.assertStatusEqual(201, self.response.data)
        self.assertEqual(ProductClass.objects.count(), 3)

    def test_patch_add_attributes(self):
        self.test_post_product_class()
        # self.login("admin", "admin")
        pc = ProductClass.objects.get(name='testpc')
        self.assertEqual(pc.pk, 3)
        self.assertEqual(pc.attributes.count(), 0)

        url = reverse('admin-product-class-detail', args=(3,))
        data = {
            "attributes": [
                {
                    "product_class": "testpc",
                    "name": "testattr",
                    "code": "testattr",
                    "type": "text",
                },
            ],
        }
        self.response = self.patch(url, **data)
        self.response.assertStatusEqual(200)
        self.assertEqual(len(self.response['attributes']), 1)
