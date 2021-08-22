import csv
from datetime import datetime
import logging
import os
import threading
import time

from PIL import Image
import requests


logging.basicConfig(
    filename='color_scanner.log',
    level=logging.INFO,
    format='%(asctime)s | %(levelname)s | %(threadName)s | %(message)s'
)


def log_info(func):
    """decorator function for logging"""
    def wrapper(*args, **kwargs):
        logging.info(f'Starting {func.__name__}')
        val = func(*args, **kwargs)
        logging.info(f'Finished {func.__name__}')
        return val
    return wrapper


def load_urls(data_path='sample_data//input.txt'):
    with open(os.path.join(os.path.dirname(__file__), data_path), 'r') as f:
        urls = [line.strip() for line in f.readlines()]
    return urls


def find_top_colors(img, n=3):
    colors = img.getcolors(maxcolors=256**3)  # this is the main bottleneck
    if isinstance(colors[0][1], int):  # i.e. image has been removed
        return
    top_n = sorted(colors, reverse=True, key=lambda x: x[0])[:n]
    return [rgb_to_hex(x[1][0], x[1][1], x[1][2]) for x in top_n]


def rgb_to_hex(r, g, b):
    return r"#{:02X}{:02X}{:02X}".format(r, g, b)


@log_info
def load_image(url):
    return Image.open(requests.get(url, stream=True).raw)


class ColorScanner():
    def __init__(self, urls, fname, n_colors=3, write_freq=25):
        self.urls = urls
        self.n_colors = n_colors
        self.results = []
        self.fname = fname
        self.write_freq = write_freq

    def scan(self):
        for i, url in enumerate(self.urls):
            img = load_image(url)

            if i == 0:
                color_count_thread = None
            else:
                color_count_thread.join()
                if len(self.results) >= self.write_freq:
                    self.write_results()

            color_count_thread = threading.Thread(
                target=self.get_top_colors,
                args=(url, img)
            )
            color_count_thread.start()  # continue on to loading next image

        color_count_thread.join()
        if len(self.results) > 0:
            self.write_results()

    @log_info
    def get_top_colors(self, url, img):
        top_colors = find_top_colors(img)
        if top_colors:  # image not removed
            self.results.append([url] + top_colors)
        else:
            self.results.append([url])

    @log_info
    def write_results(self):
        logging.info(f"Writing {len(self.results)} results to {self.fname}")
        with open(self.fname, 'a') as csvfile:
            writer = csv.writer(csvfile, dialect='unix')
            writer.writerows(self.results)
        self.results = []


if __name__ == '__main__':
    t1 = time.perf_counter()
    fname = datetime.now().strftime("results_%Y%m%d_%H%M%S.csv")
    cs = ColorScanner(urls=load_urls()[:50], fname=fname)
    cs.scan()
    t2 = time.perf_counter()
    print(f'{t2 - t1} seconds')
