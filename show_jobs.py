# why not import the job_status_db from server.py?
# because when importing this module into server.py, the object
# is not yet created.
# also, try minimizing the sharing of global state
from server_codes import ExitCode

def show_jobs(job_status_db):
    """
    create a nice table with all the jobs past and present
    :return: html page
    """
    from Leaderboard import html_pre
    if job_status_db.lock.locked():
        return "Table is currently locked. Try again soon"
    s = html_pre + "<h1>Job table</h1> <br><br>"
    s += """<table>
            <tr>
            <th>Date</th>
            <th>Job name</th>
            <th>Job ID</th>
            <th>Duration [sec]</th>
            <th>Status</th>
            <th>exit code</th>
            </tr>"""

    # sort the rows by descending date
    items = sorted(list(job_status_db.jobs.values()) ,key=lambda x: -x.start_time.timestamp())
    for j in items:
        when = j.start_time.ctime() if j.start_time is not None else "?"
        run_time = '{:.5}'.format(j.run_time) if j.run_time is not None else "N/A"
        # try to use a textual value if available for the exit code
        # this is probably the worst way to do it
        exit_code = j.exit_code
        if j.exit_code in ExitCode.values():
            exit_code = ExitCode(j.exit_code).name
        s += "<tr> <td>{}</td> <td>{}</td> <td>{}</td> <td>{}</td> <td>{}</td> <td>{}</td></tr>".\
            format(when,j.filename,j.job_id, run_time,j.status,exit_code)
    s += "</table>"
    return s
