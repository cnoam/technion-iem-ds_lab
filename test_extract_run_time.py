from unittest import TestCase
from AsyncChecker import extract_run_time


class TestExtract_run_time(TestCase):
    def test_extract_run_time(self):
        s = """----------- compilation OK
--- about to run: /home/noam/technion-iem-DS_ex/94201/ex3/homework3 /home/noam/technion-iem-DS_ex/94201/ex3/csv/50.csv
run time: 0.25 user 0.01 system
--- finished the tested run.
Comparing output , /home/noam/technion-iem-DS_ex/94201/ex3/50_out_fast
Traceback (most recent call last):
  File "/home/noam/technion-iem-ds_lab/tester_ex3.py", line 13, in <module>
    from frozendict import frozendict
ImportError: No module named frozendict
============ 1
Sorry: some error occured. Please examine the STDERR"""
        assert(extract_run_time(s) == 0.26)

