from functools import wraps
from time import time
import logging
import re


def wrap_html_source(text):
    """
    wrap the text with html tags to force the browser show the code as was created without corrupting it
    """
    if text is None:
        text = "ERROR: got None value!"
    return "<html><pre><code> " + text +  "</code></pre></html>"


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


def memoize(func):
    cache = {}

    def wrapped(*args, **kwargs):
        key = (tuple(args), tuple(kwargs.items()))
        if key not in cache:
            cache[key] = func(*args, **kwargs)
        return cache[key]

    return wrapped


def version_string():
    """Try to get the commit ID.
    If running in docker, it is not available, so try using an env var"""
    if in_docker():
        import version
        return version.commit_id
    else:
        return commitId()


def commitId() -> str:
    """ try to get the current git commit Id.
    This will NOT run when inside a docker container.
    :return short commit ID or empty string"""
    import subprocess
    id = ''
    completed_proc = subprocess.run(['bash', '-c','git rev-parse --short HEAD'],
                                    check=False, stdout=subprocess.PIPE, stderr=subprocess.PIPE )
    if completed_proc.returncode == 0:
        id = completed_proc.stdout.decode()
    return id


def load_allowed_submitters_id(fname: str)-> set:
    s = set()
    try:
        with open(fname, "r") as fin:
            s = fin.readlines()
            s = { x.strip() for x in s}
    except:
        pass
    return s


def in_docker():
    """:return True if running inside a docker container
    https://www.baeldung.com/linux/is-process-running-inside-container
    """
    with open('/proc/1/sched', 'rt') as ifh:
        line = ifh.readline()
        return 'systemd' not in line


def replace_url_to_link(value):
    # Replace url to link
    # https://gist.github.com/guillaumepiot/4539986
    urls = re.compile(r"((https?):((//)|(\\\\))+[\w\d:#@%/;$()~_?\+-=\\\.&]*)", re.MULTILINE|re.UNICODE)
    value = urls.sub(r'<a href="\1" target="_blank">\1</a>', value)
    # Replace email to mailto
    urls = re.compile(r"([\w\-\.]+@(\w[\w\-]+\.)+[\w\-]+)", re.MULTILINE|re.UNICODE)
    value = urls.sub(r'<a href="mailto:\1">\1</a>', value)
    return value


if __name__ == "__main__":
    @measure
    def hello():
        from time import sleep
        sleep(0.335)
        print('hello world')

    hello()