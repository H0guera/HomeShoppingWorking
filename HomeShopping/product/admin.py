from django.contrib import admin

from product.models import Product, ProductClass, ProductCategory, ProductAttribute, ProductAttributeValue, StockRecord

admin.site.register(Product)
admin.site.register(ProductClass)
admin.site.register(ProductCategory)
admin.site.register(ProductAttribute)
admin.site.register(ProductAttributeValue)
admin.site.register(StockRecord)
