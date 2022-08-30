
"""We need the batch Id from the output of the run ( in a text string).
This is because we run the call in a subprocess.
"""

from serverpkg.logger import Logger
from serverpkg.spark import SparkResources

logger = Logger(__name__).logger

class SparkCallback:
    def __init__(self, sender, resource_m : SparkResources.SparkResources, cb=None):
        """
        :param sender: unique ID of the user who sends the job (str)
        :param running_jobs dict of sender_ID -> batch_ID
        :param cb: optional callable
        """
        self.next_cb = cb
        self.sender = sender
        self.rm = resource_m
        if sender is None or len(sender) < 2:
            raise ValueError('missing sender name')

    def at_end(self, *args, **kwargs):
        d = args[0][0]
        stdout_s = d['stdout']
        exit_code = d['exit_code']
        if exit_code == 0:
            b_id = self._parse_batch_id(stdout_str=stdout_s)
            if b_id is not None:
                self.rm.add_batch_id(user_id=self.sender, batch_id=b_id)
        if self.next_cb:
            self.next_cb()

    def _parse_batch_id(self, stdout_str ):
        """look for text like  BATCH ID = 666  """
        import re
        matches = re.findall('^BATCH ID = (\d+)', stdout_str, flags=re.MULTILINE)
        if len(matches) == 0:
            logger.warning("batch ID not found in stdout")
            return None
        else:
            return matches[0]


    def __call__(self, *args, **kwargs):
        """ usage:
        >>> s = SparkCallback(a_callback)
        >>> s(stdout_text)
        """
        self.at_end(args, kwargs)


def test():
    c = SparkCallback( lambda : print("outer CB"))
    c("BATCH ID = 543")


if __name__ == "__main__":
    test()
