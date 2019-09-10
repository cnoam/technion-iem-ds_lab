from flask import render_template
from flask import Flask, render_template, request, url_for
from flask_login import LoginManager, login_user, logout_user, login_required
from werkzeug.utils import redirect
from flask_login import UserMixin
from serverpkg import app

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


@app.route("/admin")
@login_required
def admin_page():
    return render_template('admin.html')