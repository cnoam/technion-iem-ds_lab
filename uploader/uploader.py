"""
Upload homework TAR.GZ file from zip file created by Moodle to the Automatic Checker

Student's homework submissions can be downloaded from Moodle in one zip file.

We assume here that ALL the submissions are in a TAR.gz format (one file for each submission)
This script will open the ZIP file, and upload all the files in it to the checker.
If the server is busy, it will wait.

When all files are uploaded, the script exits.

Usage:
upload_to_checker.py [--host=server_name] zip_file_name exercise_number

"""

import logging
import os
import tempfile
import threading
import time
import shutil
import zipfile
from http import HTTPStatus

import requests

MAX_JOBS = 2  # TODO remove this value and rely on the server's 503 code .

logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')


class Uploader():
    def __init__(self, host_server, upload_url):
        """
        :param host_server: host name of the server where the file will be uploaded to. e.g. "homework.com"
        :param upload_url: path to the upload : e.g. "/submit/hw/3/"
        """
        self.input_queue = []
        self.server_url = upload_url
        self.host_server = host_server
        self.http_scheme = "http://"
        self.num_uploaded = 0
        self.total_num_enqueued = 0

    def enqueue_for_upload(self, file_name):
        """
        enqueue a file name to be uploaded.
        return immediately
        :param file_name:
        """
        self.input_queue.append(file_name)  # careful - should it be thread safe?
        self.total_num_enqueued += 1

    def start_uploading(self):
        """ create a worker thread,
        start uploading from the input queue, do not overwhelm the server
        :return immediatley.
        """
        self.worker_thread = threading.Thread(target=self._work)
        self.worker_thread.start()

    def _upload(self, file_name):
        # full path is needed for opening the file, but for clarity,
        # the server should get only the basename
        files = {'file': (os.path.basename(file_name), open(file_name, 'rb'), 'application/gzip', {'Expires': '0'})}
        r = requests.post(self.http_scheme + self.host_server + self.server_url, files=files)
        if r.status_code != HTTPStatus.OK:
            logging.error("Server returned " + str(r))
            if r.status_code == HTTPStatus.SERVICE_UNAVAILABLE:
                logging.fatal("oops. Server is asked to work when busy. This should not happen.")
            raise RuntimeError()

        self.num_uploaded += 1
        logging.info(
            "Uploaded {} files. {} to go.".format(self.num_uploaded, self.total_num_enqueued - self.num_uploaded))

    def _check_server_status(self):
        import json
        r = requests.get(self.http_scheme + self.host_server + "/status")
        j = None
        try:
            j = r.json()
        except json.decoder.JSONDecodeError:
            logging.fatal("The server does not cooperate. Check server version.")
        return j

    def _work(self):
        """worker thread proc"""
        while len(self.input_queue) > 0:
            reply = self._check_server_status()
            while reply['num_jobs'] >= MAX_JOBS:
                logging.info("Sleeping until the server is not busy...")
                time.sleep(4)
                reply = self._check_server_status()
            self._upload(self.input_queue.pop(0))
        logging.info("worker finished")

    def wait(self):
        self.worker_thread.join()


if __name__ == "__main__":
    import argparse

    # TODO: connect to the "source copy detector" script

    parser = argparse.ArgumentParser()
    parser.add_argument("--host", help="hostname of the server")
    parser.add_argument("file", help="input file name (ZIP)")
    parser.add_argument("ex_num", help="exercise number (e.g. 3)")
    args = parser.parse_args()

    path_to_zip_file = args.file
    ex_num = args.ex_num
    server = args.host
    if server is None:
        server = "homework-tester.westeurope.cloudapp.azure.com"
    upload_url = "/submit/hw/" + str(ex_num)
    directory_to_extract_to = tempfile.mkdtemp(dir='.')

    try:
        with zipfile.ZipFile(path_to_zip_file, 'r') as zip_ref:
            zip_ref.extractall(directory_to_extract_to)

        uploader = Uploader(server, upload_url)
        for root, dirs, files in os.walk(directory_to_extract_to, topdown=False):
            for name in files:
                uploader.enqueue_for_upload(os.path.join(root, name))
        uploader.start_uploading()
        uploader.wait()
    finally:
        try:
            shutil.rmtree(directory_to_extract_to)
        except PermissionError:
            logging.warning("Could not remove {}. Please remove it manually".format(directory_to_extract_to))
