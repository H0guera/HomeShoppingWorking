from django.contrib import admin

from order.models import ShippingAddress, Order, OrderLine, OrderLineAttribute

admin.site.register(ShippingAddress)
admin.site.register(Order)
admin.site.register(OrderLine)
admin.site.register(OrderLineAttribute)
