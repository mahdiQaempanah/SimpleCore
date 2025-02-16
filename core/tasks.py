import copy
import decimal
from celery import shared_task
from django.db import IntegrityError, transaction
from django.http import HttpRequest, HttpResponse


from core.enums import OrderSide, OrderStatus, OrderType
from core.models import Order, Market
from core.utils import ExecutionEvaluator


def make_orm_valid_order_dict(order_dict):
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
    timer_creat_order = ExecutionEvaluator.timer("creat order")
    timer_fill = ExecutionEvaluator.timer("fill")
    timer_save_based = ExecutionEvaluator.timer("based")

    valid_order_dict = make_orm_valid_order_dict(order_dict)
    timer_creat_order.start()
    order_obj = Order.objects.create(**valid_order_dict)
    timer_creat_order.finish()

    timer_fill.start()
    order_obj.fill()
    timer_fill.finish()

    timer_save_based.start()
    order_obj.save_based_remaining()
    timer_save_based.finish()

    if order_obj.remaining_amount > 0:
        if order_obj.remaining_amount == order_obj.primary_amount:
            return f'Order {order_obj.id} does not filled',200
        else:
            return f'Order {order_obj.id} partially filled', 200
    else:
        return f'Order {order_obj.id} filled completely', 200


