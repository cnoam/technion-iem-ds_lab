from http import HTTPStatus

import utils
from .ssh_client import ssh2_ssh
import logging

def get_logs(cluster_url_name, appId):
    # yarn logs  -am -1    -log_files stdout -applicationId application_1624861312520_0009
    passwd = "%Qq12345678"

    # get the log of stdout from the last run from this appId
    cmd = f"yarn logs  -am -1 -log_files stdout -applicationId {appId}"
    logging.info(f"connecting using SSH to Spark node {cluster_url_name}")
    output,status = ssh2_ssh(host=cluster_url_name, port=22, user="sshuser", password=passwd, command=cmd)
    if status != 0:
        return "Failed connecting to Spark master", HTTPStatus.BAD_GATEWAY

    return utils.wrap_html_source(output), HTTPStatus.OK
