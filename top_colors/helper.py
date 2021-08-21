import time


def rgb_to_hex(r, g, b):
    return r"#{:02X}{:02X}{:02X}".format(r, g, b)


def print_time(func):
    """decorator function for timing"""
    def wrapper(*args, **kwargs):
        t = time.process_time()
        val = func(*args, **kwargs)
        print(func, time.process_time() - t)
        return val
    return wrapper
