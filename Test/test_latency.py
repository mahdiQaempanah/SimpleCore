import requests
import time
import matplotlib.pyplot as plt
from concurrent.futures import ThreadPoolExecutor, as_completed


# Configuration
url = 'http://127.0.0.1:8000/core/order/'
num_requests = 1000
num_trials = 1

def make_orders():
    orders = []
    for _ in range(400):
        orders.append({
            'order_type': 'LIMIT',
            'order_side': 'BUY',
            'market': 1,
            'primary_amount': 1,
            'price': 1000 + _
        })
    for _ in range(200):
        orders.append({
            'order_type': 'MARKET',
            'order_side': 'SELL',
            'market': 1,
            'primary_amount': 1,
            'price': 1500
        })
    for _ in range(400):
        orders.append({
            'order_type': 'LIMIT',
            'order_side': 'SELL',
            'market': 1,
            'primary_amount': 1,
            'price': 1400 - _
        })
    return orders

def test(number_of_trials, orders):
    latencies = []
    for _ in range(number_of_trials):
        latencies.append(measure_latency_multi_thread(orders))
    return latencies

def measure_latency_multi_thread(orders):
    start_time = time.time()
    # Use ThreadPoolExecutor to send requests concurrently
    with ThreadPoolExecutor() as executor:
        futures = {executor.submit(send_request, order): order for order in orders}
        # Collect responses (if needed) and wait for all threads to finish
        for future in as_completed(futures):
            response = future.result()  # You can process the response if needed
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

# def measure_latency(orders):
#     latencies = []
#     start_time = time.time()
#     for _ in range(len(orders)):
#         response = requests.post(url, data=orders[_])
#         latencies.append(time.time() - start_time)
#     return latencies

def show_results(latencies):
    print(latencies)
    # plt.plot(latencies)
    # plt.ylabel('Latency (s)')
    # plt.xlabel('whi')
    # plt.show()

def main():
    orders = make_orders()
    latencies = test(num_trials, orders)
    show_results(latencies)

if __name__ == '__main__':
    main()
