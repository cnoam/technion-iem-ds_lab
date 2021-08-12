
def wrap_html_source(text):
    """
    wrap the text with html tags to force the browser show the code as was created without corrupting it
    """
    if text is None:
        text = "ERROR: got None value!"
    return "<html><pre><code> " + text +  "</code></pre></html>"


from functools import wraps
from time import time
import logging
def measure(func):
    @wraps(func)
    def _time_it(*args, **kwargs):
        start = int(round(time() * 1000))
        try:
            return func(*args, **kwargs)
        finally:
            end_ = int(round(time() * 1000)) - start
            if end_ >= 300:
                logging.fatal(f"Total execution time: {end_ if end_ > 0 else 0} ms")
    return _time_it


def version_string() -> str:
    """ Ideally we would read the git commit ID,
    but it is not available when running in the docker container.
    """
    # import version
    return "unknown" # version.__version__


if __name__ == "__main__":

    @measure
    def hello():
        from time import sleep
        sleep(0.335)
        print('hello world')

    hello()