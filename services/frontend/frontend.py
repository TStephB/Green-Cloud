from flask import Flask, render_template, jsonify, request, redirect, url_for, session
import requests
import os

app = Flask(__name__, template_folder="templates", static_folder="static")
app.secret_key = 'your_secret_key'  # Replace with a secure key in production

# Config: service URLs (you can later move this to a config file)
SERVICE_URLS = {
    'sensors': 'http://sensor-visualizer:5000',
    'ml_control': 'http://ml-controller:5000',
    'manual_control': 'http://fan-controller:5000',
    'workflow': 'http://data-collector:5000',
    'load_sim': 'http://workload-tester:5000',
    'greenmeter': 'http://green-meter:5000',
    'feed': 'http://data-collector:5000'
}

@app.before_request
def restrict_access():
    public_paths = {'/login', '/register', '/static/', '/favicon.ico'}
    if not session.get('username') and not any(request.path.startswith(path) for path in public_paths):
        return redirect(url_for('login'))

@app.route('/')
def index():
    if 'username' in session:
        return redirect(url_for('feed'))
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    message = ''
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        try:
            response = requests.post(f"{SERVICE_URLS['feed']}/login", json={"username": username, "password": password})
            if response.status_code == 200:
                session['username'] = username
                return redirect(url_for('feed'))
            else:
                message = 'Invalid credentials'
        except:
            message = 'Auth service unavailable'
    return render_template('login.html', title="Login", message=message)

@app.route('/register', methods=['GET', 'POST'])
def register():
    message = ''
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        try:
            response = requests.post(f"{SERVICE_URLS['feed']}/register", json={"username": username, "password": password})
            if response.status_code == 201:
                return redirect(url_for('login'))
            else:
                message = 'Username already exists'
        except:
            message = 'Registration service unavailable'
    return render_template('register.html', title="Register", message=message)

@app.route('/logout')
def logout():
    session.pop('username', None)
    return redirect(url_for('login'))

@app.route('/sensors')
def sensors():
    try:
        response = requests.get(f"{SERVICE_URLS['sensors']}/data")
        data = response.json()
    except:
        data = {'error': 'Could not fetch sensor data'}
    return render_template('sensors.html', title="Sensors", data=data)

@app.route('/ml-control')
def ml_control():
    try:
        response = requests.get(f"{SERVICE_URLS['ml_control']}/status")
        data = response.json()
    except:
        data = {'error': 'ML service not available'}
    return render_template('ml_control.html', title="ML Control", data=data)

@app.route('/manual-control', methods=['GET', 'POST'])
def manual_control():
    message = None
    if request.method == 'POST':
        speed = request.form.get('speed')
        try:
            requests.post(f"{SERVICE_URLS['manual_control']}/set_speed", json={'speed': speed})
            message = 'Fan speed updated.'
        except:
            message = 'Failed to update speed.'
    return render_template('manual_control.html', title="Manual Fan Control", message=message)

@app.route('/workflow')
def workflow():
    try:
        response = requests.get(f"{SERVICE_URLS['workflow']}/metrics")
        data = response.json()
    except:
        data = {'error': 'Workflow data not available'}
    return render_template('workflow.html', title="User Workflow", data=data)

@app.route('/load')
def load():
    try:
        requests.get(f"{SERVICE_URLS['load_sim']}/start")
        msg = 'Load simulation started.'
    except:
        msg = 'Failed to start load simulation.'
    return render_template('load_simulator.html', title="Load Simulator", message=msg)

@app.route('/greenmeter')
def greenmeter():
    try:
        response = requests.get(f"{SERVICE_URLS['greenmeter']}/score")
        data = response.json()
    except:
        data = {'error': 'Greenmeter unavailable'}
    return render_template('greenmeter.html', title="GreenMeter", data=data)

@app.route('/feed', methods=['GET', 'POST'])
def feed():
    message = ''
    if request.method == 'POST':
        text = request.form.get('post_text')
        try:
            response = requests.post(f"{SERVICE_URLS['feed']}/post", json={"username": session['username'], "text": text})
            if response.status_code != 201:
                message = 'Failed to post update'
        except:
            message = 'Posting service unavailable'
    try:
        response = requests.get(f"{SERVICE_URLS['feed']}/posts")
        posts = response.json()
    except:
        posts = []
    return render_template('feed.html', title="Feed", posts=posts, message=message)

if __name__ == '__main__':
    os.makedirs("templates", exist_ok=True)
    os.makedirs("static", exist_ok=True)

    base_template = '''
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{{ title }}</title>
  <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
</head>
<body>
  {% if session.get('username') %}
  <nav class="navbar navbar-expand-lg navbar-dark bg-dark">
    <div class="container-fluid">
      <a class="navbar-brand" href="/">Mini Data Center</a>
      <div class="collapse navbar-collapse">
        <ul class="navbar-nav me-auto mb-2 mb-lg-0">
          <li class="nav-item"><a class="nav-link" href="/sensors">Sensors</a></li>
          <li class="nav-item"><a class="nav-link" href="/ml-control">ML Control</a></li>
          <li class="nav-item"><a class="nav-link" href="/manual-control">Manual Control</a></li>
          <li class="nav-item"><a class="nav-link" href="/workflow">Workflow</a></li>
          <li class="nav-item"><a class="nav-link" href="/load">Load Test</a></li>
          <li class="nav-item"><a class="nav-link" href="/greenmeter">GreenMeter</a></li>
          <li class="nav-item"><a class="nav-link" href="/feed">Feed</a></li>
          <li class="nav-item"><a class="nav-link" href="/logout">Logout ({{ session['username'] }})</a></li>
        </ul>
      </div>
    </div>
  </nav>
  {% endif %}
  <div class="container mt-4">
    {% block content %}{% endblock %}
  </div>
</body>
</html>'''

    with open("templates/base.html", "w") as f:
        f.write(base_template)

    for name in ["sensors", "ml_control", "manual_control", "workflow", "load_simulator", "greenmeter"]:
        with open(f"templates/{name}.html", "w") as f:
            f.write(f"""{{% extends 'base.html' %}}
{{% block content %}}
<h1>{name.replace('_', ' ').title()}</h1>
<p>This is a placeholder page for {name}.</p>
{{% endblock %}}
""")

    feed_template = '''
{% extends 'base.html' %}
{% block content %}
<h1>Feed</h1>
{% if message %}<div class="alert alert-warning">{{ message }}</div>{% endif %}
<form method="POST">
  <div class="mb-3">
    <textarea name="post_text" class="form-control" placeholder="What's on your mind?" rows="3"></textarea>
  </div>
  <button type="submit" class="btn btn-primary">Post</button>
</form>
<hr>
{% for post in posts %}
  <div class="card mb-2">
    <div class="card-body">
      <h6 class="card-subtitle mb-2 text-muted">{{ post.username }}</h6>
      <p class="card-text">{{ post.text }}</p>
    </div>
  </div>
{% endfor %}
{% endblock %}'''

    with open("templates/feed.html", "w") as f:
        f.write(feed_template)

    login_template = '''
{% extends 'base.html' %}
{% block content %}
<div class="row justify-content-center">
  <div class="col-md-6">
    <h2 class="mb-4">Login</h2>
    {% if message %}<div class="alert alert-danger">{{ message }}</div>{% endif %}
    <form method="POST">
      <div class="mb-3">
        <label for="username" class="form-label">Username</label>
        <input type="text" class="form-control" name="username" required>
      </div>
      <div class="mb-3">
        <label for="password" class="form-label">Password</label>
        <input type="password" class="form-control" name="password" required>
      </div>
      <button type="submit" class="btn btn-primary">Login</button>
      <p class="mt-3">Don't have an account? <a href="/register">Register here</a>.</p>
    </form>
  </div>
</div>
{% endblock %}'''

    with open("templates/login.html", "w") as f:
        f.write(login_template)

    register_template = '''
{% extends 'base.html' %}
{% block content %}
<div class="row justify-content-center">
  <div class="col-md-6">
    <h2 class="mb-4">Register</h2>
    {% if message %}<div class="alert alert-danger">{{ message }}</div>{% endif %}
    <form method="POST">
      <div class="mb-3">
        <label for="username" class="form-label">Username</label>
        <input type="text" class="form-control" name="username" required>
      </div>
      <div class="mb-3">
        <label for="password" class="form-label">Password</label>
        <input type="password" class="form-control" name="password" required>
      </div>
      <button type="submit" class="btn btn-success">Register</button>
      <p class="mt-3">Already have an account? <a href="/login">Login here</a>.</p>
    </form>
  </div>
</div>
{% endblock %}'''

    with open("templates/register.html", "w") as f:
        f.write(register_template)

    app.run(host='0.0.0.0', port=5000)
