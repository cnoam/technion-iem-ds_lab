
import random
import re
import pickle
from threading import Lock


class JobStatus():
    """
       a job :
        status: (pending|running|failed|completed)
        run_time: None | float-seconds
        stdout: None | string
        stderr: None | string
        exit_code: None| int
       """

    def __init__(self, id, filename):
        """
        :param id:
        :param filename: <string> file name to check, in the format [optional prefix]nnnnnn_mmmmmm.tar.gz
        """
        self.status = 'pending'
        self.job_id = id
        self.run_time = None  # will hold the duration
        self.stdout = None
        self.stderr = None
        self.exit_code = None
        self.start_time = None  # will hold the wallclock time when started
        matches = re.findall(r"(\d+)_(\d+).", filename)
        if len(matches)==0 :
            self.filename = filename
        else:
            self.filename = "_".join(matches[0]) # this is roughly the file name provided to checker.sh (the unit under test)
        assert (len(self.filename) > 0)

    def _job_completed(self, exit_code, run_time,stdout, stderr):
        self.status = 'completed' if exit_code == 0 else 'failed'
        self.run_time = run_time
        self.exit_code = exit_code
        self.stdout = stdout
        self.stderr = stderr

    def __str__(self):
        s = "{id} {stat} . \t".format(id = self.job_id, stat=self.status)
        if self.run_time is not None:
            s += "runtime={:.3f} sec.".format(self.run_time)
        if self.exit_code is not None:
            s += "{code}".format(code=self.exit_code)
        return s

    def as_html(self):
        import server
        if self.status in ( 'pending', 'running'):
            text = 'Job {} is currently {}'.format( self.job_id, self.status)
        elif self.status == 'failed':
            text = """<h1>Job {} failed with exit code {}</h1> <br>
                STDOUT:<br>
                {}<br><br>
                STDERR:<br>
                {}""".format(self.job_id, self.exit_code,
                server.wrap_html_source(self.stdout),
                server.wrap_html_source(self.stderr))
        elif self.status == 'completed':
            text = 'Job {} completed in {:.3f} seconds.'.format(self.job_id, self.run_time)
        else:
            raise ValueError('impossible state:'+ str(self.status) )
        return text


class JobStatusDB():
    """wrapper around simple dict,
     so I can replace with DB implementation if I wish"""

    # keep the pickle file in a place that will persist!
    # in Docker, every container restart, the local filesystem is cleaned
    # so '/logs' is mounted on the host's file system
    pickle_file_name = '/logs/job_status.pickle'

    def __init__(self):
        self.jobs = {}
        self.lock = Lock()
        # load current values from pickle
        try:
            with  open(self.pickle_file_name, "rb") as f:
                self.jobs = pickle.load(f)
        except FileNotFoundError as ex:
            pass

    def add_job(self, package_file_name):
        """Create a new job object, give it ID, put it in the db
        :return the new JobStatus object
        """
        jobid = random.randint(1,1000)
        j = JobStatus(jobid, package_file_name)
        self.jobs[jobid] = j
        return j

    def get_job_stat(self, job_id):
        return (self.jobs[job_id]).as_html()

    def num_running_jobs(self):
        count = 0
        for jobid, jobstat in self.jobs.items():
            if jobstat.status == 'running':
                count += 1
        return count

    def job_completed(self, job,  exit_code, run_time,stdout, stderr):
        # forward to the job, and then update the "disk database"
        with self.lock:  # verify multi thread access will not corrupt the pickle
            job._job_completed(exit_code, run_time,stdout, stderr)
            #with open(self.pickle_file_name, "wb") as f:
            #    pickle.dump(self.jobs, f)

    def __str__(self):
        s = "LOCKED " if self.lock.locked() else ""
        for j in self.jobs.values():
            s += ", " + str(j)
        return s


if __name__ == "__main__":
    db = JobStatusDB()
    print("jobs: " + str(db))
    if True or len(db.jobs) == 0 :
        job1 = db.add_job("one")
        job2 = db.add_job("two")
        db.job_completed(job1,0,0.9,"nothing","  no errors")
        db.job_completed(job2, 2, 1.4, "nothing", "errors")
