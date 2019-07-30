"""
check_ex9 -- the outcome of Python workshop

Check the performance  of the supplied classifier on the data
that will be supplied here
Upon return, the JobStatusDb will be updated.
"""


import re
import sys
import os


from logger_init import init_logger
logger = init_logger(__name__)

try:
    from model import Model
except ImportError as ex:
    logger.error("Could not import Model: " +  str(ex))
    exit(1)


def _load_reference_labels(path):
    import pickle
    import os
    with open(os.path.join(path,'reference_labels.pickle'), 'rb') as fin:
        ref = pickle.load(fin)
    return ref


if __name__ == "__main__":
 
    from server_codes import ExitCode
    from sklearn.preprocessing import MultiLabelBinarizer
    import sklearn.metrics
    
    dpath = os.environ['DATA_PATH']  # will raise KeyError if not found
    user_data_dir = '.'
    test_data_dir = dpath + '/reuters_test_data'
    secret_labels_dir = dpath + '/secret_labels'

    try:
        model = Model(user_data_dir)

        reference = _load_reference_labels(secret_labels_dir)

        predictions = model.predict(test_data_dir)
    except NotImplementedError as ex:
        logger.error("Exception raised in tested code:" + str(ex))
        exit(ExitCode.PROCESS_ERROR)
    if type(predictions) != tuple:
        logger.error("Expected type tuple from tested code")
        exit(ExitCode.PROCESS_ERROR)
    mlb = MultiLabelBinarizer()
    r = mlb.fit_transform(reference)
    p = mlb.transform(predictions)
    score = 0
    try:
        score = sklearn.metrics.f1_score(y_true=r, y_pred=p, average='macro')
    except ValueError as ex:
        logger.error("result value is invalid: " + str(ex))
        exit(ExitCode.PROCESS_ERROR)
    print("F1 score: ", score)
    exit(0)

