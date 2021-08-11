
"""We need the batch Id from the output of the run ( in a text string).
This is because we run the call in a subprocess.
"""
import logging


class SparkCallback:
    def __init__(self, sender, running_jobs, cb=None):
        """
        :param sender: unique ID of the user who sends the job (str)
        :param running_jobs dict of sender_ID -> batch_ID
        :param cb: optional callable
        """
        self.next_cb = cb
        self.batch_id = None
        self.source = sender
        self.db = running_jobs
        if sender is None or len(sender) < 2:
            raise ValueError('missing sender name')

    def at_end(self, *args, **kwargs):
        d = args[0][0]
        stdout_s = d['stdout']
        exit_code = d['exit_code']
        if exit_code == 0:
            self._parse_batch_id(stdout_str=stdout_s)
            # add the new batch_id only if success
            self.db[self.source] = self.batch_id
        if self.next_cb:
            self.next_cb()

    def _parse_batch_id(self, stdout_str ):
        """look for text like  BATCH ID = 666  """
        import re
        matches = re.findall('^BATCH ID = (\d+)', stdout_str)
        if len(matches) == 0:
            logging.warning("batch ID not found in stdout")
        else:
            self.batch_id = matches[0]


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
