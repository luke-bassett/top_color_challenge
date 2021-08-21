import os
import time
from color_scanner import ColorScanner

t1 = time.perf_counter()

data_path = '..//sample_data//input.txt'
with open(os.path.join(os.path.dirname(__file__), data_path), 'r') as f:
    urls = [line.strip() for line in f.readlines()]

results = []

for url in urls[:25]:
    sc = ColorScanner(url)
    sc.load_image()
    print(sc.get_top_colors())
    results.append((url, sc.top_colors))

print(results)


t2 = time.perf_counter()
print(f'finished in {t2 - t1} seconds')
