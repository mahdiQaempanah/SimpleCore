import copy
import decimal
from celery import shared_task
from django.db import IntegrityError
from django.http import HttpRequest, HttpResponse
from django.db.backends.base import *

from core.enums import OrderSide, OrderStatus, OrderType
from core.models import Order, Market
import time

cnt, sm = 0, 0

def make_valid_order_dict(order_dict):
    valid_order_dict = copy.deepcopy(order_dict)
    market = Market.objects.get(pk=order_dict['market'])
    valid_order_dict['market'] = market
    valid_order_dict['remaining_amount'] = decimal.Decimal(order_dict['remaining_amount'])
    valid_order_dict['primary_amount'] = decimal.Decimal(order_dict['primary_amount'])
    if order_dict.get('price'):
        valid_order_dict['price'] = decimal.Decimal(order_dict['price'])
    return valid_order_dict

def handle_new_order(order_dict):
    valid_order_dict = make_valid_order_dict(order_dict)
    global cnt, sm
    obj = Order.objects.create(**valid_order_dict)
    start_time = time.time()
    is_maker = obj.is_maker()
    if is_maker:
        obj.order_status = OrderStatus.WAITING.value
        obj.save(update_fields=['order_status'])
        return f'Order {obj.id} created and is waiting to be filled', 200

    else:
        start_time = time.time()
        other_side = OrderSide.BUY.value if obj.order_side == OrderSide.SELL.value else OrderSide.SELL.value
        if obj.order_type == OrderType.MARKET.value:
            if obj.market.get_remaining_makers_amount(other_side) < obj.primary_amount:
                obj.order_status = OrderStatus.CANCELED.value
                obj.save(update_fields=['order_status'])
                return 'Not enough amount', 200
        cnt += 1
        sm += time.time() - start_time
        obj.fill()
        obj.save_based_remaining()
        if obj.remaining_amount > 0:
            return f'Order {obj.id} partially filled',200
        else:
            return f'Order {obj.id} filled', 200

def run_handler(n):
    global cnt, sm
    for i in range(n):
        handle_new_order({'market': 2, 'order_type': 'LIMIT', 'order_side': 'BUY', 'primary_amount': '1.5', 'remaining_amount': '1.5', 'price': '1000'})
    print(f"Average time: {sm}")

