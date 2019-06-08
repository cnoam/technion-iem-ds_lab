
class Leaderboard():

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

        top_5 = completed[0:5]
        for j in top_5:
            s += "{}\t\t{:.3f} Sec <br>".format(j.filename, j.run_time)
        s += "<br>"
        return  s
