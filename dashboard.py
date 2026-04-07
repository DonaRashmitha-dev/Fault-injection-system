import matplotlib
matplotlib.use("TkAgg")

import matplotlib.pyplot as plt
from metrics import get_metrics

def run_dashboard():
    plt.ion()

    while True:
        data = get_metrics()

        labels = list(data.keys())
        values = list(data.values())

        plt.clf()
        plt.bar(labels, values)
        plt.title("System Metrics")

        plt.draw()
        plt.pause(2)