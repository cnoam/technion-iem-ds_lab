# written and tested on linux only
# It will not work on Windows
import sys
if sys.version_info.major != 3:
    raise Exception("must use python 3")

import os
from flask import Flask, flash, request, redirect, url_for,render_template
from werkzeug.utils import secure_filename
import subprocess

UPLOAD_FOLDER = './tmp'
ALLOWED_EXTENSIONS = {'gz', 'zip'}

app = Flask(__name__, template_folder='./templates')
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024
app.secret_key = b'3456o00sdf045'

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/',methods = ['GET'])
def index():
    return render_template('index.html')

@app.route('/submit/hw/<int:number>', methods=['GET', 'POST'])
def upload_file(number):
    """ upload homework 'number'
        call a checker and return the result.
        Block here until the checker completes.
    """
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
            file.save(saved_file_name)

            try:
                the_reply =  handle_file(saved_file_name,number)
            finally:
                os.unlink(saved_file_name)
            return  the_reply
            #return redirect(url_for('upload_file', filename=filename))
    return render_template('upload_homework.html', hw_number = number)

def wrap_html_source(text):
    """
    wrap the text with html tags to force the browser show the code as was created without corrupting it
    """

    return "<html><pre><code> " + text +  "</code></pre></html>"


def handle_file(file_name, ex_number):
    """
    :param file_name: homework that need to be checked
    :param ex_number homework exercise number
    :return: html doc with the result and maybe an explanation
    """
    timeout = 10
    completed_proc = None
    try:
        reference_output = "./data/ref_" + str(ex_number)+"_output"
        reference_input  = "./data/ref_"+ str(ex_number)+"_input"
        print("ref files:  "+reference_input+","+reference_output)
        #  https://medium.com/@mccode/understanding-how-uid-and-gid-work-in-docker-containers-c37a01d01cf
        completed_proc = subprocess.run( ['./checker.sh',file_name, reference_input, reference_output], check=False, stdout=subprocess.PIPE, stderr=subprocess.PIPE,timeout=timeout)
	#        print(completed_proc.stdout)
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
   app.run(host="0.0.0.0", port=80)

