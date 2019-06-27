
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
<body>"""


class Leaderboard():
    max_lines_to_display = 10

    def __init__(self, jobsDb):
        self.jobsDb = jobsDb

    def show(self):
        """
        Create an html page with the top 5 jobs, sorted by increasing runtime.
        :return: html page
        """
        s = html_pre + "<h1>Leader board!</h1> <br><br>"
        s += "<h2>Showing top {} results</h2><br>".format(self.max_lines_to_display)
        s += """<table>
        <tr>
        <th>Date</th>
        <th>Job name</th>
        <th>Duration [sec]</th>
        </tr>"""

        jobs = self.jobsDb.jobs.values()
        completed = list(filter(lambda  job: job.status == 'completed', jobs))

        # sort by ascending run_time
        completed.sort(key=lambda x: x.run_time)

        for j in completed[0: self.max_lines_to_display]:
            when = j.start_time.ctime() if j.start_time is not None else "?"
            s += "<tr> <td>{}</td> <td>{}</td> <td>{:.3f}</td> </tr>".format(when ,j.filename, j.run_time)
        s += "</table>"

        s += """<table>
        <tr>
        <th>Date</th>
        <th>Job name</th>
        <th>Duration [sec]</th>
        </tr>"""
        s += "<br><br><h3> these are marked as wrong answer, but might still be good<h3>"
        completed = list(filter(lambda  job: job.exit_code == 42, jobs))
        for j in completed:
            when = j.start_time.ctime() if j.start_time is not None else "?"
            s += "<tr> <td>{}</td> <td>{}</td> <td>{:.3f}</td> </tr>".format(when ,j.filename, j.run_time)
        s += "</table>"
        return s
