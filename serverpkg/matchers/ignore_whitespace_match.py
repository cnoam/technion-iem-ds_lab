"""
Compare two files supplied as command line args
return 0 if  after removing ALL WHITE SPACES they are exactly identical,
return ExitCode.COMPARE_FAILED otherwise.
"""
import subprocess
import sys
#HACK. I need the codes, but dont waste time finding the right
# dir structure
# from serverpkg.server_codes import ExitCode

def remove_spaces( aString):
    import re
    r = re.compile(r"\s+", re.MULTILINE)
    return r.sub('',aString)

def check(file1, file2):
    """Compare file1 and file2.
    Ignore leading and trailing whitespaces of the file"""

    with open(file1) as f1:
        test_output = remove_spaces(f1.read())
    with open(file2) as f2:
        ref_output = remove_spaces(f2.read())

    #print("test:\n" + test_output)
    #print("\n\nREF:\n", ref_output)
    #p = subprocess.run(['diff','-awbZEy', '--suppress-common-lines', file1,file2], stdout=subprocess.PIPE)
    #print(p.stdout.decode())
    return  test_output == ref_output


if __name__ == "__main__":
    print("ignore whitespaces: comparing {} and {}".format(sys.argv[1], sys.argv[2]))
    good = check(sys.argv[1], sys.argv[2])
    exit(0 if good else 42)    #  ExitCode.COMPARE_FAILED)
