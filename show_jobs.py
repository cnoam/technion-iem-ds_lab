# why not import the job_status_db from server.py?
# because when importing this module into server.py, the object
# is not yet created.
# also, try minimizing the sharing of global state

def show_jobs(job_status_db):
    """
    create a nice table with all the jobs past and present
    :return: html page
    """
    s = "<h1>Jobs (runing and completed)</h1>"
    for job in job_status_db.jobs.values():
        s += str(job) + '<br>'
    s+='<br>'
    return s