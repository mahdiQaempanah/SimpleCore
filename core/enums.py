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
    FILLED = 'FILLED'
    CANCELED = 'CANCELED'

