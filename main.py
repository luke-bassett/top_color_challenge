"""
TODO
- decide how to handle removed images
"""
import csv
import logging
import numpy as np
import os
import time
from typing import List
from queue import Queue
from threading import Thread

from PIL import Image
import requests


logging.basicConfig(
    filename="color_scanner.log",
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(threadName)s | %(message)s",
)


def find_top_colors(img: Image, n: int = 3) -> List[str]:
    """Return top n colors from an image as hexes."""
    colors = img.getcolors(maxcolors=256 ** 3)
    top_n = sorted(colors, reverse=True, key=lambda x: x[0])[:n]
    return [rgb_to_hex(x[1][0], x[1][1], x[1][2]) for x in top_n]


def rgb_to_hex(r: int, g: int, b: int) -> str:
    """Return hex color from rgb values."""
    return r"#{:02X}{:02X}{:02X}".format(r, g, b)


def load_image(url: str) -> Image:
    """Return image loaded from url."""
    return Image.open(requests.get(url, stream=True).raw)


def check_valid_image(im: Image) -> bool:
    im_shape = np.array(im).shape
    return (len(im_shape) == 3) and (im_shape[-1] >= 3)


# Read
def read_urls(urls_fname: str, url_q: Queue) -> None:
    with open(urls_fname, 'r') as urlfile:
        while True:
            url = urlfile.readline().strip()
            if url != '':
                logging.info(f'add to url_q: {url}')
                url_q.put(url)
            else:
                logging.info('finished reading urls')
                break


# Process
def process_image(url_q, result_q):
    while True:
        if not url_q.empty():
            url = url_q.get()
            logging.info(f'processing image from url: {url}')
            im = load_image(url)
            if check_valid_image(im):
                res = [url] + find_top_colors(im)
                result_q.put(res)
        elif finished_reading:
            logging.info('finished processing images')
            break


# Write
def write_results(results_fname, result_q):
    with open(results_fname, 'a') as csvfile:
        writer = csv.writer(csvfile, dialect='unix')
        while True:
            if not result_q.empty():
                result = result_q.get()
                writer.writerow(result)
                logging.info(f'writing result: {result}')
            elif finished_processing:
                logging.info('finished writing results')
                break


def main(urls_fname, results_fname, n_process_threads=5, url_q_size=10):
    url_q = Queue(maxsize=url_q_size)
    result_q = Queue()

    global finished_reading
    finished_reading = False
    global finished_processing
    finished_processing = False

    read_thread = Thread(target=read_urls, args=(urls_fname, url_q))
    read_thread.start()
    write_thread = Thread(target=write_results, args=(results_fname, result_q))
    write_thread.start()

    process_threads = []
    for _ in range(n_process_threads):
        thread = Thread(target=process_image, args=(url_q, result_q))
        thread.start()
        process_threads.append(thread)

    read_thread.join()
    finished_reading = True
    [thread.join() for thread in process_threads]
    finished_processing = True
    write_thread.join()


if __name__ == '__main__':
    t1 = time.perf_counter()

    if os.path.exists('result.csv'):
        os.remove('result.csv')

    main('sample_data/shortinput.txt', 'test.csv')
    print(f"{time.perf_counter() - t1} seconds")
