"""
allow up to 3 submissions for each team
keep the best score

"""

import pickle
import logging

logger = logging.getLogger(__name__)


class WorkshopDb():
    """A wrapper around a 'database' of the submissions.
    It isolates the internal implementation from the user of the class
    """
    MAX_SUBMISSIONS = 3
    pickle_file_name = 'workshop_db.pickle'

    def __init__(self):
        self.data = {}  # submission_id -> (score, num_submissions)
        try:
            with  open(self.pickle_file_name, "rb") as f:
                self.data = pickle.load(f)
        except FileNotFoundError as ex:
            logger.warning("pickle file not found")


    def try_add_submission(self, submission_id):
        if submission_id not in self.data:
            self.data[submission_id] = (0.0, 1)
            self._commit()
            return True
        else:
            if self.data[submission_id][1] < WorkshopDb.MAX_SUBMISSIONS:
                self.data[submission_id] = (self.data[submission_id][0] , self.data[submission_id][1] + 1)
                self._commit()
                return True
            else:
                return False


    def add_score(self,submission_id,score):
        current_score = self.data[submission_id][0]
        if score > current_score:
            self.data[submission_id] = (score, self.data[submission_id][1])
            self._commit()


    def get_scores(self):
        return self.data

    def _commit(self):
        try:
            with open(self.pickle_file_name, "wb") as f:
                pickle.dump(self.data,f)
        except FileNotFoundError as ex:
            logger.warning("pickle file:"  + str(ex))


    def purge_db(self):
        import os
        try:
            os.unlink(self.pickle_file_name)
        except FileNotFoundError:
            pass