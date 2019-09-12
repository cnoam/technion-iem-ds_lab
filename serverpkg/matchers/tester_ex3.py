"""
check_ex3

Check if two text files are considered equal for course 94201, 2019-05 homework ex 3

>>> from tester_ex3 import check
>>> check("50_output.txt", "50_output_permuted.txt")
True
"""

import re
import sys
from serverpkg.server_codes import ExitCode
from frozendict import frozendict


class RegexError(BaseException):
    pass


class ParseError(BaseException):
    pass

regex = r"^Cluster (\d+):\s*\(([\d+,\s*]+)\)\s*,?.*=\s*(\w*),.* ([\d.]+)"

def parse_cluster(string):
    """
    parse a string of the format
    Cluster 6: (6,11,44,40,43,17,18,32,24,36,21), dominant label = KIRC, purity = 0.876
    and put it in a data structure
    NOTE: the tuple is ordered collection and we preserve the original order.
    :param string: one line with the above syntax
    :return: {"id": "6", "tuple": tuple<int> , "dominant": "KIRK", "purity": "0.876" }
    """
    prog = re.compile(regex)
    result = prog.findall(string)
    if len(result) != 1:  # must have exactly one match
        raise RegexError("Failed to match regex. line=" + string)

    result = result[0]

    # convert "6,11,44,40" to (6,11,40,44)
    t1 = result[1].split(",")
    t2 = tuple(map(int, t1))
    return {"id": result[0], "tuple": t2, "dominant": result[2], "purity": result[3]}


def parse_result_file(filename):
    with open(filename) as fin:
        root = {}
        # for line in fin:
        for link in range(3):
            # read the linkage type
            linkage = fin.readline().strip()
            # now loop on the (5) clusters, reading each of them
            x = []
            for i in range(5):  # or read until empty line
                line = fin.readline()
                x.append(parse_cluster(line))
            root[linkage] = x
            # eat optional empty line
            where = fin.tell()
            line = fin.readline()
            if len(line.strip()) > 0:
                fin.seek(where)  #  undo the read of the non empty line
    return root


def compare(reference, tested):
    """
    Compare the two outputs according to a specific logic
    :param reference: dict< "linkage type" : dict< int : tuple<int> > >
    :param tested: ditto
    :return: True iff both input are equal
    """

    def canoicalize(v):
        """
        :param v: the whole data struct containing the result for a linkage type
        :return: the data, in canonical format.
        """
        # sort the tuples for each sub dict

        canon = {}
        for link_name, clusters in v.items():
            clusters_set = set()
            canon[link_name] = clusters_set
            # the clusters is list<dict> . We need to somehow get canoical ordering of the list to enable comparison
            for cluster in clusters:
                cluster["tuple"] = tuple(sorted(cluster["tuple"]))

                # the cluster ID "should have been" part of the solution, but I see that for some students
                # the cluster content is correct, but the ID is different.
                # so set the ID to the lowest (first) value in the tuple
                cluster['id'] = cluster['tuple'][0]
                cluster = frozendict(cluster)
                clusters_set.add(cluster)
        return canon

    return canoicalize(reference) == canoicalize(tested)


def test():
    assert not check("50_output.txt", "50_output_different.txt")
    assert check("50_output.txt", "50_output_permuted.txt")


def check(file_name_a, file_name_b):
    """
    check if the two input files are considered equal, for the purpose of this specific homework

    :param file_name_a: output of one run
    :param file_name_b: output of another run
    :return: 0 if the files are equal (the content might be not identical)
    """
    reference = parse_result_file(file_name_a)
    tested_output = parse_result_file(file_name_b)
    return  0 if compare(reference, tested_output) else ExitCode.COMPARE_FAILED

def _match(string):
    prog = re.compile(regex)
    result = prog.findall(string)
    return len(result) == 1

if __name__ == "__main__":
    assert _match('Cluster 2: (2) dominant label = PRAD, purity = 1')
    assert _match('Cluster 22: (2) dominant label = PRAD, purity = 1')
    assert _match('Cluster 2: (2 , 33) dominant label = PRAD, purity = 1')
    assert _match('Cluster 2: (2) dominant label = PRAD, purity = 0.9887')

    #  exit(test())
    print("ex3: comparing {} and {}".format(sys.argv[1], sys.argv[2]))
    good = check(sys.argv[1], sys.argv[2])
    exit(good)
