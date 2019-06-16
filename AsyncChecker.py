import threading
import subprocess
import time
import re
from server import logger


def extract_run_time(string):
    """
    extract the runtime that we wrote as the last line in the stderr stream supplied in string
    :param string: the stderr stream. last line looks like: 0.5 user 1.6 system
    :return: run time in seconds <float>
    :raises In
    """
    matches = re.findall("run time: ([0-9.]+) user ([0-9.]+) system", string)
    if len(matches) != 1:
        raise ValueError("run times not found in \n" + string)
    return sum(map(float, matches[0]))


class AsyncChecker(threading.Thread):
    timeout_sec = 3000

    def __init__(self, new_job, package_under_test, reference_input, reference_output, completion_cb):
        super().__init__(name = "job "+ str(new_job.job_id))
        self.job_status = new_job
        self.package_under_test = package_under_test
        self.reference_input = reference_input
        self.reference_output = reference_output
        self.completion_cb = completion_cb

    def run(self):
        import os
        self.job_status.status='running' # todo use enums!
        completed_proc = None
        # WARNING: on Windows pltaform, the clock() measurement is "wallclock"
        # so sleep(2) will give 2 seconds instead of 0.0
        start_time = time.process_time()
        try:
            logger.info("ref files:  " + self.reference_input + "," + self.reference_output)
            #  https://medium.com/@mccode/understanding-how-uid-and-gid-work-in-docker-containers-c37a01d01cf
            comparator = '{}/tester_ex3.py'.format(os.getcwd())
            completed_proc = subprocess.run(['./checker.sh', self.package_under_test, self.reference_input,
                                             self.reference_output, comparator],
                                            check=False, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                                            timeout= self.timeout_sec)

            # try to extract the run time from the last line of stderr
            prog_run_time = extract_run_time(completed_proc.stderr.decode('utf-8'))
            self.job_status.job_completed(completed_proc.returncode,
                                      prog_run_time,
                                      stdout = completed_proc.stdout.decode('utf-8'),
                                      stderr=completed_proc.stderr.decode('utf-8')
                                      )

        # except subprocess.TimeoutExpired:
        #    message = "Your code ran for too long. timeout set to "+ str(timeout) + " seconds"
        except subprocess.CalledProcessError as ex:
            #message = 'Your code failed. Please check the reported output\n\n' + completed_proc.stderr.decode('utf-8')
            self.job_status.completed(-100,
                                      stdout=completed_proc.stdout.decode('utf-8'),
                                      stderr=completed_proc.stderr.decode('utf-8')
                                      )
        except Exception as ex:
            logger.error("This should never happen:" + str(ex))
            self.job_status.job_completed(exit_code=-200,run_time = 0, stdout = None, stderr = None)
        finally:
            if self.completion_cb is not None:
                self.completion_cb()
        logger.info("thread {} exiting".format(self.getName()))
