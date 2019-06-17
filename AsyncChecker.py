import threading
import subprocess
import re

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
    timeout_sec = 3000 # TODO: check code behavior when timeout

    def __init__(self, job_db,  new_job, package_under_test, reference_input, reference_output, completion_cb):
        super().__init__(name = "job "+ str(new_job.job_id))
        self.job_status = new_job
        self.package_under_test = package_under_test
        self.reference_input = reference_input
        self.reference_output = reference_output
        self.completion_cb = completion_cb
        self.job_db = job_db


    def run(self):
        import os
        self.job_status.status='running' # todo use enums!
        completed_proc = None

        try:
            logger.info("ref files:  " + self.reference_input + "," + self.reference_output)
            #  https://medium.com/@mccode/understanding-how-uid-and-gid-work-in-docker-containers-c37a01d01cf
            comparator = '{}/tester_ex3.py'.format(os.getcwd())
            prog_run_time = None
            completed_proc = subprocess.run(['./checker.sh', self.package_under_test, self.reference_input, self.reference_output, comparator],
                                            check=False, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                                            timeout= self.timeout_sec)

            logger.info("job {} completed with exit code {}".format(self.job_status.job_id, completed_proc.returncode))
            if completed_proc.returncode != 0:
                logger.info("STDERR:\n" + completed_proc.stderr.decode('utf-8'))
            else:
                # try to extract the run time from the last line of stderr
                try:
                    prog_run_time = _extract_run_time(completed_proc.stderr.decode('utf-8'))
                except ValueError:
                    logger.warning("Execution time not found for this run. Ignoring it")
            self.job_db.job_completed(self.job_status,
                                      exit_code=completed_proc.returncode,
                                      run_time=prog_run_time,
                                      stdout=completed_proc.stdout.decode('utf-8'),
                                      stderr=completed_proc.stderr.decode('utf-8')
                                      )

        # except subprocess.TimeoutExpired:
        #    message = "Your code ran for too long. timeout set to "+ str(timeout) + " seconds"
        except subprocess.CalledProcessError as ex:
            self.job_db.job_completed(self.job_status,
                                      exit_code=-100,
                                      run_time=None,
                                      stdout=completed_proc.stdout.decode('utf-8'),
                                      stderr=completed_proc.stderr.decode('utf-8')
                                      )
        # uncomment the next lines only for special debug.
        # if there is a bug, the code here should crash, and the web server will return 500 as it should!
        #
        # except Exception as ex:
        #     logger.error("This should never happen:" + str(ex))
        #     self.job_status.job_completed(exit_code=-200,run_time = 0, stdout = None, stderr = None)
        finally:
            if self.completion_cb is not None:
                self.completion_cb()
        logger.info("thread {} exiting".format(self.getName()))
