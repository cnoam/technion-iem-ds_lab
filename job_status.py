
import random


class JobStatus():
    def __init__(self, id):
        """
        a job :
         status: (pending|running|failed|completed)
         run_time: None | float-seconds
         stdout: None | string
         stderr: None | string
         exit_code: None| int
        """
        self.status = 'pending'
        self.job_id = id
        self.run_time = None
        self.stdout = None
        self.stderr = None
        self.exit_code = None

    def job_completed(self, exit_code, run_time,stdout, stderr):
        self.status = 'completed' if exit_code == 0 else 'failed'
        self.run_time = run_time
        self.exit_code = exit_code
        self.stdout = stdout
        self.stderr = stderr

    def __str__(self):
        s = "{id} {stat} ".format(id = self.job_id, stat=self.status)
        if self.run_time is not None:
            s += "{:.3f} sec   exitcode {code}".format(self.run_time, code=self.exit_code)
        return s

    def as_html(self):
        if self.status in ( 'pending', 'running'):
            text = 'Job {} is currently {}'.format( self.job_id, self.status)
        elif self.status == 'failed':
            text = """<h1>Job {} failed with exit code {}</h1> <br>
                STDOUT:<br>
                {}<br><br>
                STDERR:<br>
                {}""".format(self.job_id, self.exit_code, self.stdout, self.stderr)
        elif self.status == 'completed':
            text = 'Job {} completed in {:.3f} seconds.'.format(self.job_id, self.run_time)
        else:
            raise ValueError('impossible state:'+ str(self.status) )
        return text


class JobStatusDB():
    """wrapper around simple dict, so I can replace with DB implementation if I wish"""
    def __init__(self):
        self.jobs = {}

    def add_job(self):
        """Create a new job object, give it ID, put it in the db
        :return the new JobStatus object
        """
        jobid = random.randint(1,1000)
        j = JobStatus(jobid)
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
