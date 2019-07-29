import threading
import subprocess
import re
from server_codes import ExitCode
from logger_init import init_logger
logger = init_logger('asyncChecker')

def _extract_run_time(string):
    """
    extract the runtime that we wrote as the last line in the stderr stream supplied in string
    :param string: the stderr stream. last line looks like: 0.5 user 1.6 system
    :return: run time in seconds <float>
    :raises ValueError
    """
    matches = re.findall("run time: ([0-9.]+) user ([0-9.]+) system", string)
    if len(matches) != 1:
        raise ValueError("run times not found in \n" + string)
    return sum(map(float, matches[0]))


class AsyncChecker(threading.Thread):

    def __init__(self, job_db,  new_job, package_under_test, reference_input, reference_output, completion_cb, timeout_sec = 300):
        super().__init__(name = "job "+ str(new_job.job_id))
        self.job_status = new_job
        self.package_under_test = package_under_test
        self.reference_input = reference_input
        self.reference_output = reference_output
        self.completion_cb = completion_cb
        self.job_db = job_db
        self.timeout_sec = timeout_sec

    def run(self):
        import datetime
        import workshop_db
        self.job_status.status='running' # todo use enums!
        self.job_status.start_time = datetime.datetime.today()
        completed_proc = None

        exit_code = None
        run_time = None
        try:
            import  os
            logger.info("ref files:  " + self.reference_input + "," + self.reference_output)
            #  https://medium.com/@mccode/understanding-how-uid-and-gid-work-in-docker-containers-c37a01d01cf
            comparator = self.job_status.comparator_file_name
            assert (comparator is not None)
            executor = self.job_status.executor_file_name
            assert (executor is not None)
            prog_run_time = None
            logger.debug("executor={}, UUT={}, comparator={}".format( executor,self.package_under_test, comparator))

            # run the subprocess ( a shell that runs the tested process) under a timeout constraint.
            # there is a known problem (https://bugs.python.org/issue26534) using timeout in such scenario,
            # so in addition to the python's timeout, I pass the value in an Environment var to the shell
            # and use timeout command there.
            # the timeout value in the shell is shorter than the python's so it will expire first and indicate a problem
            # in the tested executable and not the tester script.
            os.environ.putenv('UUT_TIMEOUT', str(self.timeout_sec - 1))
            completed_proc = subprocess.run([executor, self.package_under_test, self.reference_input,
                                             self.reference_output, comparator],
                                            check=False, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                                            timeout= self.timeout_sec)
            logger.info("job {} completed with exit code {}".format(self.job_status.job_id, completed_proc.returncode))
            if completed_proc.returncode != 0:
                logger.info("STDERR:\n" + completed_proc.stderr.decode('utf-8'))

            # try to extract the run time from the last line of stderr
            try: prog_run_time = _extract_run_time(completed_proc.stderr.decode('utf-8'))
            except ValueError:
                logger.warning("Execution time not found for this run. Ignoring it")
            exit_code=completed_proc.returncode
            run_time=prog_run_time

        except OSError as ex:
            logger.error("Internal error: " + str(ex))
            exit_code = ExitCode.SERVER_ERROR
            run_time = None
        except subprocess.TimeoutExpired:
            logger.warning("job timed out. timeout set to "+ str(self.timeout_sec) + " seconds")
            exit_code = ExitCode.TIMEOUT
            run_time = None
        except subprocess.CalledProcessError:
            exit_code= ExitCode.PROCESS_ERROR
            run_time=None
        finally:
            out = completed_proc.stdout.decode('utf-8') if completed_proc is not None else None
            err = completed_proc.stderr.decode('utf-8') if completed_proc is not None else None
            score = self._extract_score(out)
            self.job_db.job_completed(self.job_status,
                                      exit_code= exit_code,
                                      run_time=run_time,
                                      stdout=out,
                                      stderr=err,
                                      score=score
                                      )

            # HACK for the workshop:
            if score is not None:
                import os
                name = os.path.basename(self.package_under_test)
                workshop_db.WorkshopDb().add_score(name,score)
            if self.completion_cb is not None:
                self.completion_cb()
        logger.info("thread {} exiting".format(self.getName()))

    def _extract_score(self, stdout):
        """try to find a score in the format F1 score = 0.987.
        To avoid user's malicious printing, use the bottom most print
        F1 score: 0.987
        :return: the score in float, or None if can't find it
        """
        import re
        last_line = stdout[stdout.rfind('F1') : ]
        match = re.findall(r'F1 score:\s*([.\d]+)', last_line)
        return float(match[0]) if len(match) == 1 else None  #  expect a single match

if __name__ == "__main__":

    # check that the timeout is applied to the process spawned by the shell which is spawned by the python process.
    from job_status import JobStatus, JobStatusDB
    db = JobStatusDB()
    uut = './loop'
    job = db.add_job(uut)
    job.set_handlers("foo_comparator", "./checker_sh.sh")
    a = AsyncChecker(db, job, uut,"ONE","TWO", None)
    a.start()
