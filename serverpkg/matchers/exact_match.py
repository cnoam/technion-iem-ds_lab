"""
Compare two files supplied as command line args
return 0 if they are exactly identical,
return ExitCode.COMPARE_FAILED otherwise.
"""

import sys
#HACK. I need the codes, but dont waste time finding the right
# dir structure
# from serverpkg.server_codes import ExitCode


def check(file1, file2):
    """Compare file1 and file2.
    Ignore leading and trailing whitespaces of the file"""

    with open(file1,'r') as f1:
        test_output = f1.read()
    with open(file2) as f2:
        ref_output = f2.read()
    #p = subprocess.run(['diff', file1,file2], stdout=subprocess.PIPE)
    #print(p.stdout)
    return  test_output.strip() == ref_output.strip()
    #return  test_output == ref_output


if __name__ == "__main__":
    print("exact_match: comparing {} and {}".format(sys.argv[1], sys.argv[2]))
    good = check(sys.argv[1], sys.argv[2])
    exit(0 if good else 42)    #  ExitCode.COMPARE_FAILED)
