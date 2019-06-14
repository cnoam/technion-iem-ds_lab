
class Leaderboard():
    max_lines_to_display = 10

    def __init__(self, jobsDb):
        self.jobsDb = jobsDb

    def show(self):
        """
        Create an html page with the top 5 jobs, sorted by increasing runtime.
        :return: html page
        """
        s = "<h1>Leader board!</h1> <br><br>"

        jobs = self.jobsDb.jobs.values()
        completed = list(filter(lambda  job: job.status == 'completed', jobs))

        # sort by ascending run_time
        completed.sort(key=lambda x: x.run_time)

        s += "<h2>Showing top {} results</h2><br>".format(self.max_lines_to_display)
        for j in completed[0: self.max_lines_to_display]:
            s += "{}\t\t{:.3f} Sec <br>".format(j.filename, j.run_time)
        s += "<br>"
        return  s
