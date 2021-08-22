import csv
import threading
import os
import time
import requests
from PIL import Image


results = []


def load_urls(data_path='..//sample_data//input.txt'):
    with open(os.path.join(os.path.dirname(__file__), data_path), 'r') as f:
        urls = [line.strip() for line in f.readlines()][:10]
    return urls


def load_image(url):
    return Image.open(requests.get(url, stream=True).raw)


def find_top_colors(img, n=3):
    colors = img.getcolors(maxcolors=256**3)  # this is the main bottleneck
    if isinstance(colors[0][1], int):  # i.e. image has been removed
        return
    top_n = sorted(colors, reverse=True, key=lambda x: x[0])[:n]
    return [rgb_to_hex(x[1][0], x[1][1], x[1][2]) for x in top_n]


def rgb_to_hex(r, g, b):
    return r"#{:02X}{:02X}{:02X}".format(r, g, b)


# def top_colors_to_csv(url, img, results_csv):
#     with open(results_csv, 'a') as csvfile:
#         writer = csv.writer(csvfile, dialect='unix')
#         top_colors = find_top_colors(img)
#         if top_colors:
#             writer.writerow([url] + find_top_colors(img))
#         else:
#             writer.writerow([url])


def append_results(url, img):
    top_colors = find_top_colors(img)
    if top_colors:
        results.append([url] + top_colors)
    else:
        results.append([url])


# def write_results(results, results_csv):
#     with open(results_csv, 'a') as csvfile:
#         writer=csv.writer(csvfile, dialect='unix')
#         writer.writerow(results)

def process(urls, results_csv):
    """Load image and process
    
    As long as loading the image into memory is faster than counting
    the colors this shouldn't results.append([url])results.append([url]).append([url])results.append([url])be wasteful
    """

    color_count_thread = None
    results_writer_thread = None
    for url in urls:
        img = load_image(url)
        
        if color_count_thread is not None:
            color_count_thread.join()
            # results_writer_thread = threading.Thread(target=write_results, args=(results, results_csv))

        
        color_count_thread = threading.Thread(
            target=append_results, 
            args=(url, img)
        )
        
        color_count_thread.start()


if __name__ == '__main__':

    t1 = time.perf_counter()

    urls = load_urls()
    process(urls, 'res2.csv')
    print(results)

    t2 = time.perf_counter()
    print(f'{t2 - t1} seconds')
