# why not import the job_status_db from server.py?
# because when importing this module into server.py, the object
# is not yet created.
# also, try minimizing the sharing of global state
from .server_codes import ExitCode


def show_jobs(job_status_db):
    """
    create a nice table with all the jobs past and present.
    This is a View of the JobStatusDb ( as in MVC )
    :return: html page
    """
    from .leaderboard import html_pre
    # if job_status_db.lock.locked():
    #     return "Table is currently locked. Try again soon"
    s = html_pre + "<h1>Job table</h1> <br>" \
                   "<h3>You can sort by any column by clicking the header</h3><br>" \
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

    for job in items:
        when = job.start_time.ctime() if job.start_time is not None else "?"
        run_time = '{:.5}'.format(job.run_time) if job.run_time is not None else "N/A"
        # try to use a textual value if available for the exit code
        # this is probably the worst way to do it
        exit_code = job.exit_code
        exit_code_name = ""
        if job.exit_code in ExitCode.values():
            exit_code_name = ExitCode(job.exit_code).name

        link_to_job = '<a href=check_job_status/%d' % job.job_id + '>%d' % job.job_id + '</a>'
        # if the exit code is COMPARE_FAILED we want to have a link that will let the user see the diffs.
        # we need to get the ref file and the stdout.
        # something along the lines of host/94219/show_diff?first=ref_hw_2_output&second=876
        show_diff_button = True

        ref_name = f"/ref_hw_{job.exercise_name}_output"
        ################################
        if show_diff_button and exit_code == ExitCode.COMPARE_FAILED:
            page_link = f"{job.course_id}/show_diff?first={ref_name}&jobid={job.job_id}"
            prefix = '<form action={} method="post">'.format(page_link)
            postfix = '</form>'
            button_link = prefix + '<input type=submit value="compare">' + postfix
            s += "<tr> <td>{}</td> <td>{}</td> <td>{}</td> <td>{}</td> <td>{}</td> <td>{}</td></tr>". \
                format(when, job.filename, link_to_job, run_time, job.status.name, button_link)
        else:
            s += "<tr> <td>{}</td> <td>{}</td> <td>{}</td> <td>{}</td> <td>{}</td> <td>{}</td></tr>".\
                format(when,job.filename, link_to_job, run_time,job.status.name,exit_code_name)
    s += "</table>"
    return s
