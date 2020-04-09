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
                   "<h3>You can sort by any column by clicking the header</h3><br>"
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
        when = j.start_time.ctime() if j.start_time is not None else "?"
        run_time = '{:.5}'.format(j.run_time) if j.run_time is not None else "N/A"
        # try to use a textual value if available for the exit code
        # this is probably the worst way to do it
        exit_code = j.exit_code
        if j.exit_code in ExitCode.values():
            exit_code = ExitCode(j.exit_code).name

        link_to_job = '<a href=check_job_status/%d' % j.job_id + '>%d'% j.job_id + '</a>'
        s += "<tr> <td>{}</td> <td>{}</td> <td>{}</td> <td>{}</td> <td>{}</td> <td>{}</td></tr>".\
            format(when,j.filename, link_to_job, run_time,j.status.name,exit_code)
    s += "</table>"
    return s
