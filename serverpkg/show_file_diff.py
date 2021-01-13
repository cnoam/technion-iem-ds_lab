import difflib
from http import HTTPStatus
from typing import List

def show_html_file_diff(string1, string2):
    """ create an html page with a table showing the textual diff between file1 and file2
    :param string1: list(string) content of file1
    :param string2: list(string) content of file2
    :return:  tuple( http response text, http response code)
    """
    assert isinstance(string1, list)
    assert isinstance(string2, list)
    return difflib.HtmlDiff(wrapcolumn=80).make_file(string2,string1,'your output','reference',context=True,numlines=3)


def show_html_diff(courseId, job, first):
    """returns an HTML page with visual diff between the reference file and the actual output.
    arguments are passed to the GET/POST:  first=94219/ref_hw_2_output&jobid=876'
    """

    def cleaned_stdout(strings) -> List[str]:
        """ Discard line before
        ==== compilation OK ====
         and after
        ==== finished the tested run ===="""
        start = 1
        end = -1
        for line in strings:
            if line == "==== compilation OK ====":
                break
            start += 1
        tmp = strings.copy()
        tmp.reverse()
        for line in tmp:
            if line == "==== finished the tested run ====":
                break
            end -= 1
        return strings[start:end]


    if first is None:
        # we only have the job ID.
        # get the reference file used
        pass
    else:
        from_file_name = "/data/{}/{}".format(courseId, first)
        try:
            with open(from_file_name) as ff:
                fromlines = ff.readlines()
        except FileNotFoundError:
            return "Source file %s not found" % from_file_name, HTTPStatus.NOT_FOUND
    return show_html_file_diff(string1=fromlines, string2=cleaned_stdout(job.stdout.splitlines()))
