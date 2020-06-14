"""
Admin pages are placed in this module.
It is loaded from the server module.
"""
from http import HTTPStatus
from flask import render_template, request, url_for, flash
from flask_login import LoginManager, login_user, logout_user, login_required
from werkzeug.utils import redirect
from flask_login import UserMixin

from . server import app, logger

login_manager = LoginManager()
login_manager.init_app(app)


class User(UserMixin):
    def __init__(self):
        self.username = 'admin'
        self.password = 'pass'
        self.id = "77"


the_single_user = User()

@login_manager.user_loader
def load_user(user_id):
    return the_single_user if user_id == the_single_user.id else None


@app.route('/login', methods = ['GET','POST'])
def login():
    error = None
    if request.method == 'POST':
        user = User()
        if request.form['username'] != user.username or request.form['password'] != user.password:
            error = 'Invalid Credentials. Please try again.'
        else:
            login_user(user, remember=True)
            return redirect(url_for('index'))
    return render_template('login.html',error=error)


@app.route('/logout')
@login_required
def logout():
    logout_user()
    return "logged out"


@app.route("/admin", methods=['GET', 'POST'])
@login_required
def admin_page():
    if request.method == 'POST':
        _upload_and_save()
    return render_template('admin.html')


@app.route("/admin/show_ex_config")
def show_ex_config():
    with open(app.config['assignment_config_file'],'r') as fin:
        contents = fin.read()
    return render_template('dump_source_code.html', source = contents)


def _upload_and_save():
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
    if file:
        file_name = app.config['assignment_config_file']
        try:
            file.save(file_name)
        except OSError as ex:
            logger.error("Failed saving file=" + file_name, ex)
            raise


@app.route("/purge", methods=['GET'])
@login_required
def purge_completed_jobs():
    """ test the db deletion of matching rows"""
    from .server import _job_status_db
    from .job_status import Job
    _job_status_db.delete_jobs(Job.Status.completed)
    flash('deleted completed jobs (if any)')
    return '', HTTPStatus.OK


@app.route("/purge/failed", methods=['GET'])
@login_required
def purge_failed_jobs():
    """ test the db deletion of matching rows"""
    from .server import _job_status_db
    from .job_status import Job
    _job_status_db.delete_jobs(Job.Status.failed)
    flash('deleted failed jobs (if any)')
    return '', HTTPStatus.OK

@app.route("/jobs_as_csv", methods=['GET'])
@login_required
def get_job_results():
    import re
    import datetime
    from .server import _job_status_db
    from .server_codes import ExitCode

    csv_output = "Date,ID , status,exit code\n"
    for j in _job_status_db.jobs().values():
        # matches = re.findall(r"(\d{8,9})_(\d{8,9})", j.filename)
        exit_code = j.exit_code
        if j.exit_code in ExitCode.values():
            exit_code = ExitCode(j.exit_code).name
        matches = j.filename.split('_')
        if len(matches)==0 :
            csv_output += "0, %s\n" % j.status.name
        else:
            for id in matches:
                if len(id)>7: # It's ID
                    csv_output += "%s,%s,%s, %s\n" % (datetime.datetime.now(),id, j.status.name,exit_code)
            # (id1, id2) = matches[0]
            # csv_output += "%s, %s\n%s, %s\n" % (id1,j.status.name, id2, j.status.name )

    from flask import make_response
    resp = make_response(csv_output)
    resp.headers['Content-Type'] = 'text/plain'
    return resp
