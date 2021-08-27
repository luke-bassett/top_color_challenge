"""Finds top colors per image from a list of image urls.

This module reads URLs from a provided file, then retrieves the images at the URLs
and finds the top three most prevelent colors. The output is a csv with the format
(url, color, color, color). URLs for which the image has been removed are not
included in the results file.

The program is capable of handling large input files. Separate threads are used
for reading from the input, counting the colors, and writing to the output.
Additionally loading the entire input or output file to memory is avoided.

The number of threads used for counting colors is configurable since this is the
most resource intensive task. A single thread is used for reading from the input
file and another for writing to the results file.

Functions
---------
find_top_colors
    Return top n colors from an image as hexes.

rgb_to_hex
    Return hex color from rgb values.

load_image
    Return image loaded from url, avoids saving to disk.

check_valid_image
    In cases where the image has been removed a grayscale image is returned.
    This function checks the shape of the image to confirm that there are at
    least 3 channels. (RGB)

find_eof
    Returns EOF location

read_urls
    Reads urls from input file, url_path, and puts them into urls.

process_image
    Gets urls from urls, retrieves image, counts colors, and puts results
    into results. When multiple threads run this function, waiting for
    respose from the url will naturally release the thread and allow for other
    threads to proceed.

write_results
    Gets results from results and appends them the the file at result_path.
    Creates file if it does not exist.

runner
    Reads urls from url_path and writes results to result_path. This
    functions handles creation of threads. n_process_threads defines how many
    threads are created to retrieve images and count colors. url_q_size sets the
    max size of the urls. Limiting the size of the urls keeps the program from
    reading all items in the input file before continuing.

    The defaults for n_process_threads and url_q_size are candidates for furthur
    tuning and the optimal value will depend on the machine executing the module.


Example Usage
-------------
> python top_colors.py -i [input path] -o [output path] -t [n threads] -q [input q size]
    -i --urlfile    REQUIRED path of file containing urls, one pre linE
    -o --resfile    REQUIRED path of file to append results to
    -t --threads    OPTIONAL number of threads for image retrieval and color counting
    -q --qsize      OPTIONAL number of ulrs in queue
"""
import argparse
import csv
import logging
import numpy as np
import random
import time
from typing import List, TextIO
from queue import Queue
from threading import Thread

import PIL
from PIL import Image
import requests

DEFAULT_THREADS = 5
DEFAULT_URL_Q = 10

# Parser -------------------------------------------------------------------------------
parser = argparse.ArgumentParser(
    description="""Find top 3 most prevelent colors from images and
                save to csv. Images are specified by a list of urls."""
)
parser.add_argument(
    "-i", "--urlfile", type=str, help="File containing urls. One url per line."
)
parser.add_argument(
    "-o",
    "--resfile",
    type=str,
    help="Path to save results csv. Will append if already exists.",
)
parser.add_argument(
    "-t",
    "--threads",
    type=int,
    default=DEFAULT_THREADS,
    help="Number of threads for image retrieval and color counting.",
)
parser.add_argument(
    "-q", "--qsize", type=int, default=DEFAULT_URL_Q, help="Size of url queue."
)
args = parser.parse_args()
# End Parser ---------------------------------------------------------------------------


logging.basicConfig(
    filename="color_scanner.log",
    level=logging.DEBUG,
    format="%(asctime)s | %(levelname)s | %(threadName)s | %(message)s",
)


def find_top_colors(im: Image, n: int = 3) -> List[str]:
    """Return top n colors from an image as hexes.

    args: im: PIL.Image, n: int
    returns: A list of the top n most prevelent colors in hex format.
    """
    colors = im.getcolors(maxcolors=256 ** 3)
    top_n = sorted(colors, reverse=True, key=lambda x: x[0])[:n]
    return [rgb_to_hex(x[1][0], x[1][1], x[1][2]) for x in top_n]


def rgb_to_hex(r: int, g: int, b: int) -> str:
    """Return hex color from rgb values.

    args: r: int, g: int, b: int
    returns: The hex color as a string (example "#FFFFFF").
    """
    return r"#{:02X}{:02X}{:02X}".format(r, g, b)


def load_image(url: str) -> Image:
    """Return image loaded from url, avoids saving to disk.

    args: url: str
    returns: PIL.Image
    """
    try:
        r = requests.get(url, stream=True).raw
    except requests.exceptions.ConnectionError:
        logging.warning(f"Failed to connect to {url}")
        return
    except requests.exceptions.MissingSchema:
        logging.warning(f"Invalid URL schema {url}")
        return

    try:
        return Image.open(r)
    except PIL.UnidentifiedImageError:
        logging.warning(f"No image found at {url}")


def check_valid_image(im: Image) -> bool:
    """Returns true if image is valid.

    args: im: PIL.Image
    returns: Bool representing whether the image has been removed.

    In cases where the image has been removed a grayscale image is returned
    with text stating that the target images has been removed.
    This function checks the shape of the image to confirm that there are at
    least 3 channels. (RGB)

    This may not be the desired behavior and could be changed.
    """
    im_shape = np.array(im).shape
    return (len(im_shape) == 3) and (im_shape[-1] >= 3)


def find_eof(f: TextIO) -> int:
    """Returns end-of-file position."""
    f.seek(0, 2)  # end of file
    eof = f.tell()
    f.seek(0, 0)  # begining of file
    return eof


def read_urls(url_path: str, urls: Queue) -> None:
    """Reads from url_path and puts into queue urls.

    args: url_path: str, urls: queue.Queue
    returns: None
    """
    try:
        with open(url_path, "r") as urlfile:
            eof = find_eof(urlfile)
            while True:
                url = urlfile.readline().strip()
                if url != "":
                    logging.debug(f"add to urls: {url}")
                    urls.put(url)
                elif urlfile.tell() != eof:  # handle blank line
                    continue
                else:
                    break
    except FileNotFoundError as err:
        logging.critical("Input file not found.")
        raise Exception("Input file not found") from err


def process_image(urls: Queue, results: Queue) -> None:
    """Gets urls from queue, and puts results into queue.

    args: urls: queue.Queue, results: queue.Queue
    returns: None

    When multiple threads run this function, waiting for
    respose from the url will naturally release the thread and allow for other
    threads to proceed.
    """
    while True:
        if not urls.empty():
            url = urls.get()
            logging.debug(f"processing image from url: {url}")
            im = load_image(url)
            if not im:
                continue
            if not check_valid_image(im):
                logging.warning(f"Image has been removed, {url}")
                continue
            logging.debug(f"Image loaded from {url}")
            res = [url] + find_top_colors(im)
            logging.debug(f"Found top colors from {url}")
            results.put(res)
        elif finished_reading:
            logging.debug("thread finished processing images")
            break
        time.sleep(random.random() * 0.001)


def write_results(result_path: str, results: Queue) -> None:
    """Gets results and appends them to result_path.

    args: results: queue.Queue, result_path: str
    returns: None

    Creates file if it does not exist.
    """
    try:
        with open(result_path, "a") as csvfile:
            writer = csv.writer(csvfile, dialect="unix")
            while True:
                if not results.empty():
                    result = results.get()
                    writer.writerow(result)
                    logging.debug(f"writing result: {result}")
                elif finished_processing:
                    break
                time.sleep(random.random() * 0.001)
    except FileNotFoundError as err:
        logging.critical("Result path not valid.")
        raise Exception("Result path not valid") from err


def runner(
    url_path: str,
    result_path: str,
    n_process_threads: int = DEFAULT_THREADS,
    url_q_size: int = DEFAULT_URL_Q,
) -> None:
    """Reads urls from url_path and writes results to result_path.

    args: url_path: str, result_path: str, n_process_threads: int = 5,
          url_q_size: int = 10
    returns: None

    This functions handles creation of threads. n_process_threads defines how
    many threads are created to retrieve images and count colors. url_q_size sets
    the max size of the urls. Limiting the size of the urls keeps the program
    from reading all items in the input file before continuing.

    The defaults for n_process_threads and url_q_size are candidates for furthur
    tuning and the optimal value will depend on the machine executing the module.
    """
    global finished_reading
    finished_reading = False
    global finished_processing
    finished_processing = False

    urls = Queue(maxsize=url_q_size)
    results = Queue()

    read_thread = Thread(target=read_urls, args=(url_path, urls))
    logging.info("Starting read URLs thread")
    read_thread.start()
    write_thread = Thread(target=write_results, args=(result_path, results))
    logging.info("Starting writing results thread.")
    write_thread.start()

    process_threads = []
    logging.info(f"Starting {n_process_threads} process images thread(s).")
    for _ in range(n_process_threads):
        thread = Thread(target=process_image, args=(urls, results))
        thread.start()
        process_threads.append(thread)

    read_thread.join()
    finished_reading = True
    logging.info("Finished reading URLS.")

    [thread.join() for thread in process_threads]
    finished_processing = True
    logging.info("All threads finished processing images.")

    write_thread.join()
    logging.info("Finished writing results.")


if __name__ == "__main__":
    t1 = time.perf_counter()
    runner(args.urlfile, args.resfile, args.threads, args.qsize)
    print(f"Finished in {round(time.perf_counter() - t1, 3)} seconds")
