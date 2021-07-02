#
# pip install parallel-ssh
import logging
from pssh.clients import ParallelSSHClient
from pssh.utils import enable_host_logger

# loggers = [logging.getLogger(name) for name in logging.root.manager.loggerDict]
# for logger in loggers:
#     logger.setLevel(logging.DEBUG)
   
from pssh.clients import ParallelSSHClient

# client = ParallelSSHClient(['localhost', 'localhost'], user="cnoam", password="bb@Zduke" )
# output = client.run_command('ls /')
# client.join()
#
# for host_output in output:
#     hostname = host_output.host
#     stdout = list(host_output.stdout)
#     print("Host %s: exit code %s, output %s" % (
#           hostname, host_output.exit_code, stdout))


def parallel_ssh(host, user, password, command):
    #enable_host_logger()
    client = ParallelSSHClient([host], user=user, password=password)
    output = client.run_command(command)
    client.join()
    stdout = ""
    for host_output in output:
        stdout_li = list(host_output.stdout)
        for line in stdout_li:
            stdout += line + "\n"

    print("output", stdout)
    return stdout


def ssh_client(host, user, password, command):
    return parallel_ssh(host, user, password, command)

if __name__ == "__main__":
    o = parallel_ssh("localhost", user="cnoam", password="", command="ls /")
    print(o)
