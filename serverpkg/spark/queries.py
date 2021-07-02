from http import HTTPStatus
import pssh
import utils
from .ssh_client import ssh_client
from serverpkg.logger import Logger
logger = Logger(__name__).logger


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


if __name__ == "__main__":
   cluster_url_name="noam-spark-ssh.azurehdinsight.net"
   appId="application_1625220040852_0008"
   print("calling get_logs({},{})".format(cluster_url_name,appId))
   x = get_logs(cluster_url_name,appId)
   print("returned\n",x)


