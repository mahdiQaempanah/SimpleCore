from enum import Enum
from django.db import models

class OrderType(models.TextChoices):
    LIMIT = 'LIMIT'
    MARKET = 'MARKET'

class OrderSide(models.TextChoices):
    BUY = 'BUY'
    SELL = 'SELL'

class OrderStatus(models.TextChoices):
    WAITING = 'WAITING'
    INITIATED = 'INITIATED'
    FILLED = 'FILLED'
    PARTIALLY_FILLED = 'PARTIALLY_FILLED'
    CANCELED = 'CANCELED'

