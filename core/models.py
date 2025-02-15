from django.db import models
from core.enums import *
from django.db import DatabaseError, transaction

class Market(models.Model):
    symbol = models.CharField(max_length=120, unique=True)

    def get_best_maker_price_or_none(self, order_side):
        if order_side == OrderSide.SELL.value:
            return Order.objects.filter(market=self, order_side=order_side, order_status=OrderStatus.WAITING.value).aggregate(models.Min('price'))['price__min']
        return Order.objects.filter(market=self, order_side=order_side, order_status=OrderStatus.WAITING.value).aggregate(models.Max('price'))['price__max']

    def get_remaining_makers_amount(self, order_side):
        ret = Order.objects.filter(market=self, order_side=order_side, order_status=OrderStatus.WAITING.value).aggregate(models.Sum('remaining_amount'))['remaining_amount__sum']
        return ret if ret is not None else 0

    def get_best_maker_obj_or_none(self, order_side):
        if order_side == OrderSide.SELL.value:
            return Order.objects.filter(market=self, order_side=OrderSide.SELL.value, remaining_amount__gt=0,
                                        order_status=OrderStatus.WAITING.value).order_by('price').first()
        return Order.objects.filter(market=self, order_side=order_side, order_status=OrderStatus.WAITING.value).order_by('-price').first()

    def get_order_book(self, order_side):
        if order_side == OrderSide.SELL:
            return Order.objects.filter(market=self, order_side = order_side, order_type=OrderType.LIMIT, order_status=OrderStatus.WAITING.value).order_by('price')
        else:
            return Order.objects.filter(market=self, order_side=order_side, order_type=OrderType.LIMIT,
                                        order_status=OrderStatus.WAITING.value).order_by('-price')

class Order(models.Model):
    order_type = models.CharField(choices=OrderType, max_length=10)
    order_side = models.CharField(choices=OrderSide, max_length=10)
    order_status = models.CharField(choices=OrderStatus, max_length=10)
    market = models.ForeignKey(Market, on_delete=models.CASCADE)
    primary_amount = models.DecimalField(decimal_places=8, max_digits=20)
    remaining_amount = models.DecimalField(decimal_places=8, max_digits=20, default=0)
    price = models.DecimalField(decimal_places=8, max_digits=20, null=True, blank=True)

    class Meta:
        indexes = [
            models.Index(fields=['market', 'order_side', 'order_status']),
            models.Index(fields=['price']),
        ]

    def is_maker(self):
        if self.order_type == OrderType.MARKET.value:
            return False
        other_side = OrderSide.BUY.value if self.order_side == OrderSide.SELL.value else OrderSide.SELL.value
        best_other_side_maker = self.market.get_best_maker_obj_or_none(other_side)
        return not self.can_trade(best_other_side_maker)

    def can_trade(self, other_order):
        if other_order is None:
            return False
        if self.order_side == other_order.order_side:
            return False
        if self.order_type == OrderType.MARKET.value and other_order.order_type == OrderType.MARKET.value:
            return False
        if self.order_type == OrderType.MARKET.value or other_order.order_type == OrderType.MARKET.value:
            return True
        if self.order_side == OrderSide.SELL.value:
            return self.price <= other_order.price
        return self.price >= other_order.price

    @transaction.atomic
    def fill_atomic(self):
        other_side = OrderSide.BUY.value if self.order_side == OrderSide.SELL.value else OrderSide.SELL.value
        while self.remaining_amount > 0:
            best_other_side_maker = self.market.get_best_maker_obj_or_none(other_side)
            if not self.can_trade(best_other_side_maker):
                break
            if self.remaining_amount >= best_other_side_maker.remaining_amount:
                    amount = best_other_side_maker.remaining_amount
                    self.remaining_amount -= amount
                    self.save(update_fields=['remaining_amount'])
                    best_other_side_maker.remaining_amount = 0
                    best_other_side_maker.order_status = OrderStatus.FILLED.value
            else:
                    amount = self.remaining_amount
                    best_other_side_maker.remaining_amount -= amount
                    self.remaining_amount = 0
                    self.order_status = OrderStatus.FILLED.value
                    best_other_side_maker.save(update_fields=['remaining_amount', 'order_status'])
            best_other_side_maker.save()
            Trade.objects.create(maker=best_other_side_maker, taker=self, amount=amount,
                                 price=best_other_side_maker.price)

    def fill(self):
        other_side = OrderSide.BUY.value if self.order_side == OrderSide.SELL.value else OrderSide.SELL.value
        while self.remaining_amount > 0:
            best_other_side_maker = self.market.get_best_maker_obj_or_none(other_side)
            if not self.can_trade(best_other_side_maker):
                break
            if self.remaining_amount >= best_other_side_maker.remaining_amount:
                with transaction.atomic():
                    amount = best_other_side_maker.remaining_amount
                    self.remaining_amount -= best_other_side_maker.remaining_amount
                    self.save(update_fields=['remaining_amount'])
                    best_other_side_maker.remaining_amount = 0
                    best_other_side_maker.order_status = OrderStatus.FILLED.value
                    best_other_side_maker.save()
                    Trade.objects.create(maker=best_other_side_maker, taker=self, amount=amount,
                                         price=best_other_side_maker.price)
            else:
                with transaction.atomic():
                    amount = self.remaining_amount
                    best_other_side_maker.remaining_amount -= self.remaining_amount
                    self.remaining_amount = 0
                    self.order_status = OrderStatus.FILLED.value
                    best_other_side_maker.save(update_fields=['remaining_amount', 'order_status'])
                    Trade.objects.create(maker=best_other_side_maker, taker=self, amount=amount,
                                         price=best_other_side_maker.price)


    def save_based_remaining(self):
        if self.remaining_amount == 0:
            self.order_status = OrderStatus.FILLED.value
        else:
            self.order_status = OrderStatus.WAITING.value
        self.save(update_fields=['remaining_amount', 'order_status'])


class Trade(models.Model):
    maker = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='maker')
    taker = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='taker')
    amount = models.DecimalField(decimal_places=8, max_digits=20)
    price = models.DecimalField(decimal_places=8, max_digits=20)


