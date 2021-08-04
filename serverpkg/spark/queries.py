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


def get_logs(cluster_url_name, passwd, appId):
    """ get the logs of the application from the Spark cluster.
        This function uses YARN log aggregation.

    :param cluster_url_name: URL of the spark cluster
    :param appId: unique application ID created when submitting a batch to the spark master
    :return: tuple (reply body, HTTP status code)
    """
    # yarn logs  -am -1    -log_files stdout -applicationId application_1624861312520_0009

    # get the log of stdout from the last run from this appId
    cmd = f"yarn logs  -am -1 -log_files stdout -applicationId {appId}"
    logger.info(f"connecting using SSH to Spark node {cluster_url_name}")
    try:
        output = ssh_client(host=cluster_url_name, user="sshuser", password=passwd, command=cmd)
    except pssh.exceptions.UnknownHostError as ex:
        logger.error("SSH receive error" + str(ex))
        return utils.wrap_html_source(str(ex)), HTTPStatus.SERVICE_UNAVAILABLE
    except pssh.exceptions.AuthenticationError as ex:
        print("SSH connection error" + str(ex))
        return utils.wrap_html_source(str(ex)), HTTPStatus.SERVICE_UNAVAILABLE
    except Exception as ex:
        return utils.wrap_html_source(str(ex)), HTTPStatus.INTERNAL_SERVER_ERROR

    return utils.wrap_html_source(output), HTTPStatus.OK


def get_appId_from_batchId( url: str,  livy_pass: str, batch_id: int) -> str:
    """

    :param url:
    :param batch_id:
    :return:
    :raise: requests.exceptions, ConnectionError, SparkError
    """
    q = f"/livy/batches/{batch_id}"
    h = {"X-Requested-By": "admin" , "Content-Type": "application/json"}

    auth = HTTPBasicAuth('admin', livy_pass)
    try:
        reply=requests.get(url=url+"/"+q, headers=h, auth=auth, timeout=10.0)
        if reply.status_code != HTTPStatus.OK:
            raise SparkError("batch ID NOT FOUND")
    except requests.exceptions.SSLError as ex:
        raise ConnectionError(str(ex))
    try:
        j = reply.json()
    except json.JSONDecodeError:
        logger.error("get_appId_from_batchId: response is not json")
        raise SparkError("response is not json")
    logger.info("appid=%s, batchId=%d"%( j["appId"], batch_id))
    return j["appId"]


def test():
   cluster_url_name="https://noam-spark.azurehdinsight.net"
   cluster_ssh_url_name = "noam-spark-ssh.azurehdinsight.net"
   passwd = "%Qq12345678"
   appId = get_appId_from_batchId(cluster_url_name, passwd, 33)
   print("calling get_logs({},{})".format(cluster_url_name,appId))
   x = get_logs(cluster_ssh_url_name,passwd, appId)
   print("returned\n", x)

if __name__ == "__main__":
    test()
