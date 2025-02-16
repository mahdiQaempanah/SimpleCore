import decimal
import profile

from django.db import IntegrityError
from django.shortcuts import render
from rest_framework import generics

from .enums import OrderStatus, OrderType, OrderSide
from .models import Market, Order, Trade
from django.views import View
from django.http import HttpResponse, HttpRequest, JsonResponse
from django.db import DatabaseError, transaction
from .tasks import *
from .utils import ExecutionEvaluator


class MarketView(View):
    def get(self, request: HttpRequest):
        if 'pk' in request.GET:
            try:
                market = Market.objects.get(pk=request.GET['pk'])
                return HttpResponse(f'Market {market.symbol}')
            except Market.DoesNotExist:
                return JsonResponse({'message': 'Market not found'}, status=404)
        markets = Market.objects.all()
        return JsonResponse({'markets': [market.symbol for market in markets]})

    def post(self, request: HttpRequest):
        try:
            market = Market.objects.create(symbol=request.POST['symbol'])
            return JsonResponse({'message': f'Market {market.symbol} created'})
        except IntegrityError:
            return JsonResponse({'message': 'Market already exists'}, status=400)
        except KeyError:
            return JsonResponse({'message': 'Missing required fields'}, status=400)


class OrderBookView(View):
    def get(self, request: HttpRequest):
        try:
            market = Market.objects.get(symbol=request.GET['symbol'])
            order_side = request.GET['order_side']
            makers = market.get_order_book(order_side, True)
            return JsonResponse({'orders': [{'id':order.pk, 'price':order.price, 'remaining amount':order.remaining_amount} for order in makers]})
        except KeyError:
            return JsonResponse({'message': 'Missing required fields'}, status=400)


class OrderView(View):
    def get(self, request: HttpRequest):
        if 'pk' in request.GET:
            try:
                order = Order.objects.get(pk=request.GET['pk'])
                return JsonResponse({'message': f'Order {order.pk}: {order.order_type} {order.order_side} {order.market.symbol} {order.primary_amount} {order.price}'})
            except Order.DoesNotExist:
                return HttpResponse('Order not found', status=404)
        orders = Order.objects.all()
        return JsonResponse({'orders': [f'{order.pk}: {order.order_type} {order.order_side} {order.market.symbol} {order.primary_amount} {order.price}' for order in orders]})

    def post(self, request: HttpRequest):
        try:
            order_dict = OrderView.make_order_dict(request)
            if order_dict is None:
                return JsonResponse({'message': 'Invalid value'}, status=400)
            result = handle_new_order.apply_async(args=[order_dict], queue=f"market_{order_dict['market']}")
            response = result.get(timeout=5)
            return JsonResponse({'message': response[0]}, status=response[1])
        except IntegrityError:
            return JsonResponse({'message': 'Order already exists'}, status=400)
        except KeyError:
            return JsonResponse({'message': 'Missing required fields'}, status=400)
        except ValueError:
            return JsonResponse({'message': 'Invalid value'}, status=400)

    @staticmethod
    def make_order_dict(request: HttpRequest):
        try:
            order_dict = {
                'order_type': request.POST['order_type'],
                'order_side': request.POST['order_side'],
                'market': int(request.POST['market']),
                'remaining_amount': request.POST['primary_amount'],
                'primary_amount': request.POST['primary_amount'],
                'price': request.POST.get('price', None),
                'order_status': OrderStatus.INITIATED.value
            }
            if order_dict['order_type'] == OrderType.LIMIT.value and order_dict['price'] is None:
                return None
            return order_dict
        except KeyError:
            return None
        except ValueError:
            return None
        except TypeError:
            return None


class TradeView(View):
    def get(self, request):
        trades = Trade.objects.all()
        return JsonResponse({'trades': [{'pk':trade.pk, 'maker pk':trade.maker.pk, 'taker pk':trade.taker.pk,  'amount':trade.amount, 'price':trade.price} for trade in trades]})

    def post(self, request):
        trade_dict = self.make_trade_dict(request)
        try:
            trade = Trade.objects.create(**trade_dict)
            return JsonResponse({'message': f'Trade {trade.pk} created'})
        except IntegrityError:
            return JsonResponse({'message': 'Trade already exists'}, status=400)
        except KeyError:
            return JsonResponse({'message': 'Missing required fields'}, status=400)
        except ValueError:
            return JsonResponse({'message': 'Invalid value'}, status=400)

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