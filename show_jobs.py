# why not import the job_status_db from server.py?
# because when importing this module into server.py, the object
# is not yet created.
# also, try minimizing the sharing of global state

def show_jobs(job_status_db):
    """
    create a nice table with all the jobs past and present
    :return: html page
    """
    from Leaderboard import html_pre
    if job_status_db.lock.locked():
        return "Table is currently locked. Try again soon"
    s = html_pre
    s = html_pre + "<h1>Job table</h1> <br><br>"
    s += """<table>
            <tr>
            <th>Date</th>
            <th>Job ID</th>
            <th>Duration [sec]</th>
            <th>Status</th>
            </tr>"""
    for j in job_status_db.jobs.values():
        when = j.start_time.ctime() if j.start_time is not None else "?"
        s += "<tr> <td>{}</td> <td>{}</td> <td>{:.3f}</td> <td>{}</td> </tr>".format(when,j.id,j.run_time,j.status)
    s += "</table>"
    return s
