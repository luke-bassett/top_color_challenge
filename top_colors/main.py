from multiprocessing import Pool
import os
import time
from color_scanner import ColorScanner


def load_data(data_path='..//sample_data//input.txt'):
    with open(os.path.join(os.path.dirname(__file__), data_path), 'r') as f:
        urls = [line.strip() for line in f.readlines()][:24]
    return urls


def scan_from_url(url):
    scanner = ColorScanner(url)
    scanner.load_image()
    return url, scanner.get_top_colors()


def process(func, arg_list, n_procs=12):
    with Pool(n_procs) as p:
        results = p.map(func, arg_list)
    return results


if __name__ == '__main__':

    t1 = time.perf_counter()

    urls = load_data()
    print(process(scan_from_url, urls))

    t2 = time.perf_counter()
    print(f'finished in {t2 - t1} seconds')
