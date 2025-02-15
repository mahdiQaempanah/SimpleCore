import copy
import decimal
from celery import shared_task
from django.db import IntegrityError
from django.http import HttpRequest, HttpResponse


from core.enums import OrderSide, OrderStatus, OrderType
from core.models import Order, Market


def make_valid_order_dict(order_dict):
    valid_order_dict = copy.deepcopy(order_dict)
    market = Market.objects.get(pk=order_dict['market'])
    valid_order_dict['market'] = market
    valid_order_dict['remaining_amount'] = decimal.Decimal(order_dict['remaining_amount'])
    valid_order_dict['primary_amount'] = decimal.Decimal(order_dict['primary_amount'])
    if order_dict.get('price'):
        valid_order_dict['price'] = decimal.Decimal(order_dict['price'])
    return valid_order_dict

@shared_task
def handle_new_order(order_dict):
    valid_order_dict = make_valid_order_dict(order_dict)
    order_obj = Order.objects.create(**valid_order_dict)
    if order_obj.is_maker():
        order_obj.order_status = OrderStatus.WAITING.value
        order_obj.save(update_fields=['order_status'])
        return f'Order {order_obj.id} created and is waiting to be filled', 200
    else:
        other_side = OrderSide.BUY.value if order_obj.order_side == OrderSide.SELL.value else OrderSide.SELL.value
        if order_obj.order_type == OrderType.MARKET.value:
            if order_obj.market.get_remaining_makers_amount(other_side) < order_obj.primary_amount:
                order_obj.order_status = OrderStatus.CANCELED.value
                order_obj.save(update_fields=['order_status'])
                return 'Not enough amount', 200
        if order_obj.order_type == OrderType.MARKET.value:
            order_obj.fill_atomic()
        else:
            order_obj.fill()
        order_obj.save_based_remaining()
        if order_obj.remaining_amount > 0:
            return f'Order {order_obj.id} partially filled',200
        else:
            return f'Order {order_obj.id} filled', 200


