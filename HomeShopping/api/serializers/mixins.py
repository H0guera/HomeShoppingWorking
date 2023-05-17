from django.db import transaction

from order.models import Order, OrderLine, OrderLineAttribute


class OrderPlacementMixin:

    def generate_order_number(self, basket):
        return 100000 + basket.id

    def place_order(self, basket, order_number, order_total,
                    user=None, shipping_address=None, **kwargs):

        if basket.num_items() <= 0:
            raise ValueError("Empty baskets cannot be submitted")

        if not order_number:
            order_number = self.generate_order_number(basket)

        if Order.objects.filter(number=order_number).exists():
            raise ValueError("There is already an order with number %s"
                             % order_number)
        if 'request' not in kwargs:
            request = getattr(self, 'request', None)
        else:
            request = kwargs.pop('request')

        with transaction.atomic():
            shipping_address = self.create_shipping_address(shipping_address)
            order = self.create_order_model(basket, order_total, order_number,
                                            user, shipping_address, **kwargs)

            for basket_line in basket.lines.all():
                self.create_line_models(order, basket_line)
                self.update_stock_records(basket_line)

        return order

    def create_shipping_address(self, shipping_address):
        if not shipping_address:
            return None
        shipping_address.save()
        return shipping_address

    def create_order_model(self, basket, order_total, order_number,
                           user, shipping_address, **extra_order_fields):
        order_data = {'basket': basket,
                      'total': order_total,
                      'number': order_number,
                      }
        if user and user.is_authenticated:
            order_data['user_id'] = user.id

        if shipping_address:
            order_data['shipping_address'] = shipping_address

        if extra_order_fields:
            order_data.update(extra_order_fields)

        order = Order(**order_data)
        order.save()
        return order

    def create_line_models(self, order, basket_line):
        line_data = {'order': order,
                     'product': basket_line.product,
                     'quantity': basket_line.quantity,
                     'stockrecord': basket_line.product.stockrecords.get(product=basket_line.product)}
        order_line = OrderLine(**line_data)
        order_line.save()
        self.create_line_attrs(order_line, basket_line)

    def create_line_attrs(self, order_line, basket_line):
        for attr in basket_line.product.attributes.all():
            OrderLineAttribute.objects.create(line=order_line, type=attr.name,
                                              value=attr.productattributevalue_set.get(id=attr.id))

    def update_stock_records(self, basket_line):
        stockrecord = basket_line.product.stockrecords.get(product=basket_line.product)
        stockrecord.num_in_stock -= basket_line.quantity
        stockrecord.save()
