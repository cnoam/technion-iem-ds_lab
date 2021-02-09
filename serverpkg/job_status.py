
import datetime
import re
import sqlite3
from enum import Enum

import utils
from .logger_init import init_logger

logger = init_logger('job_status')


class Job():
    """
       a job  represents a task to execute the uploaded code.
       If using a relational database, Job is the object related to a row in the jobs table

        status: (pending|running|failed|completed)
        run_time: None | float-seconds
        stdout: None | string
        stderr: None | string
        exit_code: None| int
       """

    class Status(Enum):
        pending =1
        running =2
        failed  =3
        completed =4

    @staticmethod
    def from_tuple( value):
        j = Job(0, 'dummy', 'dummy')
        (j.job_id ,
         j.status,
         j.run_time ,
         j.stdout ,
         j.stderr,
         j.exit_code,
         j.start_time ,
         j.comparator_file_name ,
         j.executor_file_name,
         j.exercise_name,
         j.filename) = value

        # convert to status:Job.Status
        j.status = Job.Status[j.status]
        if j.start_time is None:
            logger.warning("partial job record: " + str(j))
            j.start_time = datetime.datetime(1948,1,1)
        else:
            j.start_time = datetime.datetime.strptime(j.start_time,"%Y-%m-%d %H:%M:%S.%f")
        return j

    @staticmethod
    def JobSqlSchema():
        """return the SQL string to generate a table with the attributes"""
        return """job_id     integer PRIMARY KEY,
                  status     text NOT NULL,
                  run_time   real,
                  stdout     text,
                  stderr      text,
                  exit_code  integer,
                  start_time DATETIME,
                  comparator_file_name text,
                  executor_file_name text,
                  exercise_name text,
                  filename   text
                  """

    def to_tuple(self):
        return (self.job_id, self.status.name, self.run_time, self.stdout, self.stderr, self.exit_code, self.start_time,
                self.comparator_file_name, self.executor_file_name, self.exercise_name, self.filename)

    def __init__(self, exercise_name, filename,job_id=None):
        """
        :param job_id: job ID (unique value)
        :param filename: <string> file name to check, in the format [optional prefix]nnnnnn_mmmmmm.tar.gz
        """
        self.status = Job.Status.pending
        self.job_id = job_id
        self.run_time = None  # will hold the duration
        self.stdout = None
        self.stderr = None
        self.exit_code = None
        self.start_time = None  # will hold the wallclock time when started
        self.comparator_file_name = None
        self.executor_file_name = None
        self.exercise_name = str(exercise_name) # used to identify for which exercise/lab number this job is related.

        matches = re.findall(r"(\d{8,9})_(\d{8,9})", filename)
        if len(matches)==0 :
            self.filename = filename
        else:
            self.filename = "_".join(matches[0]) # this is roughly the file name provided to checker.sh (the unit under test)
        assert (len(self.filename) > 0)

    def set_handlers(self,comparator_file_name, executor_file_name):
        self.comparator_file_name = comparator_file_name
        self.executor_file_name = executor_file_name


    # def _job_completed(self, exit_code, run_time,stdout, stderr):
    #     self.status = 'completed' if exit_code == 0 else 'failed'
    #     self.run_time = run_time
    #     self.exit_code = exit_code
    #     self.stdout = stdout
    #     self.stderr = stderr

    def __str__(self):
        s = "{id} {stat} . \t".format(id = self.job_id, stat=self.status)
        if self.run_time is not None:
            s += "runtime={:.3f} sec.".format(self.run_time)
        if self.exit_code is not None:
            s += " exitcode={code}".format(code=self.exit_code)
        return s

    def __eq__(self, other):
        return  self.to_tuple() == other.to_tuple()

    def __ne__(self, other):
        return not __eq__(other)

    def as_html(self):
        if self.status in (Job.Status.pending, Job.Status.running):
            text = 'Job {} is currently {}'.format( self.job_id, self.status.name)
        elif self.status == Job.Status.failed:
            text = """<h1>Job {} failed with exit code {}</h1> <br>
                STDOUT:<br>
                {}<br><br>
                STDERR:<br>
                {}""".format(self.job_id, self.exit_code,
                             utils.wrap_html_source(self.stdout),
                             utils.wrap_html_source(self.stderr))
        elif self.status == Job.Status.completed:
            if self.run_time is None:  # soft fail if the internal state is not perfect
                self.run_time = 0.0
            text = 'Job {} completed in {:.3f} seconds.'.format(self.job_id, self.run_time)
            text += """STDOUT:<br>
                {}<br><br>
                STDERR:<br>
                {}""".format(utils.wrap_html_source(self.stdout),
                             utils.wrap_html_source(self.stderr))
        else:
            raise ValueError('impossible state:'+ str(self.status.name) )
        return text


import multiprocessing
db_creation_sync_lock = multiprocessing.Lock() # TODO don't we need a name?


class JobStatusDB():
    """wrapper around simple persistent dict,
     Internally use sqlite3

     When using gunicorn as the frontend webserver, with 2 or more workers, each worker is a process.
     This improves the server's response dramatically but now need to handle multi process access to the data.
     Using sqlite takes care of this inherrently.

     Use a new Connection object in each function to avoid the need to sync multi thread access myself
     see https://stackoverflow.com/questions/48218065/programmingerror-sqlite-objects-created-in-a-thread-can-only-be-used-in-that-sa/51147168
     """

    # keep the db file in a place that will persist!
    # in Docker, every container restart, the local filesystem is cleaned
    # so '/db' is mounted on the host's file system
    # @param: db_dir_name: full path to the database directory. Can be non existent
    def __init__(self, db_dir_name : str):
        import os
        self.db_dir_name = db_dir_name
        self.db_file_name = os.path.join(db_dir_name, "jobs.db")

    def _create_tables(self):
        """Create the needed SQL table if they are not already created.
        :Note: must be multiprocess safe since this code can be called concurrently
        from (e.g) 3 processes"""
        #db_creation_sync_lock.lock() #TODO: finish coding the multi process safe creation or make it redundant

        # make sure the db dir is created
        import os
        logger.info("opening file %s" % self.db_file_name)
        try:
            os.mkdir(self.db_dir_name)
        except FileExistsError:
            pass
        except PermissionError:
            logger.error("Permission denied when trying to create the DB directory")
            raise
        try:
            with sqlite3.connect(self.db_file_name) as conn:
                conn.execute("CREATE TABLE IF NOT EXISTS jobs ( {} ); ".format(Job.JobSqlSchema()))
        except sqlite3.OperationalError:
            print("is the file system writable?\n")
            raise
        #db_creation_sync_lock.release()

    def _drop_tables(self):
        with sqlite3.connect(self.db_file_name) as conn:
            conn.execute("DROP TABLE jobs; ")

    def insert_to_db(self, job):
        """
        add a new record to the DB
        :postcond: update the job.job_id if it was None
        :param job :type Job
        :return: job id : int
        """
        with sqlite3.connect(self.db_file_name) as conn:
            cur =conn.execute("INSERT INTO jobs VALUES (?,?,?,?,?,?,?,?,?,?,?)", job.to_tuple())
            id = cur.lastrowid
            job.job_id = id
        return job.job_id


    def select_a_job(self, job_id) -> Job :
        """
        select a job from the db
        :param job_id:
        :return: a Job object or None if not found
        :raises Exception if there are more than one records with this job_id ???
        """
        with sqlite3.connect(self.db_file_name) as conn:
            cur = conn.execute("SELECT * FROM jobs WHERE job_id=?",(job_id,) )
            rows = cur.fetchall()
        if len(rows) > 1:
            raise Exception("Too many job records")
        if len(rows) == 0:
            return None
        return Job.from_tuple(rows[0])


    def num_jobs(self):
        """
        :return: number of Job records
        """
        with sqlite3.connect(self.db_file_name) as conn:
            count_list = conn.execute("SELECT COUNT(*) FROM jobs;").fetchall()
        return count_list[0][0]

    def add_job(self, ex_type_name:tuple, package_file_name) -> Job:
        """Create a new job object, give it ID, put it in the db
        :return the new Job object
        """
        assert isinstance(ex_type_name, tuple)
        a_job = Job(ex_type_name[1], filename=package_file_name)
        self.insert_to_db(a_job)
        return a_job

    def get_job_stat(self, job_id):
        """Query the database"""
        job = self.select_a_job(job_id)
        if job is None:
            raise KeyError("job id {} not found".format(job_id))
        return job.as_html()


    def num_running_jobs(self):
        with sqlite3.connect(self.db_file_name) as conn:
            rows = conn.execute("SELECT COUNT(*) FROM jobs WHERE status=?;", ( Job.Status.running.name,)).fetchone()
        return rows[0]

    def delete_jobs(self, job_status):
        """
        delete from the DB records matching the job status.
        :param job_status:
        :return: how many records were deleted
        """
        with sqlite3.connect(self.db_file_name) as conn:
            rows = conn.execute("DELETE FROM jobs WHERE status=?;", (job_status.name,)).fetchall()
            if len(rows) > 0:
                logger.info("deleted %d rows with status %s" % (len(rows), job_status.name ))
        return len(rows)

    # def set_job_status(self, job_id:int, new_status:Job.Status):
    #     """udpate the relevant entry in the DB.
    #     WARNING: python objects of Job are NOT updated. only the DB"""
    #     with sqlite3.connect(self.db_file_name) as conn:
    #         conn.execute("UPDATE jobs SET status=?WHERE job_id=?", (new_status.name, job_id))

    def mark_job_running(self, job_id:int, start_time:datetime.datetime) -> None:
        with sqlite3.connect(self.db_file_name) as conn:
            conn.execute("UPDATE jobs SET status=?, start_time=? WHERE job_id=?", (Job.Status.running.name, start_time, job_id))

    def mark_job_completed(self, job_id :int, exit_code, run_time,stdout, stderr) -> None:
        assert isinstance(job_id,int)
        with sqlite3.connect(self.db_file_name) as conn:
            conn.execute("UPDATE jobs \
            SET \
            status=?  ,\
            exit_code=? ,\
            run_time=? ,\
            stdout=? ,\
            stderr=? \
            WHERE job_id=?", ('completed' if exit_code == 0 else 'failed',
                              exit_code, run_time, stdout, stderr, job_id))

    def jobs(self):
        """
        create a dict with all the Job object.
        A better implementation is to make it a generator and yield a single item each call,
        but in that case, how do we know what is the status of the database?
        :return: dict(job_id:int -> Job)
        """
        d = dict()
        with sqlite3.connect(self.db_file_name) as conn:
            rows = conn.execute("SELECT * from jobs").fetchall()
            for row in rows:
                job = Job.from_tuple(row)
                d[job.job_id] = job
        return d

    def __str__(self):
        """ create a string containing a line for each row ( a Job )"""
        s = ""
        with sqlite3.connect(self.db_file_name) as conn:
            rows = conn.execute("SELECT * from jobs").fetchall()
        for row in rows:
            s += str(Job.from_tuple(row)) + ", "
        return s


if __name__ == "__main__":
    db = JobStatusDB()
    db._create_connection(':memory:')
    db._create_tables()
    print("jobs: " + str(db))
    job1 = db.add_job(("hw",1),"uut1")
    job2 = db.add_job(("two",2),"uut2")
    print("jobs2: " + str(db))
    db.mark_job_completed(job1.job_id,0,0.9,"nothing","  no errors")
    #db.mark_job_completed(job2.job_id, 2, 1.4, "nothing", "errors")
    print("jobs after completion: " + str(db))
