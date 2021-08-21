import os
from color_scanner import ColorScanner

data_path = '..//sample_data//input.txt'
with open(os.path.join(os.path.dirname(__file__), data_path), 'r') as f:
    urls = [line.strip() for line in f.readlines()]

results = []

for url in urls[:10]:
    sc = ColorScanner()
    sc.load_image(url)
    print(sc.get_top_colors())
    results.append((url, sc.top_colors))

print(results)
