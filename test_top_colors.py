import os
from PIL import Image
import top_colors


def test_find_top_colors():
    im = Image.open("sample_data/mclaren.jpg")
    colors = top_colors.find_top_colors(im)
    test_colors = ["#82A2BB", "#7F9FB8", "#81A1BA"]
    assert colors == test_colors


def test_rgb_to_hex():
    assert top_colors.rgb_to_hex(0, 0, 0) == "#000000"
    assert top_colors.rgb_to_hex(255, 255, 255) == "#FFFFFF"
    assert top_colors.rgb_to_hex(123, 77, 24) == "#7B4D18"


def test_load_image():
    assert top_colors.load_image("https://i.imgur.com/pt9rmrv.jpg") == Image.open(
        "sample_data/watercolor.jpg"
    )
    assert top_colors.load_image('https://thisisafakeurl.com/fake') is None
    assert top_colors.load_image('invalid schema') is None


def test_check_valid_image():
    im = Image.open("sample_data/mclaren.jpg")
    assert top_colors.check_valid_image(im) is True
    assert top_colors.check_valid_image(im.convert('L')) is False


def test_find_eof():
    with open('sample_data/input.txt', 'r') as f:
        assert top_colors.find_eof(f) == 34623


def test_main():
    if os.path.exists('temp.csv'):
        os.remove('temp.csv')
    top_colors.main('sample_data/test_input.txt', 'temp.csv')

    with open('temp.csv', 'r') as f:
        test_lines = f.readlines()
    os.remove('temp.csv')

    with open('sample_data/test_results.csv', 'r') as f:
        compare_lines = f.readlines()

    assert len(test_lines) == len(compare_lines)
    assert all([line in test_lines for line in compare_lines]) is True
    assert all([line in compare_lines for line in test_lines]) is True
