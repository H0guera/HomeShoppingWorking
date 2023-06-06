from django.core.cache import cache
from django.db.models import Prefetch

from rest_framework import generics

from api.serializers.product import CategorySerializer, ProductStockRecordSerializer, ProductSerializer
from product.models import ProductCategory, StockRecord, Product, ProductAttributeValue


class ProductList(generics.ListAPIView):
    queryset = Product.objects.all().select_related('product_class').prefetch_related(
        'stockrecords',
        Prefetch('attribute_values', queryset=ProductAttributeValue.objects.select_related('attribute')),
        Prefetch('children', queryset=Product.objects.all().prefetch_related(
            Prefetch('attribute_values', queryset=ProductAttributeValue.objects.all().select_related('attribute')),
        )),
    )
    serializer_class = ProductSerializer

    def get_queryset(self):
        """
        Allow filtering on structure so standalone and parent products can
        be selected separately, eg::

            http://127.0.0.1:8000/api/products/?structure=standalone

        or::

            http://127.0.0.1:8000/api/products/?structure=parent
        """
        qs_cache_name = 'p_list_cache'
        qs_cache = cache.get(qs_cache_name)

        if qs_cache:
            qs = qs_cache
        else:
            qs = super(ProductList, self).get_queryset()
        structure = self.request.query_params.get("structure")
        if structure is not None:
            return qs.filter(structure=structure)

        return qs


class ProductDetail(generics.RetrieveAPIView):
    queryset = Product.objects.all().select_related('product_class').prefetch_related(
        Prefetch('attribute_values', queryset=ProductAttributeValue.objects.all().select_related('attribute')),
        Prefetch('children', queryset=Product.objects.all().prefetch_related(
            Prefetch('attribute_values', queryset=ProductAttributeValue.objects.all().select_related('attribute')),
        ),
                 ),
    )
    serializer_class = ProductSerializer


class ProductStockRecords(generics.ListAPIView):
    serializer_class = ProductStockRecordSerializer
    queryset = StockRecord.objects.all()

    def get_queryset(self):
        product_pk = self.kwargs.get("pk")
        return super().get_queryset().filter(product_id=product_pk)


class ProductStockRecordDetail(generics.RetrieveAPIView):
    serializer_class = ProductStockRecordSerializer
    queryset = StockRecord.objects.all()


class ProductStockRecordsDetail(generics.RetrieveAPIView):
    serializer_class = ProductStockRecordSerializer
    queryset = StockRecord.objects.all()


class CategoryList(generics.ListAPIView):
    queryset = ProductCategory.objects.all()
    serializer_class = CategorySerializer


class CategoryDetail(generics.ListAPIView):
    queryset = ProductCategory.objects.all()
    serializer_class = CategorySerializer
