from django.db import transaction, IntegrityError
from django.test import TestCase

from core.models import Market


class MarketTestCase(TestCase):
    def test_market_add(self):
        market = Market.objects.create(symbol='BTCUSD')
        self.assertEqual(market.symbol, 'BTCUSD')
        self.assertEqual(Market.objects.count(), 1)

    def test_symbol_exist(self): #unique constraint exist
        Market.objects.create(symbol='BTCUSD')
        try:
            with transaction.atomic():
                Market.objects.create(symbol='BTCUSD')
            self.fail('Should raise IntegrityError')
        except IntegrityError:
            pass
