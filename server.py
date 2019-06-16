# written and tested on linux only
# It will not work on Windows

import sys
import os
from flask import Flask, flash, request, redirect, url_for,render_template
from werkzeug.utils import secure_filename
import subprocess
import logging
_log_path="/logs/"


def in_docker():
    with open('/proc/1/cgroup', 'rt') as ifh:
        return 'docker' in ifh.read()


try:
    if not in_docker():
        _log_path = "/home/noam/data/logs/"
except FileNotFoundError:
    # On windows there is no such file
    _log_path = "./"

# prepare a logger to my liking
logger = logging.getLogger('server')
stream_handler = logging.StreamHandler()
file_handler = logging.FileHandler(filename=_log_path +'homework_checker.log')
logger.setLevel(logging.DEBUG) # for the whole logger
#stream_handler.setLevel(logging.DEBUG) # for each handler (if different from the logger)
#file_handler.setLevel(logging.DEBUG)
log_formatter = logging.Formatter('%(asctime)-15s %(name)s - %(levelname)s - %(message)s')
file_handler.setFormatter(log_formatter)
stream_handler.setFormatter(log_formatter)
logger.addHandler(stream_handler)
logger.addHandler(file_handler)

tmp = open(_log_path+"test","w") # should raise if there is an error
tmp.close()
os.unlink(_log_path+"test")

import job_status
import  show_jobs
from AsyncChecker import AsyncChecker

if sys.version_info.major != 3:
    raise Exception("must use python 3")


logger.debug("TODO: connect logger channel to Azure log viewer!")

UPLOAD_FOLDER = r'/tmp'
ALLOWED_EXTENSIONS = {'gz','xz'}

app = Flask(__name__, template_folder='./templates')
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024
app.secret_key = b'3456o00sdf045'

_job_status_db = job_status.JobStatusDB()


def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


@app.route('/',methods = ['GET'])
def index():
    return render_template('index.html')


@app.route('/jobs')
def show_jobs_():
    """
    create a nice table with all the jobs past and present
    :return: html page
    """
    return show_jobs.show_jobs(_job_status_db)

# noinspection PyPackageRequirements
@app.route('/submit/<ex_type>/<int:number>', methods=['GET', 'POST'])
def upload_file(ex_type, number):
    return _upload_file(ex_type, number)


def _upload_file(ex_type, ex_number, compare_to_golden = False):
    """ upload homework 'number'
        call a checker and return the result.
        Block here until the checker completes.
    """
    if not ex_type in ('lab','hw'):
        return 400, "please use {lab|hw} in the URL"
    if request.method == 'POST':
        # check if the post request has the file part
        if 'file' not in request.files:
            flash('No file part')
            return redirect(request.url)
        file = request.files['file']
        # if user does not select file, browser also
        # submit an empty part without filename
        if file.filename == '':
            flash('No selected file')
            return redirect(request.url)
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            if filename != file.filename:
                return "Please use a valid file name (e.g. ex560.tar.gz)"
            saved_file_name = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            try:
                file.save(saved_file_name)
            except:
                logger.error("Failed saving file=" + saved_file_name)
                raise

            try:
                postfix = "GOLD" if compare_to_golden else ""
                reference_output = "./data/ref_{}_{}_output{}".format(ex_type,ex_number,postfix)
                reference_input  = "./data/ref_{}_{}_input{}".format(ex_type, ex_number, postfix)
                logger.info(" ref files supplied to handler: " + reference_input + "   " + reference_output)
                logger.info("TAR file: " + saved_file_name)
                the_reply = handle_file(saved_file_name,reference_input, reference_output,
                                        lambda :os.unlink(saved_file_name) )
            finally:
                pass
                # the handle_file() is ASYNC, so at this stage we don't know yet when can the file be deleted.
                # MUST do it in a completionCallback
                #os.unlink(saved_file_name)

            return the_reply
            #return redirect(url_for('upload_file', filename=filename))
    return render_template('upload_homework.html', hw_number = ex_number, num_jobs_running=_job_status_db.num_running_jobs())


@app.route('/submit/goldi/<ex_type>/<int:number>', methods=['GET', 'POST'])
def upload_file_golden_ref(ex_type, number):
    return _upload_file(ex_type, number, compare_to_golden=True)


@app.route('/check_job_status/<int:job_id>')
def get_job_stat(job_id):
    try:
        return _job_status_db.get_job_stat(job_id)
    except KeyError:
        return "job id not found", 404
    

@app.route('/leaderboard')
def show_leaderboard():
    import Leaderboard
    board = Leaderboard.Leaderboard(_job_status_db)
    return board.show()

def wrap_html_source(text):
    """
    wrap the text with html tags to force the browser show the code as was created without corrupting it
    """
    if text is None:
        text = "ERROR: got None value!"
    return "<html><pre><code> " + text +  "</code></pre></html>"


def handle_file(package_under_test, reference_input, reference_output, completionCb):
    use_async = True
    if use_async:
        return handle_file_async(package_under_test, reference_input, reference_output,completionCb)
    else:
        rv = handle_file_blocking(package_under_test, reference_input, reference_output)
        if completionCb is not None:
            completionCb()
        return rv
    
    
def handle_file_async(package_under_test, reference_input, reference_output,completionCb):
    """
    handle the supplied file: unpack, build, run, compare to golden reference.
    The operation is async (non blocking). A thread is created to handle the request
    and an entry in a "database" table is created to let the user see the result   
    :param package_under_test: 
    :param reference_input: 
    :param reference_output: 
    :return: html page showing link to the tracking page
    """
    new_job = _job_status_db.add_job(package_under_test)
    async_task = AsyncChecker(_job_status_db, new_job, package_under_test, reference_input, reference_output, completionCb)
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

    return wrap_html_source(message)


if __name__ == '__main__':
    logger.warning("Starting the server as standalone")
    app.run(host="0.0.0.0", port=8000)

