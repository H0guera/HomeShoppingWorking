from rest_framework import generics
from rest_framework.permissions import IsAdminUser

from api.serializers.admin.product import AdminStockRecordsSerializer, AdminProductClassSerializer, \
    AdminProductSerializer, AdminCategorySerializer
from api.serializers.product import ProductAttributeSerializer
from product.models import ProductAttribute, ProductClass, StockRecord, Product, ProductCategory


class ProductAttributeAdminList(generics.ListCreateAPIView):
    serializer_class = ProductAttributeSerializer
    queryset = ProductAttribute.objects.get_queryset()
    permission_classes = (IsAdminUser,)

    def get_serializer(self, *args, **kwargs):
        if "data" in kwargs:
            data = kwargs["data"]

            if isinstance(data, list):
                kwargs["many"] = True

        return super(ProductAttributeAdminList, self).get_serializer(*args, **kwargs)


class ProductAttributeAdminDetail(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = ProductAttributeSerializer
    queryset = ProductAttribute.objects.get_queryset()
    permission_classes = (IsAdminUser,)


class ProductClassAdminList(generics.ListCreateAPIView):
    serializer_class = AdminProductClassSerializer
    queryset = ProductClass.objects.get_queryset()
    permission_classes = (IsAdminUser,)


class ProductClassAdminDetail(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = AdminProductClassSerializer
    queryset = ProductClass.objects.get_queryset()
    permission_classes = (IsAdminUser,)


class ProductStockRecordsAdminList(generics.ListCreateAPIView):
    serializer_class = AdminStockRecordsSerializer
    queryset = StockRecord.objects.get_queryset()
    permission_classes = (IsAdminUser,)


class ProductStockRecordsAdminDetail(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = AdminStockRecordsSerializer
    queryset = StockRecord.objects.all()
    permission_classes = (IsAdminUser,)


class ProductAdminList(generics.ListCreateAPIView):
    serializer_class = AdminProductSerializer
    queryset = Product.objects.get_queryset()
    permission_classes = (IsAdminUser,)


class ProductAdminDetail(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = AdminProductSerializer
    queryset = Product.objects.get_queryset()
    permission_classes = (IsAdminUser,)


class ProductCategoryList(generics.ListCreateAPIView):
    serializer_class = AdminCategorySerializer
    queryset = ProductCategory.objects.all()
    permission_classes = (IsAdminUser,)


class ProductCategoryDetail(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = AdminCategorySerializer
    queryset = ProductCategory.objects.all()
    permission_classes = (IsAdminUser,)
