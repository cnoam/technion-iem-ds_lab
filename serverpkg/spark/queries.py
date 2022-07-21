import json
from http import HTTPStatus
import pssh
import requests
from requests.auth import HTTPBasicAuth
from pssh import exceptions
import utils
from .ssh_client import ssh_client
from serverpkg.logger import Logger
logger = Logger(__name__).logger

class ConnectionError(Exception): pass
class SparkError(Exception):pass


class SparkAdminQuery:
    """
    All queries sent to Spark are implemented here.
    Currently some are using Yarn directly using SSH with public keys, and some Livy using HTTPS with password.

    TODO: move everything to livy. change access to public key (why?). Even better, use a Livy client lib.
    If not possible, change the SSH to keep connection open -- this will expedite the results
    """
    def __init__(self,cluster_url_ssh_name,cluster_url_https, pkey, livy_password):
        self.cluster_url_ssh_name = cluster_url_ssh_name
        self.pkey = pkey
        self.password = livy_password
        self.timeout = 10 # seconds
        self.url_https = cluster_url_https

    def get_spark_app_list__(self) -> list:
        """ get the list of the running applications from the Spark cluster.
            This function uses YARN application .
        https://hadoop.apache.org/docs/current/hadoop-yarn/hadoop-yarn-site/YarnCommands.html#application_or_app

        :param cluster_url_ssh_name URL of the spark cluster FOR SSH ACCESS
        :param pkey path to private key file (str)
        :return: list of application ID found. Anything found is considered running, because yarn does not report completed jobs
        :raise ConnectionError and similar
        """
        cmd = f"yarn application -list"
        logger.info(f"connecting using SSH to Spark node {self.cluster_url_ssh_name}")
        try:
            output = ssh_client(host=self.cluster_url_ssh_name, user="sshuser", pkey=self.pkey, command=cmd)
        except (pssh.exceptions.UnknownHostError, pssh.exceptions.AuthenticationError) as ex:
            logger.error("SSH receive error" + str(ex))
            raise ConnectionError(str(ex))

        """ Sample output of the yarn command:
        $ yarn app -list
        WARNING: YARN_OPTS has been replaced by HADOOP_OPTS. Using value of YARN_OPTS.
        22/07/18 19:05:39 INFO client.RequestHedgingRMFailoverProxyProvider: Created wrapped proxy for [rm1, rm2]
        22/07/18 19:05:39 INFO client.AHSProxy: Connecting to Application History server at headnodehost/10.0.0.20:10200
        22/07/18 19:05:39 INFO client.RequestHedgingRMFailoverProxyProvider: Looking for the active RM in [rm1, rm2]...
        22/07/18 19:05:39 INFO client.RequestHedgingRMFailoverProxyProvider: Found active RM [rm2]
        Total number of applications (application-types: [], states: [SUBMITTED, ACCEPTED, RUNNING] and tags: []):1
                        Application-Id	    Application-Name	    Application-Type	      User	     Queue	             State	       Final-State	       Progress	                       Tracking-URL
        application_1658167526288_0002	Thrift JDBC/ODBC Server	               SPARK	     spark	 thriftsvr	           RUNNING	         UNDEFINED	            10%	http://hn0-spark9.t3p4njszo5nu3nsz0bqcjd4e2e.bx.internal.cloudapp.net:5040
        
        """
        lines = [x for x in output.split('\n') if x.startswith('application')]
        app_ids = [x[0: x.find('Thrift')].strip() for x in lines]
        return app_ids

    def get_spark_app_list(self) -> list:
        """ get the list of the running applications from the Spark cluster.
            This function uses Livy.

            The list contains all the applications - both running and completed.
            Also, some of the applications are created by spark itself.

        :return: list of { 'id' : batchid, 'application_id': appId, 'state': "running" | ... }
        :raise ConnectionError and similar
        """
        q = f"/livy/batches/"
        h = {"X-Requested-By": "admin", "Content-Type": "application/json"}
        auth = HTTPBasicAuth('admin', self.password)
        try:
            reply = requests.get(url=self.url_https + "/" + q, headers=h, auth=auth, timeout= self.timeout)
            if reply.status_code == HTTPStatus.UNAUTHORIZED:
                raise SparkError("authorization problem in Livy access")
            if reply.status_code != HTTPStatus.OK:
                raise SparkError(reply.text)
        except (requests.exceptions.SSLError, requests.exceptions.ConnectionError) as ex:
            logger.error(ex)
            raise ConnectionError(ex)
        try:
            j = reply.json()
        except json.JSONDecodeError:
            logger.error("get_appId_from_batchId: response is not json")
            raise SparkError("response is not json")
        return j['sessions']

    def get_logs(self, appId):
        """ get the logs of the application from the Spark cluster.
            This function uses YARN log aggregation.

        :param cluster_url_name: URL of the spark cluster
        :param appId: unique application ID created when submitting a batch to the spark master
        :return: tuple (reply body, HTTP status code)
        """
        # yarn logs  -am -1    -log_files stdout -applicationId application_1624861312520_0009
        # get the log of stdout from the last run from this appId
        cmd = f"yarn logs  -am -1 -log_files stdout -applicationId {appId}"
        logger.info(f"get_logs({appId}): connecting using SSH to Spark node {self.cluster_url_ssh_name}")
        try:
            output = ssh_client(host=self.cluster_url_ssh_name, user="sshuser", pkey=self.pkey, command=cmd)
        except pssh.exceptions.UnknownHostError as ex:
            logger.error("SSH receive error" + str(ex))
            return utils.wrap_html_source(str(ex)), HTTPStatus.SERVICE_UNAVAILABLE
        except pssh.exceptions.AuthenticationError as ex:
            logger.error("SSH connection error" + str(ex))
            return utils.wrap_html_source(str(ex)), HTTPStatus.SERVICE_UNAVAILABLE
        except Exception as ex:
            return utils.wrap_html_source(str(ex)), HTTPStatus.INTERNAL_SERVER_ERROR

        return utils.wrap_html_source(output), HTTPStatus.OK

    def delete_batch(self, batchId):
        """delete a spark job.
         Use Livy HTTP DELETE command"""
        logger.info(f"delete_batch({batchId})")
        response = requests.delete(f"{self.cluster_url_ssh_name}/livy/batches/{batchId}",
                                   auth=HTTPBasicAuth('admin', password=self.password),
                                   headers = {'X-Requested-By': 'admin'})
        if response.status_code != HTTPStatus.OK:
            logger.warning("Delete batch:" + str(response.content))
        return response

    def get_appId_from_batchId(self, batch_id: int) -> str:
        """
        :param batch_id:
        :return: application ID (str)
        :raise: requests.exceptions, ConnectionError, SparkError
        """
        logger.info(f"get_appId_from_batchId(batchid={batch_id})")
        q = f"/livy/batches/{batch_id}"
        h = {"X-Requested-By": "admin" , "Content-Type": "application/json"}

        auth = HTTPBasicAuth('admin', self.password)
        try:
            reply=requests.get(url= self.url_https +"/"+q, headers=h, auth=auth, timeout=self.timeout)
            if reply.status_code == HTTPStatus.UNAUTHORIZED:
                raise SparkError("authorization problem in Livy access")
            if reply.status_code != HTTPStatus.OK:
                raise SparkError("batch ID NOT FOUND")
        except (requests.exceptions.SSLError, requests.exceptions.ConnectionError) as ex:
            logger.error(ex)
            raise ConnectionError(ex)
        try:
            j = reply.json()
        except json.JSONDecodeError:
            logger.error("get_appId_from_batchId: response is not json")
            raise SparkError("response is not json")
        logger.info(f"get_appId_from_batchId(batchid={batch_id}) == {j['appId']}")
        return j['appId']


def test_get_log():
    q = SparkAdminQuery(cluster_url_ssh_name="noam-spark-ssh.azurehdinsight.net", livy_password= "111")
    #cluster_url_name="https://noam-spark.azurehdinsight.net"
    #cluster_ssh_url_name = "noam-spark-ssh.azurehdinsight.net"
    appId = q.get_appId_from_batchId(url="https://noam-spark.azurehdinsight.net",  batch_id=33)
    x = q.get_logs(appId)
    print("returned\n", x)

def test_delete():
    q = SparkAdminQuery(cluster_url_ssh_name="https://noam-spark.azurehdinsight.net", livy_password="111", pkey="")
    x = q.delete_batch(batchId=33)
    print("returned\n", x)

if __name__ == "__main__":
    test_delete()
