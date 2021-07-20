"""
check Azure related system health
"""

from serverpkg.server import app
from ..logger import Logger
logger = Logger(__name__).logger

def check_azcopy():
    """:return True if succeed uploading a file to my subs/container; False otherwise """
    import subprocess
    completed_proc = subprocess.run( [app.config['runner_dir'] + '/check_azcopy.sh'], stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False)

    if completed_proc.returncode != 0:
        logger.info("STDERR:\n" + completed_proc.stderr.decode('utf-8'))

    return completed_proc.returncode == 0
