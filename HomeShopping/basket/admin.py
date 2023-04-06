from django.contrib import admin

# Register your models here.
from basket.models import Basket, BasketLine

admin.site.register(Basket)
admin.site.register(BasketLine)
