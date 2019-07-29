"""
allow up to 3 submissions for each team
keep the best score in a table (and save the table to disk)

"""

import pickle
import logging
import threading

logger = logging.getLogger(__name__)


class WorkshopDb:
    """A wrapper around a 'database' of the submissions.
    It isolates the internal implementation from the user of the class
    """
    MAX_SUBMISSIONS = 3
    pickle_file_name = 'workshop_db.pickle'
    rw_lock = threading.Lock()

    def __init__(self):
        """
        Load the data from disk (if we can find it)
        STRONG assumption: I am the only one who can modify that data!
        MultiThread safe: hopefully (not tested)
        """
        self.data = {}  # submission_id -> (score, num_submissions)
        try:
            with open(self.pickle_file_name, "rb") as f:
                with WorkshopDb.rw_lock:
                    self.data = pickle.load(f)
        except FileNotFoundError as ex:
            logger.warning("pickle file not found")

    def try_add_submission(self, submission_id):
        """
        :param submission_id: submission name that is not changed between submissions (e.g. user name)
        :return: True iff the submission is approved to be deployed.
        """
        with WorkshopDb.rw_lock:  # take no chance: put the lock on everything
            if submission_id not in self.data:
                self.data[submission_id] = (0.0, 1)
                self._commit()
                return True
            else:
                if self.data[submission_id][1] < WorkshopDb.MAX_SUBMISSIONS:
                    self.data[submission_id] = (self.data[submission_id][0], self.data[submission_id][1] + 1)
                    self._commit()
                    return True
                else:
                    return False

    def add_score(self, submission_id, score):
        """
        Update the max score in the db.
        :param submission_id:
        :param score:
        :return: None
        """
        with WorkshopDb.rw_lock:  # take no chance: put the lock on everything
            #  grace: if the score is 0.0, don't count this submission
            if score <= 0.0:
                # undo the submission counter.
                t = self.data[submission_id]
                t[1] -= 1
                assert t[1] >= 0
                self.data[submission_id] = t

            current_score = self.data[submission_id][0]
            if score > current_score:
                self.data[submission_id] = (score, self.data[submission_id][1])
                self._commit()

    def get_scores(self):
        return self.data

    def _commit(self):
        """ save to a pickle file on disk. No need to protect with lock since all callers are locked"""
        try:
            with open(self.pickle_file_name, "wb") as f:
                pickle.dump(self.data, f)
        except FileNotFoundError as ex:
            logger.warning("pickle file:" + str(ex))

    def purge_db(self):
        import os
        try:
            os.unlink(self.pickle_file_name)
        except FileNotFoundError:
            pass
