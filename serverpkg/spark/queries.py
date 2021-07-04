import json
from http import HTTPStatus
import pssh
import requests
from requests.auth import HTTPBasicAuth

import utils
from .ssh_client import ssh_client
from serverpkg.logger import Logger
logger = Logger(__name__).logger

class ConnectionError(Exception): pass
class SparkError(Exception):pass


def get_logs(cluster_url_name, appId):
    """ get the logs of the application from the Spark cluster.
        This function uses YARN log aggregation.

    :param cluster_url_name: URL of the spark cluster
    :param appId: unique application ID created when submitting a batch to the spark master
    :return: tuple (reply body, HTTP status code)
    """
    # yarn logs  -am -1    -log_files stdout -applicationId application_1624861312520_0009
    passwd = "%Qq12345678"

    # get the log of stdout from the last run from this appId
    cmd = f"yarn logs  -am -1 -log_files stdout -applicationId {appId}"
    logger.info(f"connecting using SSH to Spark node {cluster_url_name}")
    try:
        output = ssh_client(host=cluster_url_name, user="sshuser", password=passwd, command=cmd)
    except pssh.exceptions.UnknownHostError as ex:
        print("SSH receive error" + str(ex))
        return utils.wrap_html_source(str(ex)), HTTPStatus.SERVICE_UNAVAILABLE
    except Exception as ex:
        return utils.wrap_html_source(str(ex)), HTTPStatus.INTERNAL_SERVER_ERROR

    return utils.wrap_html_source(output), HTTPStatus.OK


def get_appId_from_batchId( url: str,  livy_pass: str, batch_id: int) -> str:
    """

    :param url:
    :param batch_id:
    :return:
    :raise: requests.exceptions
    """
    q = f"/livy/batches/{batch_id}"
    h = {"X-Requested-By": "admin" , "Content-Type": "application/json"}

    auth = HTTPBasicAuth('admin', livy_pass)
    try:
        reply=requests.get(url=url+"/"+q, headers=h, auth=auth, timeout=10.0)
    except requests.exceptions.SSLError as ex:
        raise ConnectionError('')
    import simplejson
    try:
        j = reply.json()
    except (TypeError, simplejson.errors.JSONDecodeError):
        raise SparkError("response is not json")
    return j["appId"]

if __name__ == "__main__":
   cluster_url_name="https://noam-spark.azurehdinsight.net"
   passwd = "%Qq12345678"
   print(get_appId_from_batchId(cluster_url_name, passwd, 4) )

   appId="application_1625220040852_0008"

   print("calling get_logs({},{})".format(cluster_url_name,appId))
   x = get_logs(cluster_url_name,appId)
   print("returned\n", passwd, x)


