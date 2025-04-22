from flask import Flask, render_template, request, redirect, url_for, session
import requests
import os



app = Flask(__name__, template_folder="templates", static_folder="static")
app.secret_key = os.getenv('SECRET_KEY', 'your_secret_key')

# Configuration des microservices (URL interne ou localhost selon usage Docker ou local)
RUN_MODE = os.getenv("RUN_MODE", "local")  # "local" or "docker"

SERVICE_URLS = {
    'sensors': os.getenv("SENSORS_URL", 'http://localhost:5002') if RUN_MODE == "local" else 'http://sensor-visualizer:5000',
    'ml_control': os.getenv("ML_CONTROL_URL", 'http://localhost:5003') if RUN_MODE == "local" else 'http://ml-controller:5000',
    'manual_control': os.getenv("MANUAL_CONTROL_URL", 'http://localhost:5004') if RUN_MODE == "local" else 'http://fan-controller:5000',
    'workflow': os.getenv("WORKFLOW_URL", 'http://localhost:5001') if RUN_MODE == "local" else 'http://data-collector:5000',
    'load_sim': os.getenv("LOAD_SIM_URL", 'http://localhost:5005') if RUN_MODE == "local" else 'http://workload-tester:5000',
    'greenmeter': os.getenv("GREENMETER_URL", 'http://localhost:5006') if RUN_MODE == "local" else 'http://green-meter:5000',
    'feed': os.getenv("FEED_URL", 'http://localhost:5001') if RUN_MODE == "local" else 'http://data-collector:5000',
}


# 🔐 Middleware de restriction d’accès
@app.before_request
def restrict_access():
    public_paths = {'/login', '/register', '/static/', '/favicon.ico'}
    if not session.get('username') and not any(request.path.startswith(path) for path in public_paths):
        return redirect(url_for('login'))

# 🏠 Page d’accueil
@app.route('/')
def index():
    return redirect(url_for('feed')) if 'username' in session else redirect(url_for('login'))

# 🔑 Connexion
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
            message = 'Invalid credentials'
        except Exception:
            message = 'Auth service unavailable'
    return render_template('login.html', title="Login", message=message)

# 📝 Inscription
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
            message = 'Username already exists'
        except:
            message = 'Registration service unavailable'
    return render_template('register.html', title="Register", message=message)

# 🔓 Déconnexion
@app.route('/logout')
def logout():
    session.pop('username', None)
    return redirect(url_for('login'))

# 📡 Données capteurs
@app.route('/sensors')
def sensors():
    try:
        response = requests.get(f"{SERVICE_URLS['sensors']}/data")
        data = response.json()
    except:
        data = {'error': 'Could not fetch sensor data'}
    return render_template('sensors.html', title="Sensors", data=data)

# 🧠 Statut du contrôleur ML
@app.route('/ml-control')
def ml_control():
    try:
        response = requests.get(f"{SERVICE_URLS['ml_control']}/status")
        data = response.json()
    except:
        data = {'error': 'ML service not available'}
    return render_template('ml_control.html', title="ML Control", data=data)

# 🌀 Contrôle manuel des ventilateurs
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

# 📈 Données de workflow
@app.route('/workflow')
def workflow():
    try:
        response = requests.get(f"{SERVICE_URLS['workflow']}/metrics")
        data = response.json()
    except:
        data = {'error': 'Workflow data not available'}
    return render_template('workflow.html', title="User Workflow", data=data)

# ⚙️ Simulateur de charge
@app.route('/load')
def load():
    try:
        requests.get(f"{SERVICE_URLS['load_sim']}/start")
        msg = 'Load simulation started.'
    except:
        msg = 'Failed to start load simulation.'
    return render_template('load_simulator.html', title="Load Simulator", message=msg)

# 🌱 GreenMeter
@app.route('/greenmeter')
def greenmeter():
    try:
        response = requests.get(f"{SERVICE_URLS['greenmeter']}/score")
        data = response.json()
    except:
        data = {'error': 'Greenmeter unavailable'}
    return render_template('greenmeter.html', title="GreenMeter", data=data)

# 📣 Feed (interface seule)
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

# 🧪 Lancement local
if __name__ == '__main__':
    os.makedirs("templates", exist_ok=True)
    os.makedirs("static", exist_ok=True)
    app.run(host='0.0.0.0', port=5000, debug=True)
