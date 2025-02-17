import threading

import requests
import time
import matplotlib.pyplot as plt
from concurrent.futures import ThreadPoolExecutor, as_completed


# Configuration
url = 'http://127.0.0.1:8000/core/order/'

def make_orders_1(market_id):
    orders = []
    for _ in range(40):
        orders.append({
            'order_type': 'LIMIT',
            'order_side': 'BUY',
            'market': market_id,
            'primary_amount': 1,
            'price': 100 + _
        })
    for _ in range(20):
        orders.append({
            'order_type': 'MARKET',
            'order_side': 'SELL',
            'market': 1,
            'primary_amount': market_id,
            'price': 150
        })
    for _ in range(40):
        orders.append({
            'order_type': 'LIMIT',
            'order_side': 'SELL',
            'market': market_id,
            'primary_amount': market_id,
            'price': 140 - _
        })
    return orders

def make_orders_2(market_id):
    orders = []
    for _ in range(100):
        orders.append({
            'order_type': 'LIMIT',
            'order_side': 'BUY',
            'market': market_id,
            'primary_amount': 1,
            'price': 100 + _
        })
    return orders

def test(orders):
    return measure_latency_multi_thread(orders)

def measure_latency_multi_thread(orders):
    start_time = time.time()
    with ThreadPoolExecutor() as executor:
        futures = {executor.submit(send_request, order): order for order in orders}
        for future in as_completed(futures):
            response = future.result()
    end_time = time.time()
    total_time = end_time - start_time
    return total_time

def measure_latency(orders):
    latencies = []
    start_time = time.time()
    for _ in range(len(orders)):
        response = requests.post(url, data=orders[_])
    finish_time = time.time()
    total_time = finish_time - start_time
    return total_time

def send_request(order):
    response = requests.post(url, data=order)
    return response

def run_test(market_id):
    orders = make_orders_2(market_id)
    print(f'whole response time for marketـ{market_id} = {test(orders)}')

def main():
    threads = []
    for i in range(1,11):
        threads.append(threading.Thread(target=run_test, args=(i,)))
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()

if __name__ == '__main__':
    main()
