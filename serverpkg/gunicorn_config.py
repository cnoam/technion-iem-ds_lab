from serverpkg.server import one_time_init
# gunicorn -c serverpkg/gunicorn_config.py ...


def on_starting(server):
    """
    Do something on server start
    before starting any of the workers.
    """
    print("gunicorn hook: on_starting")
    one_time_init()


def post_worker_init(worker):
    print("Worker has been initialized. Worker Process id –>", worker.pid)