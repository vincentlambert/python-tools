from flask import Flask, request
import platform

# If `entrypoint` is not defined in app.yaml, App Engine will look for an app
# called `app` in `main.py`.
app = Flask(__name__)


@app.route('/')
def index():
    """Return User IP address."""
    if request.environ.get('HTTP_X_FORWARDED_FOR') is None:
        print('here')
        return request.environ['REMOTE_ADDR']
    else:
        print('there')
        return request.environ['HTTP_X_FORWARDED_FOR']


@app.route('/version')
def version():
    """Return Python version."""
    return platform.python_version()


if __name__ == '__main__':
    # This is used when running locally only. When deploying to Google App
    # Engine, a webserver process such as Gunicorn will serve the app. This
    # can be configured by adding an `entrypoint` to app.yaml.
    app.run(host='0.0.0.0', port=8080, debug=True)
