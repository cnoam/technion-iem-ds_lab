from .server_codes import ExitCode
from .job_status import Job
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
        :return: list of the highest score jobs, one for each job_name
        """
        jobs = self.jobsDb.jobs().values()
        completed = list(filter(lambda job: job.status == Job.Status.completed, jobs))

        # sort by descending score
        completed.sort(key=lambda x: x.score, reverse=True)
        return completed

    def show(self, course_id, ex_name):
        """
        Create an html page with the top max_lines_to_display jobs, sorted by increasing score/runtime.
        Users can submit multiple time so we need to keep the lowest value for each user,
         and count it as single entry.
        :return: html page
        """
        s = html_pre + "<h1>Leaderboard for exercise {}/{}</h1> <br><br>".format(course_id,ex_name)
        s += "<h2>Showing top {} results</h2><br>".format(self.max_lines_to_display)
        s += """<table  class="sortable">
        <tr>
        <th>Date</th>
        <th>Job name</th>
        <th>Score</th>
        <th>Job ID</th>
        <th>Duration [sec]</th>
        </tr>"""

        completed = self._prepare_best_jobs(ex_name)

        for j in completed[0: self.max_lines_to_display]:
            when = j.start_time.ctime() if j.start_time is not None else "?"
            s += "<tr> <td>{}</td> <td>{}</td> <td>{}</td> <td>{}</td> <td>{:.3f}</td> </tr>".format(when ,j.filename, j.score, j.job_id, j.run_time)
        s += "</table>"

        return s
