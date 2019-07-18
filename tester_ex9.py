"""
check_ex9 -- the outcome of Python workshop

Check the performance  of the supplied classifier on the data wil supply here
Upon return, the JobStatusDb will be updated.
"""

import re
import sys
import os

dest_dir = './tmp/'
testing_dir = './testing/'
try:
    from main import run_me
except ImportError:
    print("Could not import main.run_me")
    exit(1)


def create_test_set():
    """The full set is 20000 documents.
    Keep 3000 aside for testing, and give them the rest (17K)
    """
    import random
    import shutil
    src_dir='/home/noam/technion-iem-ds_lab/data/reut/'
    file_pattern = 'reut2-%03d.sgm'
    num_files = 22
    shuffled = list(range(num_files))
    random.shuffle(shuffled)
    training = shuffled[:17]
    testing = shuffled[17:]
    count = 0
    for i in training:
        src = src_dir + file_pattern % i
        dest = dest_dir + ('f-%03d.sgm'% count)
        shutil.copy(src, dest)
        count += 1

    os.makedirs(testing_dir,exist_ok=True)
    for i in testing:
        src = src_dir + file_pattern % i
        dest = testing_dir + ('f-%03d.sgm'%i)
        shutil.copy(src, dest)


if __name__ == "__main__":
    from server_codes import ExitCode
    from sklearn.metrics import f1_score

    # put aside some of the files for testing, and the rest will be used for training.
    if not os.path.exists(testing_dir):
        create_test_set()

    # TODO: make sure we don't have any of the forbidden modules
    res = []
    try:

        res = run_me(dest_dir)
        # TODO: make sure we don't have any of the forbidden modules
    except:
        print("Exception raised in tested code")
        exit(ExitCode.PROCESS_ERROR)
    if type(res) != list:
        print("Expected type list from tested code")
        exit(ExitCode.PROCESS_ERROR)

    from sklearn.preprocessing import MultiLabelBinarizer
    mlb = MultiLabelBinarizer()

    # TODO: allow partial match: compute the F1 for each label, and then average them for the one record.

    #TODO: each team can submit up to 3 codes. The final score is the best of three.

    true_values = [('acq',), ('acq',), ('de','uk'), ('uk','de')]
    true_values_bin = mlb.fit_transform(true_values)
    score =0
    try:
        res_bin = mlb.fit_transform(res)
        score = f1_score(true_values_bin, res_bin, average='macro')
    except ValueError as ex:
        print("result value is invalid: " + str(ex))
        exit(ExitCode.PROCESS_ERROR)
    print("F1 score: ",score)
    #TODO save the score to some DB. Can I use the same pickle? force reloading?
    exit(0)
