import decimal
from celery import shared_task
from django.db import IntegrityError
from django.http import HttpRequest, HttpResponse

from core.enums import OrderSide, OrderStatus, OrderType
from core.models import Order, Market


@shared_task
def handle_new_order(order_dict):
    market = Market.objects.get(pk=order_dict['market'])
    order_dict['market'] = market
    order_dict['remaining_amount'] = decimal.Decimal(order_dict['remaining_amount'])
    order_dict['primary_amount'] = decimal.Decimal(order_dict['primary_amount'])
    if order_dict.get('price'):
        order_dict['price'] = decimal.Decimal(order_dict['price'])
    obj = Order.objects.create(**order_dict)
    if obj.is_maker():
        obj.order_status = OrderStatus.WAITING.value
        obj.save(update_fields=['order_status'])
        return f'Order {obj.id} created and is waiting to be filled', 200
    else:
        other_side = OrderSide.BUY.value if obj.order_side == OrderSide.SELL.value else OrderSide.SELL.value
        if obj.order_type == OrderType.MARKET.value:
            if obj.market.get_remaining_makers_amount(other_side) < obj.primary_amount:
                obj.order_status = OrderStatus.CANCELED.value
                obj.save(update_fields=['order_status'])
                return 'Not enough amount', 400
        obj.fill()
        obj.save_based_remaining()
        if obj.remaining_amount > 0:
            return f'Order {obj.id} partially filled',200
        else:
            return f'Order {obj.id} filled', 200


