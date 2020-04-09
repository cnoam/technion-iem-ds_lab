from http import HTTPStatus

from locust import HttpLocust, TaskSet, between, task


class UserUploadFile(TaskSet):
    """ create a load with a ratio of
    4:4:1  --- good upload : bad upload : get status
    """

    def __init__(self, parent):
        super().__init__(parent)

    def on_start(self):
       pass

    @task(4)
    def upload_good_file(self):
        self._upload_file('src.zip')

    @task(4)
    def upload_bad_file(self):
        self._upload_file('HW0_311032833_308554914.zip')

    def _upload_file(self,test_file_name):
        with open('/home/cnoam/Desktop/' + test_file_name, 'rb') as file_up:
            response = self.client.post("/94219/submit/hw/0",
                                        files={'file': (test_file_name, file_up, 'application/zip')})
            #if response.status_code == HTTPStatus.SERVICE_UNAVAILABLE:
            #   response.success()
            if response.status_code not in (HTTPStatus.OK, HTTPStatus.SERVICE_UNAVAILABLE):
                raise Exception('bad response from server')
                # self.parent.StopLocust()

    @task(1)
    def get_status(self):
        response = self.client.get('/status')
        import datetime
        assert response.elapsed < datetime.timedelta(milliseconds=500), "Request took too long"

    def on_stop(self):
        pass


class User(HttpLocust):
    task_set = UserUploadFile
    wait_time = between(1, 3.0)
    # host = "http://localhost:8000"
    host = "http://homework-tester.westeurope.cloudapp.azure.com"
    def setup(self):
        print("setup")

    def teardown(self):
        print("teadrown")