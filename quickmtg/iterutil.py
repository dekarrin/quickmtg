from itertools import zip_longest

def grouper(iterable, n, fillvalue=None):
    """Collect data into fixed-size chunks or blocks.
    Returned iterator will iterate over n items at a time in the original
    iterable."""
    args = [iter(iterable)] * n
    return zip_longest(*args, fillvalue=fillvalue)