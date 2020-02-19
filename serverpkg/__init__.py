import sys,os
from flask import Flask
from .logger_init import init_logger
from . import job_status

if sys.version_info.major != 3:
    raise Exception("must use python 3")

logger = init_logger('server')

UPLOAD_FOLDER = r'/tmp'
ALLOWED_EXTENSIONS = {'gz','xz','py','sh'}

MAX_CONCURRENT_JOBS = os.cpu_count()
if MAX_CONCURRENT_JOBS is None:
    MAX_CONCURRENT_JOBS = 2  # rumored bug in getting the cpu count

app = Flask(__name__, template_folder='./templates')
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024
app.config['matcher_dir'] = 'serverpkg/matchers'
app.config['runner_dir'] = 'serverpkg/runners'
app.secret_key = b'3456o00sdf045'

_job_status_db = job_status.JobStatusDB()

from . import admin
from . import server