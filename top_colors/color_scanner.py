
import requests
from PIL import Image
from find_top_colors import find_top_colors


class ColorScanner():
    def __init__(self, url, n=3):
        self.url = url
        self.n = n

    def load_image(self):
        self.image = Image.open(requests.get(self.url, stream=True).raw)

    def get_top_colors(self):
        """return top n colors as a list of hexes"""
        self.top_colors = find_top_colors(self.image, n=self.n)
        return self.top_colors
