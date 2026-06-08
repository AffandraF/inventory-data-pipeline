import time
import functools
import logging
logger = logging.getLogger(__name__)

def timeit(func):
    # Decorator to measure and log the execution time of a function.
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        start = time.perf_counter()
        result = func(*args, **kwargs)
        elapsed = time.perf_counter() - start
        logger.info(f"[{func.__name__}] finished in {elapsed:.4f} seconds")
        return result
    return wrapper
