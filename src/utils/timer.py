import time
from contextlib import contextmanager


@contextmanager
def Timer():
    class _Timer:
        def __init__(self):
            self.start = 0
            self.end = 0

        @property
        def elapsed(self):
            return self.end - self.start

    timer = _Timer()
    timer.start = time.time()
    try:
        yield timer
    finally:
        timer.end = time.time()
