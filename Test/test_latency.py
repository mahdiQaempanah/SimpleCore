import requests
import time
import matplotlib.pyplot as plt

# Configuration
url = 'http://127.0.0.1:8000/core/order/'
num_requests = 1000
num_trials = 2

def make_orders():
    orders = []
    for _ in range(400):
        orders.append({
            'order_type': 'LIMIT',
            'order_side': 'BUY',
            'market': 2,
            'primary_amount': 1,
            'price': 1000 + _
        })
    for _ in range(200):
        orders.append({
            'order_type': 'MARKET',
            'order_side': 'SELL',
            'market': 2,
            'primary_amount': 1,
            'price': 1500
        })
    for _ in range(400):
        orders.append({
            'order_type': 'LIMIT',
            'order_side': 'SELL',
            'market': 2,
            'primary_amount': 1,
            'price': 1400 - _
        })
    return orders

def test(number_of_trials, orders):
    latencies = []
    for _ in range(number_of_trials):
        latencies.append(measure_latency(orders))
    return latencies

def measure_latency(orders):
    latencies = []
    start_time = time.time()
    for _ in range(len(orders)):
        response = requests.post(url, data=orders[_])
        latencies.append(time.time() - start_time)
    return latencies

def show_results(latencies):
    plt.plot(latencies)
    plt.ylabel('Latency (s)')
    plt.xlabel('Number of requests')
    plt.show()

def main():
    orders = make_orders()
    latencies = test(num_trials, orders)
    show_results(latencies)

if __name__ == '__main__':
    main()
