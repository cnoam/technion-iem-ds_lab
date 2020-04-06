# written and tested on linux only
# It will not work on Windows
import sys, os
if sys.version_info.major != 3:
    raise Exception("must use python 3")

from .logger_init import init_logger
from http import HTTPStatus
from flask import Flask, flash, request, redirect, url_for,render_template
from werkzeug.utils import secure_filename
import subprocess
from .asyncChecker import AsyncChecker
from . import show_jobs, job_status




# -- prepare some global vars
app = Flask(__name__, template_folder='./templates')

logger = init_logger('server')


from . import admin

_job_status_db = job_status.JobStatusDB()

ALLOWED_EXTENSIONS = {'zip','gz','xz','py','sh','patch','java'} # TODO: replace with per exercise list
MAX_CONCURRENT_JOBS = os.cpu_count()
if MAX_CONCURRENT_JOBS is None:
    MAX_CONCURRENT_JOBS = 2  # rumored bug in getting the cpu count


def _configure_app():
    app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024
    app.config['matcher_dir'] = 'serverpkg/matchers'
    app.config['runner_dir'] = 'serverpkg/runners'
    app.config['assignment_config_file'] = 'hw_settings.json'

    app.config['LDAP_HOST'] = 'ldap://ccldap.technion.ac.il'
    app.config['LDAP_BASE_DN'] = 'ou=tx,dc=technion,dc=ac,dc=il'
    # app.config['LDAP_USERNAME'] = 'cn=cnoam,ou=Users,dc=il'
    # app.config['LDAP_PASSWORD'] = '--'
    app.secret_key = b'3456o00sdf045'


class SanityError(Exception):
    pass


class _HttpStatusError(Exception):
    def __init__(self, reason_string, status_code):
        self.text = reason_string
        self.status_code = status_code


def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def _running_on_dev_machine():
    """:return True if this is my dev machine"""
    import socket
    return socket.gethostname() == 'noam-cohen-u.iem.technion.ac.il'

# ---------------------

_configure_app()



# ssl
#LDAP_SCHEMA = environ.get('LDAP_SCHEMA', 'ldaps')
app.config['LDAP_PORT'] =  DAP_PORT = os.environ.get('LDAP_PORT', 636)
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

@app.errorhandler(401)
@app.route('/unauthorized')
def unauthorized_message(e):
    return 'Unauthorized, username or password incorrect'
# ---------------------------------
@app.route('/',methods = ['GET'])
def index():
    return render_template('index.html', running_locally = _running_on_dev_machine())


@app.route('/status', methods=['GET'])
def get_server_status():
    import json
    return json.dumps({'num_jobs': _job_status_db.num_running_jobs()})


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
    if request.method == 'GET':
        return render_template('upload_homework.html',
                               file_types=str(ALLOWED_EXTENSIONS),
                               course_number=course, hw_number=number,
                               num_jobs_running=_job_status_db.num_running_jobs())

    if _job_status_db.num_running_jobs() >= MAX_CONCURRENT_JOBS:
        return "Busy! try again in a few seconds.", HTTPStatus.SERVICE_UNAVAILABLE

    try:
        _get_config_for_ex(course,ex_type,number)
    except KeyError as ex:
        return "We don't have such a value. " +  str(ex), HTTPStatus.NOT_FOUND
    except SanityError as ex:
        return "<H1>Message to Tutor</H1>There is something wrong in the config file for this exercise.<br>"\
               "Please fix and submit again. <br><strong>Error: " + str(ex) + '</strong>'
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
        uploaded_file_path = _upload_file()
    except _HttpStatusError as e:
        return e.text, e.status_code

    the_reply = "oops. uninitialized variable", 500
    compare_to_golden = False
    try:
        postfix = "GOLD" if compare_to_golden else ""
        reference_output = "./data/{}/ref_{}_{}_output{}".format(course,ex_type,number,postfix)
        reference_input  = "./data/{}/ref_{}_{}_input{}".format(course,ex_type, number, postfix)
        logger.info(" ref files supplied to handler: " + reference_input + "   " + reference_output)
        logger.info("uploaded file: " + uploaded_file_path)
        the_reply = handle_file(uploaded_file_path,course, ex_type, number, reference_input, reference_output,
                               lambda :os.unlink(uploaded_file_path))
    except FileNotFoundError as e:
        logger.error("Internal error. This is probably a race condition: %s", e)

    return the_reply


def _upload_file():
    """ upload homework 'number'
    :return absolute file path of the loaded file or raise
    :note Caller has to remove the temp dir created here
    """
    assert request.method == 'POST'
    file = request.files['file']

    if not(file and allowed_file(file.filename)):
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
    

@app.route('/<int:course>/leaderboard')
def show_leaderboard(course):
    if not str(course) in course_id:
        return "course not found", HTTPStatus.NOT_FOUND
    from .leaderboard import Leaderboard
    board = Leaderboard(_job_status_db)
    return board.show(str(course))


def handle_file(package_under_test,course_number, ex_type, ex_number, reference_input, reference_output, completionCb):
    """Send the file to execution. If async, return immediately"""

    use_async = True
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
       :return tuple(matcher, executor, timeout)

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
     "blocking": true <<<<<<< [FUTURE]optional. default to false
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
    return matcher, executor, timeout


def _check_sanity(comparator_file_name, executor_file_name, timeout):
    """try to catch obvious problems in the parameters.
    :raise  internal error (because it is server side problem)
    """
    if timeout < 1 or timeout > 3000:
        raise SanityError("timeout out of range")

    # check that the file exists and is executable
    import os
    assert app.config['matcher_dir']
    if not os.path.isfile(os.path.join(app.config['matcher_dir'],comparator_file_name)):
        raise SanityError("matcher not found: "+comparator_file_name)
    full_path = os.path.join(app.config['runner_dir'],executor_file_name)
    if not (os.path.isfile(full_path) and os.access(full_path, os.X_OK)):
        raise SanityError("executor not found or not eXcutable: " + executor_file_name)


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
    new_job = _job_status_db.add_job((ex_type, ex_number),package_under_test)
    try:
        comparator, runner, timeout = _get_config_for_ex(course_number, ex_type, ex_number)
    except KeyError as ex:
        return "invalid ex number? exception=%s    "% str(ex),HTTPStatus.BAD_REQUEST

    # convert to full path
    new_job.set_handlers(os.path.join(app.config['matcher_dir'], comparator),
                         os.path.join(app.config['runner_dir'], runner))

    async_task = AsyncChecker(_job_status_db, new_job, package_under_test,
                              reference_input, reference_output, completionCb, timeout_sec=timeout)
    async_task.start()
    return render_template('job_submitted.html', job_id= new_job.job_id)


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


course_id = _get_configured_course_ids()