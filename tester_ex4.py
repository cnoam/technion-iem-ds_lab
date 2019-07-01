"""
check_ex4

Check if two text files are considered equal for course 94201, 2019-06 homework ex 4

>>> from tester_ex4 import check
>>> check("golden_4", "test_4")
True

The output format

Question 1:
classifier KNN: value of accuracy, value of recall, value of precision
classifier Rocchio:  value of accuracy, value of recall, value of precision

Question 2:
classifier KNN: value of accuracy
classifier Rocchio: value of accuracy
"""

import re
import sys


def parse_result_file(filename):
    with open(filename) as fin:
        nums = {}
        line_num = 0
        for line in fin:
            line_num += 1
            if len(line.strip()) == 0:
                continue
            matches = re.findall(r"(\d.\d+)", line)
            if len(matches) >= 1:
                nums[line_num] = list(map(float,matches))

    return nums


def compare(reference, tested):
    """
    Compare the two outputs according to a specific logic
    :return: True iff both input are equal
    """

    epsilon = 0.01
    for k,v in reference.items():
        tested_vals = tested[k]
        ok = all (map( lambda x: (abs(x[1] - x[0])) <= epsilon, zip(v,tested_vals)))
        if not ok:
            return False
    return True


def test():
    assert not check("test_4_bad", "golden_4")
    assert check("test_4", "golden_4")


def check(file_name_a, file_name_b):
    """
    check if the two input files are considered equal, for the purpose of this specific homework

    :param file_name_a: output of one run
    :param file_name_b: output of another run
    :return: True if the files are equal (the content might be not identical)
    """
    reference = parse_result_file(file_name_a)
    tested_output = parse_result_file(file_name_b)
    return compare(reference, tested_output)


if __name__ == "__main__":
    #    exit(test())
    from server_codes import ExitCode
    exit(0 if check(sys.argv[1], sys.argv[2]) else ExitCode.COMPARE_FAILED)
