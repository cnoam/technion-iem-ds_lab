import os
import logging


def _in_docker():
    with open('/proc/1/cgroup', 'rt') as ifh:
        return 'docker' in ifh.read()


class Logger:
    """
    pre configured logger object.
    simply give it module name
    """
    log_dir_name = os.environ['CHECKER_LOG_DIR'] # "/logs"
    def __init__(self, name):
        self.log_path = Logger.log_dir_name
        if not _in_docker():
            self.log_path = "./logs/"
        try:
             os.mkdir(self.log_path)
        except FileExistsError:
            pass
        except PermissionError:
            logging.error("Failed creating %s. Check directory permissions" % self.log_path)
            #raise

        self._check_writable()
        self.logger = self._init_logger(name)


    # prepare a logger to my liking
    def _init_logger(self,logger_name): # -> Logger
        """
        prepare a logger with both file and stream handlers
        :return: initialized logger object
        """
        logger = logging.getLogger(logger_name)
        stream_handler = logging.StreamHandler()
        file_handler = logging.FileHandler(filename=self.log_path +'/homework_checker.log')
        logger.setLevel(logging.DEBUG) # for the whole logger
        #stream_handler.setLevel(logging.DEBUG) # for each handler (if different from the logger)
        #file_handler.setLevel(logging.DEBUG)
        log_formatter = logging.Formatter('%(asctime)-15s %(name)s - %(levelname)s - %(message)s')
        file_handler.setFormatter(log_formatter)
        stream_handler.setFormatter(log_formatter)
        logger.addHandler(stream_handler)
        logger.addHandler(file_handler)
        return logger

    def _check_writable(self):
        # verify path is writable
        tmp = open(self.log_path+"/test","w") # should raise if there is an error
        tmp.close()
        try:
            os.unlink(self.log_path+"/test")
        except FileNotFoundError:
            # if several instances are run together (e.g. 3 by gunicorn)
            # they will disturb each other:
            # P1 opens, P2 opens, P1 unlink, P2 try to unlink and fails.
            # can solve it in several ways, but the simplest is just to ignore this
            # specific error because we don't care who deleted this file
            #self.logger.info("Someone deleted the test file but that's ok.")
            #raise Exception("d not ignore")
            pass

