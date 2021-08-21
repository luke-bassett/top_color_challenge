import helper


def find_top_colors(img, n=3):
    colors = img.getcolors(maxcolors=256**3)  # this is the main bottleneck

    if isinstance(colors[0][1], int):  # i.e. image has been removed
        return

    top_n = sorted(colors, reverse=True, key=lambda x: x[0])[:n]

    return [helper.rgb_to_hex(x[1][0], x[1][1], x[1][2]) for x in top_n]
