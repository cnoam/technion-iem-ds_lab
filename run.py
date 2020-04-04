#!/usr/bin/env python3

# To run with test web server: python run.py

from serverpkg.server import app

# see https://help.pythonanywhere.com/pages/Flask/

# NOTE: if calling app.run(... debug=True) , the app is restarted (sort of?) and there are TWO instances of the scheduled jobs.
if __name__ == '__main__':
    LISTENING_PORT = 8000
    use_http = True
    app.run(host='0.0.0.0', port=LISTENING_PORT, debug=True, ssl_context = None if use_http else 'adhoc')
