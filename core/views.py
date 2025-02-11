import decimal

from django.db import IntegrityError
from django.shortcuts import render
from rest_framework import generics

from .enums import OrderStatus, OrderType, OrderSide
from .models import Market, Order, Trade
from django.views import View
from django.http import HttpResponse, HttpRequest


class MarketView(View):
    def get(self, request: HttpRequest):
        if 'pk' in request.GET:
            try:
                market = Market.objects.get(pk=request.GET['pk'])
                return HttpResponse(f'Market {market.symbol}')
            except Market.DoesNotExist:
                return HttpResponse('Market not found', status=404)
        markets = Market.objects.all()
        return HttpResponse(', '.join([market.symbol for market in markets]))

    def post(self, request: HttpRequest):
        try:
            market = Market.objects.create(symbol=request.POST['symbol'])
            return HttpResponse(f'Market {market.symbol} created')
        except IntegrityError:
            return HttpResponse('Market already exists', status=400)
        except KeyError:
            return HttpResponse('Symbol not provided', status=400)

class OrderView(View):
    def get(self, request: HttpRequest):
        if 'pk' in request.GET:
            try:
                order = Order.objects.get(pk=request.GET['pk'])
                return HttpResponse(f'Order {order.id}')
            except Order.DoesNotExist:
                return HttpResponse('Order not found', status=404)
        orders = Order.objects.all()
        return HttpResponse(', '.join([order.pk for order in orders]))

    def post(self, request: HttpRequest):
        try:
            order_dict = self.make_order_dict(request)
            if order_dict is None:
                return HttpResponse('Invalid request', status=400)
            obj = Order.objects.create(**order_dict)
            if obj.is_maker():
                obj.order_status = OrderStatus.WAITING.value
                obj.save(update_fields=['order_status'])
                return HttpResponse(f'Order {obj.id} created and is waiting to be filled')
            else:
                other_side = OrderSide.BUY.value if obj.order_side == OrderSide.SELL.value else OrderSide.SELL.value
                if obj.order_type == OrderType.MARKET.value:
                    if obj.market.get_remaining_makers_amount(other_side) < obj.primary_amount:
                        obj.order_status = OrderStatus.CANCELED.value
                        obj.save(update_fields=['order_status'])
                        return HttpResponse('Not enough amount', status=400)
                obj.fill()
                obj.save_based_remaining()
                if obj.remaining_amount > 0:
                    return HttpResponse(f'Order {obj.id} partially filled')
                else:
                    return HttpResponse(f'Order {obj.id} filled')

        except IntegrityError:
            return HttpResponse('Order already exists', status=400)
        except KeyError:
            return HttpResponse('Missing required fields', status=400)
        except ValueError:
            return HttpResponse('Invalid value', status=400)

    def make_order_dict(self, request: HttpRequest):
        try:
            print(request.POST)
            market = Market.objects.get(pk=int(request.POST['market']))
            order_dict = {
                'order_type': request.POST['order_type'],
                'order_side': request.POST['order_side'],
                'market': market,
                'remaining_amount': decimal.Decimal(request.POST['primary_amount']),
                'primary_amount': decimal.Decimal(request.POST['primary_amount']),
                'price': request.POST.get('price', None),
                'order_status': OrderStatus.INITIATED.value
            }
            if order_dict['price'] is not None:
                order_dict['price'] = decimal.Decimal(order_dict['price'])
            if order_dict['order_type'] == OrderType.LIMIT.value and order_dict['price'] is None:
                return None
            return order_dict
        except Market.DoesNotExist:
            return None
        except KeyError:
            return None
        except ValueError:
            return None
        except TypeError:
            return None


class TradeView(View):
    def get(self, request, pk):
        try:
            trade = Trade.objects.get(pk=pk)
            return HttpResponse(f'Trade {trade.id}')
        except Trade.DoesNotExist:
            return HttpResponse('Trade not found', status=404)

    def get(self, request):
        trades = Trade.objects.all()
        return HttpResponse(', '.join([trade.pk for trade in trades]))

    def post(self, request):
        trade_dict = self.make_trade_dict(request)
        try:
            trade = Trade.objects.create(**trade_dict)
            return HttpResponse(f'Trade {trade.id} created')
        except IntegrityError:
            return HttpResponse('Trade already exists', status=400)
        except KeyError:
            return HttpResponse('Missing required fields', status=400)
        except ValueError:
            return HttpResponse('Invalid value', status=400)

    def make_trade_dict(self, request):
        try:
            maker = Order.objects.get(pk=request.POST['maker'])
            taker = Order.objects.get(pk=request.POST['taker'])
            trade_dict = {
                'maker': maker,
                'taker': taker,
                'amount': request.POST['amount']
            }
            return trade_dict
        except Order.DoesNotExist:
            return HttpResponse('Order not found', status=400)
        except KeyError:
            return HttpResponse('Missing required fields', status=400)
        except ValueError:
            return HttpResponse('Invalid value', status=400)
        except IntegrityError:
            return HttpResponse('Trade already exists', status=400)