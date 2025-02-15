from locust import HttpUser, TaskSet, task, between
import random

class OrderTaskSet(TaskSet):

    def on_start(self):
        self.orders = self.make_orders()

    def make_orders(self):
        orders = [{
            'order_type': 'LIMIT',
            'order_side': 'BUY',
            'market': 1,
            'primary_amount': 1,
            'price': 100
        }, {
            'order_type': 'LIMIT',
            'order_side': 'SELL',
            'market': 1,
            'primary_amount': 1,
            'price': 100
        }, {
            'order_type': 'LIMIT',
            'order_side': 'BUY',
            'market': 1,
            'primary_amount': 1,
            'price': 50
        }, {
            'order_type': 'LIMIT',
            'order_side': 'SELL',
            'market': 1,
            'primary_amount': 1,
            'price': 150
        }, {
            'order_type': 'MARKET',
            'order_side': 'SELL',
            'market': 1,
            'primary_amount': 500,
        }, {
            'order_type': 'MARKET',
            'order_side': 'BUY',
            'market': 1,
            'primary_amount': 500,
        }]

        return orders

    @task
    def place_order(self):
        order = random.choice(self.orders)
        self.client.post('/core/order/', data=order)

class OrderLoadTest(HttpUser):
    tasks = [OrderTaskSet]
    wait_time = between(1,1)
