import decimal

from django.urls import reverse

from api.serializers.admin.product import AdminStockRecordsSerializer, AdminProductSerializer
from api.serializers.product import ProductAttributeValueSerializer
from api.tests.utils import APITest
from product.models import Product


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

    def test_product_detail(self):
        self.response = self.client.get(reverse('product-detail', args=(2,)))
        self.response.assertStatusEqual(200)
        self.response.assertValueEqual('title', 'testproduct1')

    def test_product_list_filter(self):
        standalone_products_url = "%s?structure=standalone" % reverse("product-list")
        self.response = self.get(standalone_products_url)
        self.response.assertStatusEqual(200)
        self.assertEqual(len(self.response.body), 1)

        parent_products_url = "%s?structure=parent" % reverse("product-list")
        self.response = self.get(parent_products_url)
        self.response.assertStatusEqual(200)
        self.assertEqual(len(self.response.body), 1)

        child_products_url = "%s?structure=child" % reverse("product-list")
        self.response = self.get(child_products_url)
        self.response.assertStatusEqual(200)
        self.assertEqual(len(self.response.body), 1)

        koe_products_url = "%s?structure=koe" % reverse("product-list")
        self.response = self.get(koe_products_url)
        self.response.assertStatusEqual(200)
        self.assertEqual(len(self.response.body), 0)

    def test_product_detail(self):
        "Check product details"
        self.response = self.get(reverse("product-detail", args=(1,)))
        self.response.assertStatusEqual(200)
        default_fields = (
            "url",
            "id",
            "title",
            "structure",
            "description",
            "attributes",
            "category",
            "product_class",
            "children",
        )
        for field in default_fields:
            self.assertIn(field, self.response.body)

        self.response.assertValueEqual("title", "standalone_product")


class _ProductSerializerTest(APITest):
    def assertErrorStartsWith(self, ser, name, errorstring):
        self.assertTrue(
            ser.errors[name][0].startswith(errorstring),
            "Error '%s' does not start with '%s" % (ser.errors[name][0], errorstring),
        )


class AdminStockRecordSerializerTest(_ProductSerializerTest):
    def test_stockrecord_save(self):
        "The AdminStockRecordSerializer should be able to save stuff"
        ser = AdminStockRecordsSerializer(
            data={
                "product": 1,
                "partner_sku": "henk",
                "price": 20,
                "num_in_stock": 34,
                "owner": 2
            }
        )
        self.assertTrue(ser.is_valid(), "There where errors %s" % ser.errors)

        obj = ser.save()
        self.assertEqual(obj.product.get_title(), "standalone_product")
        self.assertEqual(obj.price, decimal.Decimal("20.00"))
        self.assertEqual(obj.num_in_stock, 34)


# class ProductAttributeValueSerializerTest(_ProductSerializerTest):
#     def test_productattributevalueserializer_error(self):
#         "If attributes do not exist on the product class a tidy error should explain"
#         product = Product.objects.get(pk=1)
#         ser = ProductAttributeValueSerializer(
#             data={"name": "zult", "code": "zult", "value": "hoolahoop", "product": product}
#         )
#
#         self.assertFalse(
#             ser.is_valid(),
#             "There should be an error because there is no attribute named zult",
#         )
#         self.assertEqual(
#             ser.errors["value"],
#             [
#                 "No attribute exist with code=zult, please define it in "
#                 "the product_class first."
#             ],
#         )
#         self.assertDictEqual(ser.errors, {"value": ["Attribute text is required."]})
#
#     def test_productattributevalueserializer_text_error(self):
#         product = Product.objects.get(pk=1)
#         ser = ProductAttributeValueSerializer(
#             data={"name": "Text", "code": "text", "value": 4, "product": product}
#         )
#         self.assertFalse(ser.is_valid(), "This should fail")
#
#         ser = ProductAttributeValueSerializer(
#             data={"name": "color", "code": "color", "value": None, "product": product}
#         )
#         self.assertFalse(ser.is_valid(), "This should fail")
#         self.assertDictEqual(ser.errors, {"value": ["Attribute text is required."]})


class AdminProductSerializerTest(_ProductSerializerTest):
    def test_create_product(self):
        "Products should be created by the serializer if needed"
        ser = AdminProductSerializer(
            data={"product_class": "t-shirts", "title": "test"}
        )
        self.assertTrue(ser.is_valid(), "Something wrong %s" % ser.errors)
        obj = ser.save()
        self.assertEqual(obj.pk, 4, "Should be new object, with a high pk")
        self.assertEqual(obj.product_class.slug, "t-shirts")
        self.assertEqual(obj.title, "test")

    # def test_modify_product(self):
    #     "We should a able to change product fields."
    #     product = Product.objects.get(pk=1)
    #
    #     ser = AdminProductSerializer(
    #         data={
    #             "product_class": "t-shirts",
    #             "slug": "lots-of-attributes",
    #             "description": "Henk",
    #         },
    #         instance=product,
    #     )
    #     self.assertTrue(ser.is_valid(), "Something wrong %s" % ser.errors)
    #     obj = ser.save()
    #     self.assertEqual(obj.pk, 3, "product should be the same as passed as instance")
    #     self.assertEqual(obj.title, "attrtypestest")
