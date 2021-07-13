# why not import the job_status_db from server.py?
# because when importing this module into server.py, the object
# is not yet created.
# also, try minimizing the sharing of global state
from .server_codes import ExitCode


def show_jobs(job_status_db, filter_func = None, filter_name= None):
    """
    create a nice table with all the jobs past and present.
    This is a View of the JobStatusDb ( as in MVC )

    :param job_status_db the in memory representation of the jobs table
    :filter_func optional function to filter which jobs to display. For example
       show only jobs whos known_course_id == 94210.
       If None, do not filter.
    :return: html page
    """
    from .leaderboard import html_pre
    x = str(filter_func)
    # if job_status_db.lock.locked():
    #     return "Table is currently locked. Try again soon"
    s = html_pre + "<h1>Job table</h1> <br>"
    if filter_func is not None:
        s += "<h2>for "+filter_name + "</h2>"
    s += "<h3>You can sort by any column by clicking the header</h3><br>" \
                   "Time is in UTC<br>"
    s += """<table class="sortable">
            <tr>
            <th>Date</th>
            <th>Job name</th>
            <th>Job ID</th>
            <th>Duration [sec]</th>
            <th>Status</th>
            <th>exit code</th>
            </tr>"""

    # sort the rows by descending date
    items = sorted(list(job_status_db.jobs().values()) ,key=lambda x: -x.start_time.timestamp())

    for j in items:
        if filter_func is None or filter_func(j):
            when = j.start_time.ctime() if j.start_time is not None else "?"
            run_time = '{:.5}'.format(j.run_time) if j.run_time is not None else "N/A"
            # try to use a textual value if available for the exit code
            # this is probably the worst way to do it
            exit_code = j.exit_code
            exit_code_name = ""
            if j.exit_code in ExitCode.values():
                exit_code_name = ExitCode(j.exit_code).name

            link_to_job = '<a href=check_job_status/%d' % j.job_id + '>%d' % j.job_id + '</a>'
            # if the exit code is COMPARE_FAILED we want to have a link that will let the user see the diffs.
            # we need to get the ref file and the stdout.
            # something along the lines of host/94219/show_diff?first=ref_hw_2_output&second=876
            show_diff_button = True
            course_id = j.course_id
            hw_number = j.exercise_name
            ref_name = "/ref_hw_{}_output".format(hw_number)
            if show_diff_button and exit_code == ExitCode.COMPARE_FAILED:
                page_link = "{course_id}/show_diff?first={first}&jobid={second}"\
                    .format(course_id=course_id,first=ref_name, second=j.job_id)
                prefix = '<form action={} method="post">'.format(page_link)
                postfix = '</form>'
                button_link = prefix + '<input type=submit value="compare">' + postfix
                s += "<tr> <td>{}</td> <td>{}</td> <td>{}</td> <td>{}</td> <td>{}</td> <td>{}</td></tr>". \
                    format(when, j.filename, link_to_job, run_time, j.status.name, button_link)
            else:
                s += "<tr> <td>{}</td> <td>{}</td> <td>{}</td> <td>{}</td> <td>{}</td> <td>{}</td></tr>".\
                    format(when,j.filename, link_to_job, run_time,j.status.name,exit_code_name)
    s += "</table>"
    return s
