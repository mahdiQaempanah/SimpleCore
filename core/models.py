from django.db import models
from fontTools.misc.cython import returns

from core.enums import *
from django.db import DatabaseError, transaction
from django.db.models import Q
import time

class Market(models.Model):
    symbol = models.CharField(max_length=120, unique=True)

    def get_order_book(self, order_side, sort_base_on_side = False):
        order_book = Order.objects.filter(
                        market=self,
                        order_side=order_side,
                        order_type=OrderType.LIMIT,
                        order_status__in=[OrderStatus.WAITING.value, OrderStatus.PARTIALLY_FILLED.value]
                    )
        if not sort_base_on_side:
            return order_book
        if order_side == OrderSide.SELL:
            return order_book.order_by('price')
        else:
            return order_book.order_by('-price')

    def get_sorted_candidates_for_trade(self, order_side, price=None):
        other_side = OrderSide.BUY.value if order_side == OrderSide.SELL.value else OrderSide.SELL.value

        filters = {
            "market": self,
            "order_side": other_side,
            "order_type": OrderType.LIMIT,
            "order_status__in": [OrderStatus.WAITING.value, OrderStatus.PARTIALLY_FILLED.value]
        }

        if price is not None:
            filters["price__gte" if order_side == OrderSide.SELL.value else "price__lte"] = price

        order_by = '-price' if order_side == OrderSide.SELL.value else 'price'

        return Order.objects.filter(**filters).order_by(order_by)


class Order(models.Model):
    order_type = models.CharField(choices=OrderType, max_length=20)
    order_side = models.CharField(choices=OrderSide, max_length=20)
    order_status = models.CharField(choices=OrderStatus, max_length=20)
    market = models.ForeignKey(Market, on_delete=models.CASCADE)
    primary_amount = models.DecimalField(decimal_places=8, max_digits=20)
    remaining_amount = models.DecimalField(decimal_places=8, max_digits=20, default=0)
    price = models.DecimalField(decimal_places=8, max_digits=20, null=True, blank=True)


    # class Meta:
    #     indexes = [
    #         models.Index(fields=['market', 'order_side', 'order_status', 'price']),
    #     ]

    def fill(self):
        candidates = self.market.get_sorted_candidates_for_trade(self.order_side, self.price if self.order_type == OrderType.LIMIT.value else None)

        for candidate in candidates:
            if self.remaining_amount == 0:
                break
            tradable_amount = min(self.remaining_amount, candidate.remaining_amount)
            self.remaining_amount -= tradable_amount
            candidate.remaining_amount -= tradable_amount
            with transaction.atomic():
                self.save()
                candidate.save_based_remaining()
                Trade.objects.create(maker=candidate, taker=self, amount=tradable_amount,
                                    price=candidate.price)
        self.save_based_remaining()

    def save_based_remaining(self):
        if self.remaining_amount == 0:
            self.order_status = OrderStatus.FILLED.value
        else:
            if self.order_type == OrderType.MARKET.value:
                self.order_status = OrderStatus.CANCELED.value
            elif self.remaining_amount == self.primary_amount:
                self.order_status = OrderStatus.WAITING.value
            else:
                self.order_status = OrderStatus.PARTIALLY_FILLED.value
        self.save()



class Trade(models.Model):
    maker = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='maker')
    taker = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='taker')
    amount = models.DecimalField(decimal_places=8, max_digits=20)
    price = models.DecimalField(decimal_places=8, max_digits=20)


