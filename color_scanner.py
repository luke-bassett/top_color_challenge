"""
Scan a list of urls of images and write a csv of urls and top colors.

Classes:

    ColorScanner

Functions:

    load_urls(str) -> List[str]
    find_top_colors(PIL.Image, int) -> List[str]
    rgb_to_hex(int, int, int) -> str
    load_image(str) -> PIL.Image

Decorator Functions:

    log_info(callable) -> callable

Writes log to module directory, color_scanner.log

"""
import csv
from datetime import datetime
import logging
import os
import threading
import time
from typing import List

from PIL import Image
import requests


logging.basicConfig(
    filename='color_scanner.log',
    level=logging.INFO,
    format='%(asctime)s | %(levelname)s | %(threadName)s | %(message)s'
)


def log_info(func: callable) -> callable:
    """Decorator function for logging at info level."""
    def wrapper(*args, **kwargs):
        logging.info(f'Starting {func.__name__}')
        val = func(*args, **kwargs)
        logging.info(f'Finished {func.__name__}')
        return val
    return wrapper


def load_urls(data_path: str='sample_data//input.txt') -> List[str]:
    """Load urls from file, return list of urls."""
    with open(os.path.join(os.path.dirname(__file__), data_path), 'r') as f:
        urls = [line.strip() for line in f.readlines()]
    return urls


def find_top_colors(img: Image, n: int=3) -> List[str]:
    """Return top n colors from an image as hexes."""
    colors = img.getcolors(maxcolors=256**3)  # this is the main bottleneck
    if isinstance(colors[0][1], int):  # i.e. image has been removed
        return
    top_n = sorted(colors, reverse=True, key=lambda x: x[0])[:n]
    return [rgb_to_hex(x[1][0], x[1][1], x[1][2]) for x in top_n]


def rgb_to_hex(r: int, g: int, b: int) -> str:
    """Return hex color from rgb values."""
    return r"#{:02X}{:02X}{:02X}".format(r, g, b)


@log_info
def load_image(url: str) -> Image:
    """Return image loaded from url."""
    return Image.open(requests.get(url, stream=True).raw)


class ColorScanner:
    """
    An object to handle scanning image urls and writing top colors.

    Attributes
    ----------
    urls : list
        list of image urls to scan
    fname : str
        output file name
    n_colors : ing
        number of top colors to find
    write_freq : int
        how many images to scan before writing results to disk

    Methods
    -------
    scan()
        scan urls and write results to file, fname
    get_top_colors(url, img)
        get the top colors for a single image and append to results
    write_results()
        write resutls to file and clear list of results
    """

    def __init__(self, urls: List[str], fname: str, n_colors: int=3, write_freq: int=25) -> None:
        """
        Constructs all the necessary attributes for the ColorScanner object.

        Parameters
        ----------
            urls : list
                list of image urls to scan
            fname : str
                output file name
            n_colors : ing
                number of top colors to find
            write_freq : int
                how many images to scan before writing results to disk
            self.results : list
                an empyt list of results to append to

        """
        self.urls = urls
        self.n_colors = n_colors
        self.fname = fname
        self.write_freq = write_freq
        self.results = []

    def scan(self) -> None:
        """
        Iterates throut ColorScanner.urls and finds top n colors.

        Color counting is handled in a separate thread so that loading of
        the next image can begin concurrently if resources are available.

        Color counting takes longer than image loading. For simplicity only
        one additional image is loaded during color counting.

        Writing resutls is handled on the main thread because it is very
        resouce light. Appending does not load the results file to memory.
        """
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
                args=(url, img),
                name='countThread'
            )
            color_count_thread.start()  # main thread continue to next image

        color_count_thread.join()
        if len(self.results) > 0:
            self.write_results()

    @log_info
    def get_top_colors(self, url: str, img: Image) -> None:
        """
        Append url and top colors to ColorScanner.results

        Parameters
        ----------
        url : str
            url of associated image
        img : PIL.Image
            image to be scanned

        Returns
        -------
        None
        """
        top_colors = find_top_colors(img)
        if top_colors:  # image not removed
            self.results.append([url] + top_colors)
        else:
            self.results.append([url])

    @log_info
    def write_results(self) -> None:
        """
        Write contents of Colorscanner.results to file.

        After writing to file ColorScanner.fname, Colorscanner.results
        is cleared.
        """
        logging.info(f"Writing {len(self.results)} results to {self.fname}")
        with open(self.fname, 'a') as csvfile:
            writer = csv.writer(csvfile, dialect='unix')
            writer.writerows(self.results)
        self.results = []


if __name__ == '__main__':
    t1 = time.perf_counter()
    fname = datetime.now().strftime("results_%Y%m%d_%H%M%S.csv")
    cs = ColorScanner(urls=load_urls()[:10], fname=fname)
    cs.scan()
    t2 = time.perf_counter()
    print(f'{t2 - t1} seconds')
