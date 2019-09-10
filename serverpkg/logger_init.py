import os
import logging
_log_path="/logs/"


def _in_docker():
    with open('/proc/1/cgroup', 'rt') as ifh:
        return 'docker' in ifh.read()


if not _in_docker():
    _log_path = "./logs/"
    try:
        os.mkdir(_log_path)
    except FileExistsError:
        pass


# prepare a logger to my liking
def init_logger(logger_name):
    """
    prepare a logger with both file and stream handlers
    :return: initialized logger object
    """
    logger = logging.getLogger(logger_name)
    stream_handler = logging.StreamHandler()
    file_handler = logging.FileHandler(filename=_log_path +'homework_checker.log')
    logger.setLevel(logging.DEBUG) # for the whole logger
    #stream_handler.setLevel(logging.DEBUG) # for each handler (if different from the logger)
    #file_handler.setLevel(logging.DEBUG)
    log_formatter = logging.Formatter('%(asctime)-15s %(name)s - %(levelname)s - %(message)s')
    file_handler.setFormatter(log_formatter)
    stream_handler.setFormatter(log_formatter)
    logger.addHandler(stream_handler)
    logger.addHandler(file_handler)
    return logger


# verify path is writable
tmp = open(_log_path+"test","w") # should raise if there is an error
tmp.close()
os.unlink(_log_path+"test")
