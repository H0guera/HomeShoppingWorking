from celery import shared_task

from django.core.cache import cache
from django.db.models import Prefetch

from product.models import Product, ProductAttributeValue


@shared_task
def bar():
    qs = Product.objects.all().select_related('product_class').prefetch_related(
        'stockrecords',
        Prefetch('attribute_values', queryset=ProductAttributeValue.objects.select_related('attribute')),
        Prefetch('children', queryset=Product.objects.all().prefetch_related(
            Prefetch('attribute_values', queryset=ProductAttributeValue.objects.all().select_related('attribute')),
        )),
    )
    product_list_cache_name = 'p_list_cache'
    cache.set(product_list_cache_name, qs, 130)
