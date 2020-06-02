import difflib

def show_html_file_diff(string1, string2):
    """ create an html page with a table showing the textual diff between file1 and file2
    :param string1: list(string) content of file1
    :param string2: list(string) content of file2
    :return:  tuple( http response text, http response code)
    """
    assert isinstance(string1, list)
    assert isinstance(string2, list)
    return difflib.HtmlDiff().make_file(string1,string2,'reference','your output',context=False,numlines=3)



