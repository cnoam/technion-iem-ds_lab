# written and tested on linux only
# It will not work on Windows

import logging
import utils
import os
import sys

from .motd import Motd

if sys.version_info.major != 3:
    raise Exception("must use python 3")


from .logger import Logger
from http import HTTPStatus
from flask import Flask, flash, request, redirect, render_template
from werkzeug.utils import secure_filename
import subprocess
from .asyncChecker import AsyncChecker
from . import show_jobs, job_status
from apscheduler.schedulers.background import BackgroundScheduler
from serverpkg.spark.SparkResources import SparkResources
from serverpkg.spark.queries import SparkError

from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

rate_limiter = None
REDIS_URL="storage" # the name as we know it in the docker-compose file
rate_limiter_enabled = True

def _configure_app():
    global scheduler
    global rate_limiter
    app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024
    data_path = os.environ['CHECKER_DATA_DIR']

    # strip trailing '/' if there is one
    if data_path[-1] == '/':
        data_path = data_path[0:-1]
    app.config['data_dir'] = data_path + '/data'
    app.config['matcher_dir'] = data_path + '/matchers'
    app.config['runner_dir'] = data_path + '/runners'
    app.config['assignment_config_file'] = data_path + '/hw_settings.json'
    app.config['database_dir'] = os.environ['CHECKER_LOG_DIR']

    # app.config['LDAP_HOST'] = 'ldap://ccldap.technion.ac.il'
    # app.config['LDAP_BASE_DN'] = 'ou=tx,dc=technion,dc=ac,dc=il'
    # app.config['LDAP_USERNAME'] = 'cn=cnoam,ou=Users,dc=il'
    # app.config['LDAP_PASSWORD'] = '--'
    app.secret_key = b'3456o00sdf045'

    # we may want to limit who can submit jobs.
    # if the set is empty - no limit. if non empty, it contains the ID of the person allowed.
    # Better to have it per course, but not worth the effort.
    app.config['allowed_submitter_id'] = utils.load_allowed_submitters_id(f'{app.config["data_dir"]}/course_users.txt')
    if len(app.config['allowed_submitter_id']) == 0:
        logging.warning("There is no limitation on submitter ID. Anyone can submit jobs.")

    # Try to get SPARK related vars, but don't fail here if we don't have it
    app.config['cluster_name'] = os.getenv('SPARK_CLUSTER_NAME')
    app.config['cluster_url_ssh'] = f"{app.config['cluster_name']}-ssh.azurehdinsight.net"
    app.config['cluster_url_https'] = f"https://{app.config['cluster_name']}.azurehdinsight.net"
    app.config['livy_password'] = os.getenv('LIVY_PASS')

    # todo: this should be checked only for projects using spark.
    if app.config['cluster_name'] is None:
        #return "Internal Error: missing SPARK_CLUSTER_NAME env var in the server", HTTPStatus.INTERNAL_SERVER_ERROR
        raise KeyError('cluster_name')
    if app.config['livy_password'] is None:
        #return "Internal Error: missing LIVY_PASS env var in the server", HTTPStatus.INTERNAL_SERVER_ERROR
        raise KeyError('livy_password')

    app.config['spark_private_key_path'] = os.getenv('SPARK_PKEY_PATH')  # absolute file path to the private key file. Needed for ssh auth.

    # This is not a config, so maybe move it from here
    app.config['spark_rm'] = SparkResources(cluster_name=app.config['cluster_name'],
                                            cluster_url_ssh=app.config['cluster_url_ssh'],
                                            cluster_url_https=app.config['cluster_url_https'],
                                            priv_key_path=app.config['spark_private_key_path'],
                                            livy_pass=app.config['livy_password'],
                                            allowed_submitters=app.config['allowed_submitter_id']
                                            )

    # The limiter needs persistent storage.
    # We use a REDIS server (in another docker container)
    rate_limiter = Limiter(app, key_func=get_remote_address,
                           storage_uri=f"redis://{REDIS_URL}:6379",
                           default_limits=["2000 per day", "60 per hour"],
                           enabled=rate_limiter_enabled)

    logger.info("Exiting _configure_app")

class SanityError(Exception):
    pass


class _HttpStatusError(Exception):
    def __init__(self, reason_string, status_code):
        self.text = reason_string
        self.status_code = status_code


def allowed_file(filename, extensions):
    # import re
    # matches = re.findall('^\d{8,9}(_\d{8,9})?(_\d{8,9})?.py', filename)
    # ok = len(matches) > 0
    # logger.info("allowed_file: filename " + ('OK' if ok else 'rejected'))
    # return ok
    if len(extensions) == 0:
        return True
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in extensions


def _running_on_dev_machine():
    """:return True if this is my dev machine"""
    import socket
    return 'noam' in socket.gethostname()
# ---------------------


# -- prepare some global vars
app = Flask(__name__, template_folder='./templates')

_job_status_db = None
#one_time_init_called = False
def one_time_init():
    """This function should be called once the server is up, and only once.
    If not done like this, gunicorn will start K workers and each will have its own scheduler
    """
    global _job_status_db
    global one_time_init_called
    scheduler = BackgroundScheduler()
    scheduler.start()
    _configure_app()
    _job_status_db = job_status.JobStatusDB(app.config['database_dir'])
    _job_status_db._create_tables()

    try:
        course_id = _get_configured_course_ids()
    except FileNotFoundError:
        logger.fatal("Configuration file not found. Check permissions and name")

    _purge_db_stale_jobs()

    # add a periodic task to get updates from Spark server.
    # We want that only ONE process will run this periodic job, and all workers will be able to read the results
    rm = app.config['spark_rm']
    scheduler.add_job(rm.update_running_apps, 'interval', seconds=SparkResources.SPARK_POLLING_INTERVAL_sec)
    #one_time_init_called = True
    logger.info("Exiting one_time_config")

logger = Logger(__name__).logger

# The following import is needed to prepare the admin endpoints
# regretably, the admin module uses _job_status_db so it can be imported only here
from . import admin

MAX_CONCURRENT_JOBS = os.cpu_count()
if MAX_CONCURRENT_JOBS is None:
    MAX_CONCURRENT_JOBS = 2  # rumored bug in getting the cpu count


_configure_app()
_job_status_db = job_status.JobStatusDB(app.config['database_dir'])
_job_status_db._create_tables()



# ssl
#LDAP_SCHEMA = environ.get('LDAP_SCHEMA', 'ldaps')
#app.config['LDAP_PORT'] =  DAP_PORT = os.environ.get('LDAP_PORT', 636)
# openLDAP
#app.config['LDAP_OPENLDAP'] = True
# Users
#app.config['LDAP_USER_OBJECT_FILTER'] = '(uid=%s)'
# Groups
#app.config['LDAP_GROUP_MEMBER_FILTER'] = '(|(&(objectClass=*)(member=%s)))'
#app.config['LDAP_GROUP_MEMBER_FILTER_FIELD'] = 'cn'
# Error Route
# @app.route('/unauthorized') <- corresponds with the path of this route when authentication fails
#app.config['LDAP_LOGIN_VIEW'] = 'unauthorized'
#ldap = LDAP(app)

#g.user = "nnn"
# @app.route('/ldap')
# #@ldap.login_required
# def test_ldap():
#     test = ldap.bind_user(app.config['LDAP_USERNAME'], app.config['LDAP_PASSWORD'])
#     print(test)


def is_maintenance_mode():
    """return True if the server is in maint mode
    """
    by_env = os.getenv('MAINTENANCE_MODE') is not None
    by_file = os.path.exists('/data/maintenance')
    return by_env or by_file

@app.before_request
def check_for_maintenance():
    rule = request.url_rule.rule if request.url_rule else ''
    if is_maintenance_mode() and 'maintenance' not in rule:
        return render_template('offline_for_maintanance.html')

@app.errorhandler(401)
@app.route('/unauthorized')
def unauthorized_message(e):
    return 'Unauthorized, username or password incorrect'
# ---------------------------------
@app.route('/',methods = ['GET'])
def index():
    import utils
    footer_text = 'commit id: {}'.format(utils.version_string())
    return render_template('index.html', running_locally=_running_on_dev_machine(),  motd = Motd().get_message(), footer= footer_text)


@app.route('/status', methods=['GET'])
def get_server_status():
    import json
    return json.dumps({'num_jobs': _job_status_db.num_running_jobs()})


@app.route('/status/azure', methods=['GET'])
def get_azure_status():
    import serverpkg.spark.azure_health as az
    import json
    return json.dumps({'azcopy upload': 'success' if az.check_azcopy() else 'fail'} )


@app.route('/jobs')
def show_jobs_():
    """
    create a nice table with all the jobs past and present
    :return: html page
    """
    return show_jobs.show_jobs(_job_status_db)


# noinspection PyPackageRequirements
@app.route('/<int:course>/submit/<ex_type>/<int:number>', methods=['GET', 'POST'])
def handle_submission(course,ex_type, number):

    # first, check the config for this URL
    try:
        config = _get_config_for_ex(course,ex_type,number)
    except KeyError as ex:
        return "We don't have such a value. " +  str(ex), HTTPStatus.NOT_FOUND
    except SanityError as ex:
        return "<H1>Message to Tutor</H1>There is something wrong in the config file for this exercise.<br>"\
               "Please fix and submit again. <br><strong>Error: " + str(ex) + '</strong>'
    except FileNotFoundError:
        return "<H1>Message to Tutor</H1>The config file is not found. Deleted or access problems?<br>" , HTTPStatus.NOT_FOUND


    if request.method == 'GET':
        return render_template('upload_homework.html',
                               file_types=str(config.get('allowed_extension',[])),
                               course_number=course, hw_number=number,
                               num_jobs_running=_job_status_db.num_running_jobs(),
                               motd=Motd().get_message())

    if _job_status_db.num_running_jobs() >= MAX_CONCURRENT_JOBS:
        return "Busy! try again in a few seconds.", HTTPStatus.SERVICE_UNAVAILABLE


    # check if the post request has the file part
    if 'file' not in request.files:
        flash('No file part')
        return redirect(request.url)
    # if user does not select file, browser also
    # submit an empty part without filename
    file = request.files['file']
    if file.filename == '':
        flash('No selected file')
        return redirect(request.url)

    if ex_type not in ('lab', 'hw'):
        return "please use {lab|hw} in the URL", HTTPStatus.BAD_REQUEST
    try:
        uploaded_file_path = _upload_file(config.get('allowed_extension',[]))
    except _HttpStatusError as e:
        return e.text, e.status_code

    the_reply = "oops. uninitialized variable", 500
    compare_to_golden = False
    try:
        postfix = "GOLD" if compare_to_golden else ""
        reference_output = "{}/{}/ref_{}_{}_output{}".format(app.config['data_dir'],course,ex_type,number,postfix)
        reference_input  = "{}/{}/ref_{}_{}_input{}".format(app.config['data_dir'],course,ex_type, number, postfix)
        logger.info(" ref files supplied to handler: " + reference_input + "   " + reference_output)
        logger.info("uploaded file: " + uploaded_file_path)
        the_reply = handle_file(uploaded_file_path,course, ex_type, number, reference_input, reference_output,
         #                      lambda :os.unlink(uploaded_file_path))
        None)
    except FileNotFoundError as e:
        logger.error("Internal error. This is probably a race condition: %s", e)

    return the_reply


def _upload_file(extensions :list):
    """ upload homework 'number'
    :param extensions list of possible file extensions e.g. ['zip', 'c' ] . Can be empty
    :return absolute file path of the loaded file or raise
    :note Caller has to remove the temp dir created here
    """
    assert request.method == 'POST'
    file = request.files['file']

    if not(file and allowed_file(file.filename, extensions)):
        raise _HttpStatusError("unexpected file type", 400)

    filename = secure_filename(file.filename)
    if filename != file.filename:
        raise _HttpStatusError(
            "Please use a valid file name (without spaces) (e.g. ex560.tar.gz)",HTTPStatus.BAD_REQUEST)
    import tempfile
    saved_file_name = os.path.join(tempfile.mkdtemp(), filename)
    try:
        file.save(saved_file_name)
    except Exception as e:
        logger.error("Failed saving file %s (%s)" , saved_file_name,e)
        raise
    return saved_file_name

#TODO: this endpoint will require authentication
@app.route('/<int:course>/submit/goldi/<ex_type>/<int:number>', methods=['GET', 'POST'])
def upload_file_golden_ref(course,ex_type, number):
    return _upload_file(course,ex_type, number, compare_to_golden=True)


@app.route('/check_job_status/<int:job_id>')
def get_job_stat(job_id):
    try:
        return _job_status_db.get_job_stat(job_id)
    except KeyError:
        return "job id not found", HTTPStatus.NOT_FOUND
    

@app.route('/<int:course>/<int:hw_id>/leaderboard')
def show_leaderboard(course,hw_id):
    """show html page of the leader board for (course, homeworkID)"""
    if not str(course) in course_id:
        return "course not found", HTTPStatus.NOT_FOUND
    from .leaderboard import Leaderboard
    board = Leaderboard(_job_status_db)
    return board.show(str(course), ex_name=hw_id)


# TODO this (like many others) is not related to the Server code. move to another file
# TODO the job object contains the courseID, so remove it from the url
@app.route('/<int:courseId>/show_diff', methods=['GET', 'POST'])
def show_diff(courseId):
    """returns an HTML page with visual diff between the reference file and the actual output.
    arguments are passed to the GET/POST:  first=94219/ref_hw_2_output&jobid=876'
    """
    from .show_file_diff import show_html_diff
    print(request.args)
    first = request.args.get('first')
    second = request.args.get('jobid')

    if second is None:
        return "arg 'jobid' missing", HTTPStatus.BAD_REQUEST
    try:
        job_id = int(second)
    except ValueError:
        return "arg 'jobid' has to be a job id", HTTPStatus.BAD_REQUEST

    job = _job_status_db.select_a_job(job_id)
    if job is None:
        return "job ID not found", HTTPStatus.NOT_FOUND

    if job.course_id != courseId:
        return "This job belongs to another course", HTTPStatus.NOT_FOUND

    return show_html_diff(job.course_id, job, first)

@app.route('/spark/delete', methods=['GET'])
def delete_spark_batch():
    """ the URL format is /spark/delete?batchId=<batch-id>
    WARNING: no authentication is done here!"""
    import re
    from serverpkg.spark import queries
    batchId = request.args.get('batchId')  # 42
    if batchId is None:
        return "use ?batchId=4", HTTPStatus.BAD_REQUEST

    url = app.config['cluster_url_https']
    live_pass = app.config['livy_password']
    queryObj = app.config['spark_rm'].query
    try:
        try:
            batchId = int(batchId)
        except ValueError:
            return "batch Id must be integer", HTTPStatus.BAD_REQUEST

        # before risking exception, remove the batchID from our local list.
        # If there is a temporary connection error, this will give extra credit to this user, but we can live with it.
        app.config['spark_rm'].remove_value(batchId)

        appId = queryObj.get_appId_from_batchId(batchId)
        if appId is None:
            return f"There is no AppId yet for batch {batchId}. Please try again later", HTTPStatus.OK

        match = re.findall(r"^application_\d{13}_\d{4}$", appId)
        if match is None or len(match) != 1:
            return "use ?appId=application_1624861312520_0009", HTTPStatus.BAD_REQUEST

        response = queryObj.delete_batch(batchId)
    except ConnectionError:
        return "Could not connect to the Spark server", HTTPStatus.BAD_GATEWAY
    except SparkError as ex:
        return "Spark server returned unexpected value or did not find the requested batch:  " + str(
            ex), HTTPStatus.NOT_FOUND
    return ("job deleted" if response.status_code == HTTPStatus.OK else "failed deleting the job" + response.text), response.status_code


@app.route('/spark/logs')
@rate_limiter.limit("1 per minute")
def get_spark_logs():
    """ get the logs from an application running in spark server.
    """
    from serverpkg.spark import queries
    appId=request.args.get('appId') # application_1624861312520_0009
    batchId=request.args.get('batchId') # 42

    if appId is None and batchId is None:
        return "use ?appId=application_1624861312520_0009 or ?batchId=4", HTTPStatus.BAD_REQUEST

    query_ = app.config['spark_rm'].query
    try:
        if batchId:
            try:
                batchId = int(batchId)
            except ValueError:
                return "batch Id must be integer", HTTPStatus.BAD_REQUEST
            appId = query_.get_appId_from_batchId(batchId)
            if appId is None:
                return f"There is no AppId yet for batch {batchId}. Please try again later", HTTPStatus.OK

        response = query_.get_logs(appId)
    except ConnectionError:
        return "Could not connect to the Spark server", HTTPStatus.BAD_GATEWAY
    except queries.SparkError as ex:
        return "Spark server returned unexpected value or did not find the requested batch:  "+ str(ex), HTTPStatus.NOT_FOUND
    return response


def handle_file(package_under_test,course_number, ex_type, ex_number, reference_input, reference_output, completionCb):
    """Send the file to execution. If async, return immediately"""

    use_async = True

    # HACK
    if course_number == 96224:
        # '/tmp/tmpfu0d54qs/58708389_111111111_66666666.py'  -> '58708389'
        slash = package_under_test.rfind('/') + 1
        sender = package_under_test[slash: package_under_test.find('_', slash  )]
        stat = app.config['spark_rm'].allow_user_to_submit(sender)
        logger.info(f"allow_user_to_submit({sender}) returned {stat}")
        if not stat['ok']:
            return stat['reason'], HTTPStatus.UNAUTHORIZED

        # we need the batch ID which is available only when the async call will finish so chain the callbacks
        from serverpkg.spark import SparkCallback
        s = SparkCallback.SparkCallback(sender=sender, resource_m= app.config['spark_rm'], cb=completionCb)
        completionCb = s

    if use_async:
        return handle_file_async(package_under_test, course_number, ex_type, ex_number, reference_input, reference_output,completionCb)
    else:
        logger.warning("this path is not maintained!")
        rv = handle_file_blocking(package_under_test, reference_input, reference_output)
        if completionCb is not None:
            completionCb()
        return rv


def _get_configured_course_ids():
    """:returns list of course ID  :type list(string)
    """
    import json
    with open(app.config['assignment_config_file'], "r") as fin:
        params = json.load(fin)
        return list(params.keys())


def _get_config_for_ex(course_number, ex_type,ex_number):
    """choose the proper (runner,matcher,...)
       for a given (course_number,ex_type,ex_number)
       :raise KeyError, FileNotFoundError, SanityError
       :return dict with keys for (matcher, executor, timeout, data_path, extensions) . Optional keys e.g. data_path may be missing

    config file in json.
    if the config file is invalid, refuse to run.
    if a value is invalid, refuse to run ( e.g. matcher/runner not found or not executable )

    Example:
  { "94201":[ {
     "id": 4,
     "matcher" : "./tester_ex4.py",
     "runner" :"./check_py.sh",
     "timeout" : 300,
     "calc_score": true <<<<<<< [FUTURE]optional. default to false
     },
     {
     "id": 1,
     "matcher" : "./exact_match.py",
     "runner" :"./check_cmake.sh",
     "timeout" : 5,
     "blocking": true, <<<<<<< [FUTURE]optional. default to false
     "allowed_extension": ["zip", "java"], <<<< optional
     "data_path": "/data/94219/yob" <<<< optional folder name
     }
    ]
   }
    """
    import json
    with open(app.config['assignment_config_file'], "r") as fin:
        params = json.load(fin)
    try:
        params = params[str(course_number)]
    except KeyError:
        logger.warning("course number not found in config file")
        raise KeyError("course number {} not found in the config file".format(course_number))
    for e in params:
        if e['id'] == ex_number:
            break
    else:
        raise KeyError("ex {} not found in the config file".format(ex_number))

    matcher = e['matcher']
    executor = e['runner']
    timeout = e['timeout']
    _check_sanity(matcher, executor, timeout)
    return e


def _check_sanity(comparator_file_name, executor_file_name, timeout):
    """try to catch obvious problems in the parameters.
    :raise  internal error (because it is server side problem)
    """
    if timeout < 1 or timeout > 3000:
        raise SanityError("timeout out of range")

    # check that the file exists and is executable
    import os
    if not app.config['matcher_dir']:
        raise SanityError("matchers dir not set. Check ENV var CHECKER_DATA_DIR")

    if not app.config['runner_dir']:
        raise SanityError("runners dir not set. Check ENV var CHECKER_DATA_DIR")
    if not os.path.isfile(os.path.join(app.config['matcher_dir'],comparator_file_name)):
        raise SanityError("matcher not found: "+comparator_file_name)
    full_path = os.path.join(app.config['runner_dir'],executor_file_name)
    if not os.path.isfile(full_path):
        raise SanityError("file not found: "+executor_file_name)
    if not os.access(full_path, os.X_OK):
        raise SanityError("executor is not eXcutable: " + executor_file_name)


def handle_file_async(package_under_test, course_number, ex_type, ex_number, reference_input, reference_output,completionCb):
    """
    handle the supplied file: unpack, build, run, compare to golden reference.
    The operation is async (non blocking). A thread is created to handle the request
    and an entry in a "database" table is created to let the user see the result   
    :param package_under_test: 
    :param reference_input: 
    :param reference_output: 
    :return: html page showing link to the tracking page
    """
    new_job = _job_status_db.add_job((ex_type, ex_number),package_under_test, course_id=course_number)
    try:
        config = _get_config_for_ex(course_number, ex_type, ex_number)
    except KeyError as ex:
        return "invalid ex number? exception=%s    "% str(ex),HTTPStatus.BAD_REQUEST

    # convert to full path
    new_job.set_handlers(os.path.join(app.config['matcher_dir'], config['matcher']),
                         os.path.join(app.config['runner_dir'], config['runner']))

    data_path = os.path.join(app.config['data_dir'], config.get('data_path',""))
    async_task = AsyncChecker(_job_status_db, new_job, package_under_test,
                        reference_input, reference_output, completionCb, data_path, timeout_sec=config['timeout'])
    async_task.start()
    return render_template('job_submitted.html', course_id=course_number, hw_id=ex_number, job_id= new_job.job_id)


def handle_file_blocking(package_under_test, reference_input, reference_output):
    """
    Handle the supplied file: unpack, build, run, compare to golden reference.
    The operation is BLOCKING, so must be completed before timeouts (in browser, http frontend etc. ) will expire.
    
    :param package_under_test: name of the TAR.GZ file containing homework that need to be checked
    :param reference_input file name of the input test vector
    :param reference_output file name of the output test vector
    :return: html doc with the result and maybe an explanation
    """
    timeout = 10
    completed_proc = None
    try:
        logger.debug("ref files:  "+reference_input+","+reference_output)
        #  https://medium.com/@mccode/understanding-how-uid-and-gid-work-in-docker-containers-c37a01d01cf
        completed_proc = subprocess.run( ['./checker.sh',package_under_test, reference_input, reference_output],
                                         check=False, stdout=subprocess.PIPE, stderr=subprocess.PIPE,timeout=timeout)
        if completed_proc.returncode == 0:
            message = "well Done!"
        else:
            message = 'Your code failed. Please check the reported output\n\n' + completed_proc.stdout.decode('utf-8')
            message += "STDERR:\n" + completed_proc.stderr.decode('utf-8')
    #except subprocess.TimeoutExpired:
    #    message = "Your code ran for too long. timeout set to "+ str(timeout) + " seconds"
    except subprocess.CalledProcessError as ex:
        message = 'Your code failed. Please check the reported output\n\n' + completed_proc.stderr.decode('utf-8')

    import utils
    return utils.wrap_html_source(message)


def _purge_db_stale_jobs():
    """due to bugs/crashes the db table may contain jobs with status 'running'
    This will cause the server to refuse more jobs (since it believes it is full).
    When starting the server we know for sure there are no running jobs, so purge them"""
    from .job_status import Job
    _job_status_db.delete_jobs(Job.Status.running)
    _job_status_db.delete_jobs(Job.Status.pending)

# when running under gunicorn, the hook will call  one_time_init()
# When running in the debugger, we need to explicitly call it

# bug: using the flag does not work because this module is first loaded and only then the hook is called.
# possible solution: move it to another module.
# if not one_time_init_called:
#     one_time_init()