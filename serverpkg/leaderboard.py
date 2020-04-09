from .server_codes import ExitCode

html_pre = """<!DOCTYPE html>
<html>
<head>
<style>
table {
  font-family: arial, sans-serif;
  border-collapse: collapse;
  width: 100%;
}

td, th {
  border: 1px solid #dddddd;
  text-align: left;
  padding: 8px;
}

tr:nth-child(even) {
  background-color: #dddddd;
}
</style>
</head>
<script src="/static/sorttable.js"></script
<body>"""


class Leaderboard():
    max_lines_to_display = 10

    def __init__(self, jobsDb):
        self.jobsDb = jobsDb

    def _prepare_best_jobs(self,ex_name):
        """
        :return: list of the lowest run time jobs, one for each job_name
        """
        jobs = self.jobsDb.jobs().values()
        completed = list(filter(lambda job: job.status == 'completed', jobs))

        # leave only jobs that do not have attribute 'exercise_number' or having it and value is ex_name
        completed = list(filter(lambda j: (not hasattr(j, 'exercise_name')) or str(j.exercise_name) == ex_name, completed))

        # sort by ascending run_time
        completed.sort(key=lambda x: x.run_time)
        return completed

    def show(self, ex_name):
        """
        Create an html page with the top max_lines_to_display jobs, sorted by increasing runtime.
        Users can submit multiple time so we need to keep the lowest value for each user,
         and count it as single entry.
        :return: html page
        """
        s = html_pre + "<h1>Leader board for exercise {}</h1> <br><br>".format(ex_name)
        s += "<h2>Showing top {} results</h2><br>".format(self.max_lines_to_display)
        s += """<table  class="sortable">
        <tr>
        <th>Date</th>
        <th>Job name</th>
        <th>Job ID</th>
        <th>Duration [sec]</th>
        </tr>"""

        completed = self._prepare_best_jobs(ex_name)

        for j in completed[0: self.max_lines_to_display]:
            when = j.start_time.ctime() if j.start_time is not None else "?"
            s += "<tr> <td>{}</td> <td>{}</td> <td>{}</td> <td>{:.3f}</td> </tr>".format(when ,j.filename, j.job_id, j.run_time)
        s += "</table>"

        # --- another table for the not so lucky
        s += """<table  class="sortable">
        <tr>
        <th>Date</th>
        <th>Job name</th>
        <th>Job ID</th>
        <th>Duration [sec]</th>
        </tr>"""
        s += "<br><br><h3> these are marked as wrong answer, but might still be good<h3>"
        completed = list(filter(lambda  job: job.exit_code == ExitCode.COMPARE_FAILED, self.jobsDb.jobs().values()))
        for j in completed:
            when = j.start_time.ctime() if j.start_time is not None else "?"
            runtime = j.run_time if j.run_time is not None else 0.0
            s += "<tr> <td>{}</td> <td>{}</td> <td>{}</td> <td>{:.3f}</td> </tr>".format(when ,j.filename, j.job_id, runtime)
        s += "</table>"
        return s
