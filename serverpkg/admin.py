
from flask import Flask, render_template, request, url_for, flash
from flask_login import LoginManager, login_user, logout_user, login_required
from werkzeug.utils import redirect, secure_filename
from flask_login import UserMixin
from http import HTTPStatus
from serverpkg import app, logger

login_manager = LoginManager()
login_manager.init_app(app)

# already in __init__ app.config['SECRET_KEY'] = "k490sk6257s" # a random string that will be used to sign cookies by flask


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
    with open('hw_settings.json','r') as fin:
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
        file_name = "hw_settings.json"
        try:
            file.save(file_name)
        except OSError as ex:
            logger.error("Failed saving file=" + file_name, ex)
            raise

