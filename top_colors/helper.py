import time


def print_time(func):
    """decorator function for timing"""
    def wrapper(*args, **kwargs):
        t = time.process_time()
        val = func(*args, **kwargs)
        print(func, time.process_time() - t)
        return val
    return wrapper
