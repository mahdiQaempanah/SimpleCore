from django.urls import path, include
from django.contrib import admin
from core.models import *
from core.views import MarketView, OrderView, TradeView, OrderBookView
from django.views.decorators.csrf import csrf_exempt
urlpatterns = [
    #    path('admin/', admin.site.urls),
    path('market/', csrf_exempt(MarketView.as_view())),
    path('order_book/', csrf_exempt(OrderBookView.as_view())),
    path('order/', csrf_exempt(OrderView.as_view())),
    path('trade/', csrf_exempt(TradeView.as_view())),
]



