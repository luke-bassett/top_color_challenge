
import requests
from PIL import Image
from find_top_colors import find_top_colors


class ColorScanner():
    def __init__(self, n=3):
        self.n = n

    def load_image(self, url):
        print(url)
        self.image = Image.open(requests.get(url, stream=True).raw)
        self.url = url

    def get_top_colors(self):
        """return top n colors as a list of hexes"""
        self.top_colors = find_top_colors(self.image, n=self.n)
        return self.top_colors
