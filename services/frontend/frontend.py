from flask import Flask, render_template, request, redirect, url_for, session, Response, jsonify
import os
import requests
from typing import Optional, Union

# Configuration Constants
DEFAULT_SECRET_KEY = 'your_secret_key'
DEFAULT_RUN_MODE = 'local'
DEFAULT_PORT = 5000

app = Flask(__name__, template_folder="templates", static_folder="static")
app.secret_key = os.getenv('SECRET_KEY', DEFAULT_SECRET_KEY)

# Service Configuration
RUN_MODE = os.getenv("RUN_MODE", DEFAULT_RUN_MODE)  # "local" or "docker"
SERVICE_URLS = {
    'sensors':        os.getenv("SENSORS_URL",        'http://localhost:5002') if RUN_MODE == "local" else 'http://sensor-visualizer:5000',
    'ml_control':     os.getenv("ML_CONTROL_URL",     'http://localhost:5003') if RUN_MODE == "local" else 'http://ml-controller:5000',
    'manual_control': os.getenv("MANUAL_CONTROL_URL", 'http://localhost:5004') if RUN_MODE == "local" else 'http://fan-controller:5000',
    'greenmeter':     os.getenv("GREENMETER_URL",     'http://localhost:5006') if RUN_MODE == "local" else 'http://green-meter:5000',
    'feed':           os.getenv("FEED_URL",           'http://localhost:5001') if RUN_MODE == "local" else 'http://data-collector:5000',
    'workload_tester':os.getenv("WORKLOAD_TESTER_URL", 'http://localhost:5005') if RUN_MODE == "local" else 'http://workload-tester:5000',
}

@app.before_request
def restrict_access() -> Optional[Response]:
    public_paths = {'/login', '/register', '/static/', '/favicon.ico'}
    if not session.get('username') and not any(request.path.startswith(path) for path in public_paths):
        return redirect(url_for('login'))

@app.route('/')
def index():
    return redirect(url_for('feed')) if 'username' in session else redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login() -> Union[str, Response]:
    message = ''
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '').strip()
        if username == 'admin' and password == 'admin':
            session['username'] = username
            return redirect(url_for('feed'))
        if not username or not password:
            message = 'Username and password are required'
        else:
            try:
                resp = requests.post(f"{SERVICE_URLS['feed']}/login",
                                     json={'username': username, 'password': password},
                                     timeout=5)
                if resp.status_code == 200:
                    session['username'] = username
                    return redirect(url_for('feed'))
                message = 'Invalid credentials'
            except requests.exceptions.RequestException as e:
                message = f'Authentication service error: {e}'
    return render_template('login.html', title='Login', message=message)

@app.route('/register', methods=['GET', 'POST'])
def register() -> Union[str, Response]:
    message = ''
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '').strip()
        if not username or not password:
            message = 'Username and password are required'
        elif len(username) < 4 or len(password) < 6:
            message = 'Username must be at least 4 characters and password 6 characters'
        else:
            try:
                resp = requests.post(f"{SERVICE_URLS['feed']}/register",
                                     json={'username': username, 'password': password},
                                     timeout=5)
                if resp.status_code == 201:
                    return redirect(url_for('login'))
                message = 'Username already exists' if resp.status_code == 409 else 'Registration failed'
            except requests.exceptions.RequestException as e:
                message = f'Registration service error: {e}'
    return render_template('register.html', title='Register', message=message)

@app.route('/logout')
def logout() -> Response:
    session.pop('username', None)
    return redirect(url_for('login'))

@app.route('/sensors')
def sensors() -> str:
    try:
        resp = requests.get(f"{SERVICE_URLS['sensors']}/data", timeout=5)
        resp.raise_for_status()
        data = resp.json()
    except requests.exceptions.RequestException as e:
        data = {'error': f'Sensor service error: {e}'}
    return render_template('sensors.html', title='Sensors', data=data)

@app.route('/ml-control')
def ml_control() -> str:
    try:
        resp = requests.get(f"{SERVICE_URLS['ml_control']}/status", timeout=5)
        resp.raise_for_status()
        data = resp.json()
    except requests.exceptions.RequestException as e:
        data = {'error': f'ML service error: {e}'}
    return render_template('ml_control.html', title='ML Control', data=data)

@app.route('/manual-control', methods=['GET', 'POST'])
def manual_control() -> str:
    message = None
    if request.method == 'POST':
        try:
            speed = int(request.form.get('speed', '0'))
            if not 0 <= speed <= 100:
                message = 'Speed must be between 0 and 100'
            else:
                try:
                    resp = requests.post(f"{SERVICE_URLS['manual_control']}/set_speed",
                                         json={'speed': speed}, timeout=5)
                    resp.raise_for_status()
                    message = 'Fan speed updated successfully'
                except requests.exceptions.RequestException as e:
                    message = f'Failed to update speed: {e}'
        except ValueError:
            message = 'Invalid speed - must be a number'
    return render_template('manual_control.html', title='Manual Fan Control', message=message)

@app.route('/greenmeter')
def greenmeter() -> str:
    try:
        resp = requests.get(f"{SERVICE_URLS['greenmeter']}/score", timeout=5)
        resp.raise_for_status()
        data = resp.json()
    except requests.exceptions.RequestException as e:
        data = {'error': f'Greenmeter service error: {e}'}
    return render_template('greenmeter.html', title='GreenMeter', data=data)

@app.route('/feed', methods=['GET', 'POST'])
def feed() -> str:
    message = ''
    if request.method == 'POST':
        text = request.form.get('post_text', '').strip()
        if not text:
            message = 'Post text cannot be empty'
        else:
            try:
                resp = requests.post(f"{SERVICE_URLS['feed']}/post", json={'username': session['username'], 'text': text}, timeout=5)
                if resp.status_code != 201:
                    message = f'Failed to post update: {resp.text}'
            except requests.exceptions.RequestException as e:
                message = f'Posting service error: {e}'
    try:
        resp = requests.get(f"{SERVICE_URLS['feed']}/posts", timeout=5)
        resp.raise_for_status()
        posts = resp.json()
    except requests.exceptions.RequestException as e:
        posts = []
        message = message or f'Failed to load posts: {e}'
    return render_template('feed.html', title='Feed', posts=posts, message=message)

@app.route('/workload')
def workload() -> str:
    return render_template('workflow.html', title='Workload Simulator')

@app.route('/start', methods=['POST'])
def proxy_start():
    try:
        resp = requests.post(f"{SERVICE_URLS['workload_tester']}/start", json=request.get_json(), timeout=10)
        return Response(resp.content, status=resp.status_code, content_type=resp.headers.get('Content-Type'))
    except requests.exceptions.RequestException as e:
        return jsonify({'error': f'Workload tester error: {e}'}), 503

@app.route('/stop', methods=['POST'])
def proxy_stop():
    try:
        resp = requests.post(f"{SERVICE_URLS['workload_tester']}/stop", timeout=10)
        return Response(resp.content, status=resp.status_code, content_type=resp.headers.get('Content-Type'))
    except requests.exceptions.RequestException as e:
        return jsonify({'error': f'Workload tester error: {e}'}), 503

@app.route('/status', methods=['GET'])
def proxy_status():
    try:
        resp = requests.get(f"{SERVICE_URLS['workload_tester']}/status", timeout=10)
        return Response(resp.content, status=resp.status_code, content_type=resp.headers.get('Content-Type'))
    except requests.exceptions.RequestException as e:
        return jsonify({'error': f'Workload tester error: {e}'}), 503

if __name__ == '__main__':
    os.makedirs("templates", exist_ok=True)
    os.makedirs("static", exist_ok=True)
    app.run(host='0.0.0.0', port=5000, debug=True)

