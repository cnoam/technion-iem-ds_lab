
import random
import re
import pickle
from threading import Lock
import utils
from .logger_init import init_logger
#from serverpkg.server import wrap_html_source
logger = init_logger('job_status')

class JobStatus():
    """
       a job :
        status: (pending|running|failed|completed)
        run_time: None | float-seconds
        stdout: None | string
        stderr: None | string
        exit_code: None| int
       """

    def __init__(self, job_id,exercise_name, filename):
        """
        :param job_id: job ID (unique value)
        :param filename: <string> file name to check, in the format [optional prefix]nnnnnn_mmmmmm.tar.gz
        """
        self.status = 'pending'
        self.job_id = job_id
        self.run_time = None  # will hold the duration
        self.stdout = None
        self.stderr = None
        self.exit_code = None
        self.start_time = None  # will hold the wallclock time when started
        self.comparator_file_name = None
        self.executor_file_name = None
        self.exercise_name = exercise_name # used to identify for which exercise/lab number this job is related.

        matches = re.findall(r"(\d+)_(\d+).", filename)
        if len(matches)==0 :
            self.filename = filename
        else:
            self.filename = "_".join(matches[0]) # this is roughly the file name provided to checker.sh (the unit under test)
        assert (len(self.filename) > 0)

    def set_handlers(self,comparator_file_name, executor_file_name):
        self.comparator_file_name = comparator_file_name
        self.executor_file_name = executor_file_name


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
        import serverpkg
        if self.status in ( 'pending', 'running'):
            text = 'Job {} is currently {}'.format( self.job_id, self.status)
        elif self.status == 'failed':
            text = """<h1>Job {} failed with exit code {}</h1> <br>
                STDOUT:<br>
                {}<br><br>
                STDERR:<br>
                {}""".format(self.job_id, self.exit_code,
                             utils.wrap_html_source(self.stdout),
                             utils.wrap_html_source(self.stderr))
        elif self.status == 'completed':
            if self.run_time is None:  # soft fail if the internal state is not perfect
                self.run_time = 0.0
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
    pickle_file_name = '/logs/job_status.pickle'  # TODO: move to a better location in the file system
    
    def __init__(self):
        self.jobs = {}
        self.lock = Lock()
        # load current values from pickle
        try:
            with  open(self.pickle_file_name, "rb") as f:
                try:
                    self.jobs = pickle.load(f)
                except ModuleNotFoundError as ex:
                    logger.error("Failed reading pickle", ex)
        except FileNotFoundError as ex:
            logger.warning("pickle file not found")

    def add_job(self, ex_type_name, package_file_name):
        """Create a new job object, give it ID, put it in the db
        :return the new JobStatus object
        """
        assert isinstance(ex_type_name, tuple)
        jobid = random.randint(1,10000)
        with self.lock:
            j = JobStatus(jobid, ex_type_name[1], package_file_name)
        self.jobs[jobid] = j
        return j

    def get_job_stat(self, job_id):
        with self.lock:
            stat =  (self.jobs[job_id]).as_html()
        return stat

    def num_running_jobs(self):
        count = 0
        with self.lock:  #   RuntimeError: dictionary changed size during iteration
            for jobid, jobstat in self.jobs.items():
                if jobstat.status == 'running':
                    count += 1
        return count

    def job_completed(self, job,  exit_code, run_time,stdout, stderr):
        # forward to the job, and then update the "disk database"
        with self.lock:  # verify multi thread access will not corrupt the pickle
            job._job_completed(exit_code, run_time,stdout, stderr)
            try:
                with open(self.pickle_file_name, "wb") as f:
                    pickle.dump(self.jobs, f)
            except:
                logger.exception("Could not write pickle file")

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
