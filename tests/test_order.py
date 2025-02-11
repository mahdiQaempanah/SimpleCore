from django.http import QueryDict, HttpRequest
from django.test import TestCase
from core.models import Order, Market, Trade
from core.views import OrderView, MarketView, TradeView
from core.enums import OrderType, OrderSide, OrderStatus



class OrderViewTestCase(TestCase):
    def test_first_limit(self):
        market = Market.objects.create(symbol='BTCUSD')
        request = HttpRequest()
        request.POST = QueryDict(f'order_type=LIMIT&order_side=BUY&market={market.pk}&primary_amount=1&price=100')
        response = OrderView().post(request)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(Order.objects.count(), 1)
        order = Order.objects.first()
        self.assertEqual(order.order_type, OrderType.LIMIT.value)
        self.assertEqual(order.order_side, OrderSide.BUY.value)
        self.assertEqual(order.market, market)
        self.assertEqual(order.primary_amount, 1)
        self.assertEqual(order.price, 100)
        self.assertEqual(order.order_status, OrderStatus.WAITING.value)

    def test_first_market(self):
        market = Market.objects.create(symbol='BTCUSD')
        request = HttpRequest()
        request.POST = QueryDict(f'order_type=MARKET&order_side=SELL&market={market.pk}&primary_amount=1')
        response = OrderView().post(request)
        self.assertEqual(response.status_code, 400)
        self.assertEqual(Order.objects.count(), 1)
        order = Order.objects.first()
        self.assertEqual(order.order_type, OrderType.MARKET.value)
        self.assertEqual(order.order_side, OrderSide.SELL.value)
        self.assertEqual(order.market, market)
        self.assertEqual(order.primary_amount, 1)
        self.assertEqual(order.order_status, OrderStatus.CANCELED.value)

    def test_limit_miss_price(self):
        market = Market.objects.create(symbol='BTCUSD')
        request = HttpRequest()
        request.POST = QueryDict(f'order_type=LIMIT&order_side=BUY&market={market.pk}&primary_amount=1')
        response = OrderView().post(request)
        self.assertEqual(response.status_code, 400)
        self.assertEqual(Order.objects.count(), 0)

    def test_different_limit_side(self):
        market = Market.objects.create(symbol='BTCUSD')
        request_sell = HttpRequest()
        request_sell.POST = QueryDict(f'order_type=LIMIT&order_side=SELL&market={market.pk}&primary_amount=1&price=100')
        response_sell = OrderView().post(request_sell)
        self.assertEqual(response_sell.status_code, 200)
        self.assertEqual(Order.objects.count(), 1)

        request_buy = HttpRequest()
        request_buy.POST = QueryDict(f'order_type=LIMIT&order_side=BUY&market={market.pk}&primary_amount=1&price=90')
        response_buy = OrderView().post(request_buy)
        self.assertEqual(response_buy.status_code, 200)
        self.assertEqual(Order.objects.count(), 2)

    def test_trade_limit_limit(self):
        market = Market.objects.create(symbol='BTCUSD')
        request_sell = HttpRequest()
        request_sell.POST = QueryDict(f'order_type=LIMIT&order_side=SELL&market={market.pk}&primary_amount=1&price=100')
        response_sell = OrderView().post(request_sell)
        self.assertEqual(response_sell.status_code, 200)
        self.assertEqual(Order.objects.count(), 1)

        request_buy = HttpRequest()
        request_buy.POST = QueryDict(f'order_type=LIMIT&order_side=BUY&market={market.pk}&primary_amount=1&price=110')
        response_buy = OrderView().post(request_buy)
        self.assertEqual(response_buy.status_code, 200)
        self.assertEqual(Order.objects.count(), 2)

        order_sell = Order.objects.get(order_side=OrderSide.SELL.value)
        order_buy = Order.objects.get(order_side=OrderSide.BUY.value)
        self.assertEqual(order_sell.order_status, OrderStatus.FILLED.value)
        self.assertEqual(order_buy.order_status, OrderStatus.FILLED.value)
        self.assertEqual(order_sell.remaining_amount, 0)
        self.assertEqual(order_buy.remaining_amount, 0)
        self.assertEqual(Trade.objects.count(), 1)
        trade = Trade.objects.first()
        self.assertEqual(trade.maker, order_sell)
        self.assertEqual(trade.taker, order_buy)
        self.assertEqual(trade.amount, 1)
        self.assertEqual(trade.price, 100)

    def test_trade_market_limit(self):
        market = Market.objects.create(symbol='BTCUSD')
        request_sell = HttpRequest()
        request_sell.POST = QueryDict(f'order_type=LIMIT&order_side=SELL&market={market.pk}&primary_amount=1&price=100')
        response_sell = OrderView().post(request_sell)
        self.assertEqual(response_sell.status_code, 200)
        self.assertEqual(Order.objects.count(), 1)

        request_buy = HttpRequest()
        request_buy.POST = QueryDict(f'order_type=MARKET&order_side=BUY&market={market.pk}&primary_amount=1&price=110')
        response_buy = OrderView().post(request_buy)
        self.assertEqual(response_buy.status_code, 200)
        self.assertEqual(Order.objects.count(), 2)

        order_sell = Order.objects.get(order_side=OrderSide.SELL.value)
        order_buy = Order.objects.get(order_side=OrderSide.BUY.value)
        self.assertEqual(order_sell.order_status, OrderStatus.FILLED.value)
        self.assertEqual(order_buy.order_status, OrderStatus.FILLED.value)
        self.assertEqual(order_sell.remaining_amount, 0)
        self.assertEqual(order_buy.remaining_amount, 0)
        self.assertEqual(Trade.objects.count(), 1)
        trade = Trade.objects.first()
        self.assertEqual(trade.maker, order_sell)
        self.assertEqual(trade.taker, order_buy)
        self.assertEqual(trade.amount, 1)
        self.assertEqual(trade.price, 100)

    def test_market_enough_amount(self):
        market = Market.objects.create(symbol='BTCUSD')
        request_sell = HttpRequest()
        request_sell.POST = QueryDict(f'order_type=LIMIT&order_side=SELL&market={market.pk}&primary_amount=1&price=100')
        _ = OrderView().post(request_sell)
        _ = OrderView().post(request_sell)
        self.assertEqual(Order.objects.count(), 2)


        request_buy = HttpRequest()
        request_buy.POST = QueryDict(f'order_type=MARKET&order_side=BUY&market={market.pk}&primary_amount=1.5')
        response_buy = OrderView().post(request_buy)
        self.assertEqual(response_buy.status_code, 200)

    def test_market_not_enough_amount(self):
        market = Market.objects.create(symbol='BTCUSD')
        request_sell = HttpRequest()
        request_sell.POST = QueryDict(f'order_type=LIMIT&order_side=SELL&market={market.pk}&primary_amount=1&price=100')
        _ = OrderView().post(request_sell)
        _ = OrderView().post(request_sell)
        self.assertEqual(Order.objects.count(), 2)

        request_buy = HttpRequest()
        request_buy.POST = QueryDict(f'order_type=MARKET&order_side=BUY&market={market.pk}&primary_amount=2.5')
        response_buy = OrderView().post(request_buy)
        self.assertEqual(response_buy.status_code, 400)


