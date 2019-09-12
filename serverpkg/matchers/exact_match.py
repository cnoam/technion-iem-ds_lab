import sys
from serverpkg.server_codes import ExitCode


def check(file1, file2):
    with open(file1,'r') as f1:
        test_output = f1.read()
    with open(file2) as f2:
        ref_output = f2.read()
    return  test_output == ref_output


if __name__ == "__main__":
    print("exact_match: comparing {} and {}".format(sys.argv[1], sys.argv[2]))
    good = check(sys.argv[1], sys.argv[2])
    exit(0 if good else ExitCode.COMPARE_FAILED)
