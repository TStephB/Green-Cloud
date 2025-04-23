from flask import Flask, render_template, request, redirect, url_for, session
import os
import requests
from typing import Dict, Any, Optional, Union

# Configuration Constants
DEFAULT_SECRET_KEY = 'your_secret_key'
DEFAULT_RUN_MODE = 'local'
DEFAULT_PORT = 5000

app = Flask(__name__, template_folder="templates", static_folder="static")
app.secret_key = os.getenv('SECRET_KEY', DEFAULT_SECRET_KEY)

# Service Configuration
RUN_MODE = os.getenv("RUN_MODE", DEFAULT_RUN_MODE)  # "local" or "docker"

SERVICE_URLS = {
    'sensors': os.getenv("SENSORS_URL", 'http://localhost:5002') if RUN_MODE == "local" else 'http://sensor-visualizer:5000',
    'ml_control': os.getenv("ML_CONTROL_URL", 'http://localhost:5003') if RUN_MODE == "local" else 'http://ml-controller:5000',
    'manual_control': os.getenv("MANUAL_CONTROL_URL", 'http://localhost:5004') if RUN_MODE == "local" else 'http://fan-controller:5000',
    'workflow': os.getenv("WORKFLOW_URL", 'http://localhost:5001') if RUN_MODE == "local" else 'http://data-collector:5000',
    'load_sim': os.getenv("LOAD_SIM_URL", 'http://localhost:5005') if RUN_MODE == "local" else 'http://workload-tester:5000',
    'greenmeter': os.getenv("GREENMETER_URL", 'http://localhost:5006') if RUN_MODE == "local" else 'http://green-meter:5000',
    'feed': os.getenv("FEED_URL", 'http://localhost:5001') if RUN_MODE == "local" else 'http://data-collector:5000',
}


@app.before_request
def restrict_access() -> Optional[Any]:
    """Middleware to restrict access to protected routes.
    
    Checks if user is authenticated before allowing access to protected routes.
    Public paths are exempt from this check.
    
    Returns:
        Optional[Any]: Flask redirect response if not authenticated, None otherwise
    """
    public_paths = {'/login', '/register', '/static/', '/favicon.ico'}
    if not session.get('username') and not any(request.path.startswith(path) for path in public_paths):
        return redirect(url_for('login'))

# 🏠 Page d’accueil
@app.route('/')
def index():
    return redirect(url_for('feed')) if 'username' in session else redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login() -> Union[str, Any]:
    """Handle user login requests.
    
    Processes both GET (show form) and POST (process submission) requests.
    Includes temporary admin bypass for development purposes.
    
    Returns:
        Union[str, Any]: Rendered template or redirect response
    """
    message = ''
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '').strip()
        
        # TEMPORARY LOGIN BYPASS (remove in production)
        if username == "admin" and password == "admin":
            session['username'] = username
            return redirect(url_for('feed'))

        if not username or not password:
            message = 'Username and password are required'
        else:
            try:
                response = requests.post(
                    f"{SERVICE_URLS['feed']}/login",
                    json={"username": username, "password": password},
                    timeout=5
                )
                if response.status_code == 200:
                    session['username'] = username
                    return redirect(url_for('feed'))
                message = 'Invalid credentials'
            except requests.exceptions.RequestException as e:
                message = f'Authentication service error: {str(e)}'
            except ValueError:
                message = 'Invalid response from authentication service'
                
    return render_template('login.html', title="Login", message=message)

@app.route('/register', methods=['GET', 'POST'])
def register() -> Union[str, Any]:
    """Handle user registration requests.
    
    Processes both GET (show form) and POST (process submission) requests.
    Validates input and communicates with registration service.
    
    Returns:
        Union[str, Any]: Rendered template or redirect response
    """
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
                response = requests.post(
                    f"{SERVICE_URLS['feed']}/register",
                    json={"username": username, "password": password},
                    timeout=5
                )
                if response.status_code == 201:
                    return redirect(url_for('login'))
                message = 'Username already exists' if response.status_code == 409 else 'Registration failed'
            except requests.exceptions.RequestException as e:
                message = f'Registration service error: {str(e)}'
            except ValueError:
                message = 'Invalid response from registration service'
                
    return render_template('register.html', title="Register", message=message)

@app.route('/logout')
def logout() -> Any:
    """Handle user logout requests.
    
    Clears the user session and redirects to login page.
    
    Returns:
        Any: Flask redirect response to login page
    """
    session.pop('username', None)
    return redirect(url_for('login'))

@app.route('/sensors')
def sensors() -> str:
    """Fetch and display sensor data.
    
    Retrieves sensor data from the sensor service and renders it in the template.
    Handles service errors gracefully with appropriate error messages.
    
    Returns:
        str: Rendered template with sensor data or error message
    """
    try:
        response = requests.get(
            f"{SERVICE_URLS['sensors']}/data",
            timeout=5
        )
        response.raise_for_status()  # Raises HTTPError for bad responses
        data = response.json()
    except requests.exceptions.RequestException as e:
        data = {'error': f'Sensor service error: {str(e)}'}
    except ValueError:
        data = {'error': 'Invalid sensor data format'}
        
    return render_template('sensors.html', title="Sensors", data=data)

@app.route('/ml-control')
def ml_control() -> str:
    """Fetch and display ML controller status.
    
    Retrieves status information from the ML controller service and renders it.
    Handles service errors gracefully with appropriate error messages.
    
    Returns:
        str: Rendered template with ML controller status or error message
    """
    try:
        response = requests.get(
            f"{SERVICE_URLS['ml_control']}/status",
            timeout=5
        )
        response.raise_for_status()
        data = response.json()
    except requests.exceptions.RequestException as e:
        data = {'error': f'ML service error: {str(e)}'}
    except ValueError:
        data = {'error': 'Invalid ML service response format'}
        
    return render_template('ml_control.html', title="ML Control", data=data)

@app.route('/manual-control', methods=['GET', 'POST'])
def manual_control() -> str:
    """Handle manual fan control requests.
    
    Processes both GET (show form) and POST (set speed) requests.
    Validates speed input and communicates with fan controller service.
    
    Returns:
        str: Rendered template with status message
    """
    message = None
    if request.method == 'POST':
        try:
            speed = int(request.form.get('speed', '0'))
            if not 0 <= speed <= 100:
                message = 'Speed must be between 0 and 100'
            else:
                try:
                    response = requests.post(
                        f"{SERVICE_URLS['manual_control']}/set_speed",
                        json={'speed': speed},
                        timeout=5
                    )
                    response.raise_for_status()
                    message = 'Fan speed updated successfully'
                except requests.exceptions.RequestException as e:
                    message = f'Failed to update speed: {str(e)}'
        except ValueError:
            message = 'Invalid speed value - must be a number'
            
    return render_template('manual_control.html', title="Manual Fan Control", message=message)

@app.route('/workflow')
def workflow() -> str:
    """Fetch and display workflow metrics.
    
    Retrieves workflow metrics from the data collector service and renders them.
    Handles service errors gracefully with appropriate error messages.
    
    Returns:
        str: Rendered template with workflow metrics or error message
    """
    try:
        response = requests.get(
            f"{SERVICE_URLS['workflow']}/metrics",
            timeout=5
        )
        response.raise_for_status()
        data = response.json()
    except requests.exceptions.RequestException as e:
        data = {'error': f'Workflow service error: {str(e)}'}
    except ValueError:
        data = {'error': 'Invalid workflow data format'}
        
    return render_template('workflow.html', title="User Workflow", data=data)

@app.route('/load')
def load() -> str:
    """Start load simulation and display status.
    
    Triggers load simulation via the workload tester service.
    Handles service errors gracefully with appropriate error messages.
    
    Returns:
        str: Rendered template with simulation status message
    """
    try:
        response = requests.get(
            f"{SERVICE_URLS['load_sim']}/start",
            timeout=5
        )
        response.raise_for_status()
        msg = 'Load simulation started successfully'
    except requests.exceptions.RequestException as e:
        msg = f'Failed to start load simulation: {str(e)}'
        
    return render_template('load_simulator.html', title="Load Simulator", message=msg)

@app.route('/greenmeter')
def greenmeter() -> str:
    """Fetch and display green performance metrics.
    
    Retrieves energy efficiency score from the green meter service.
    Handles service errors gracefully with appropriate error messages.
    
    Returns:
        str: Rendered template with green metrics or error message
    """
    try:
        response = requests.get(
            f"{SERVICE_URLS['greenmeter']}/score",
            timeout=5
        )
        response.raise_for_status()
        data = response.json()
    except requests.exceptions.RequestException as e:
        data = {'error': f'Greenmeter service error: {str(e)}'}
    except ValueError:
        data = {'error': 'Invalid greenmeter data format'}
        
    return render_template('greenmeter.html', title="GreenMeter", data=data)

@app.route('/feed', methods=['GET', 'POST'])
def feed() -> str:
    """Handle feed display and post creation.
    
    Processes both GET (show feed) and POST (create post) requests.
    Validates input and communicates with feed service.
    
    Returns:
        str: Rendered template with feed posts and status message
    """
    message = ''
    if request.method == 'POST':
        text = request.form.get('post_text', '').strip()
        if not text:
            message = 'Post text cannot be empty'
        else:
            try:
                response = requests.post(
                    f"{SERVICE_URLS['feed']}/post",
                    json={"username": session['username'], "text": text},
                    timeout=5
                )
                if response.status_code != 201:
                    message = f'Failed to post update: {response.text}'
            except requests.exceptions.RequestException as e:
                message = f'Posting service error: {str(e)}'
    
    try:
        response = requests.get(
            f"{SERVICE_URLS['feed']}/posts",
            timeout=5
        )
        response.raise_for_status()
        posts = response.json()
    except requests.exceptions.RequestException as e:
        posts = []
        message = f'Failed to load posts: {str(e)}' if not message else message
    except ValueError:
        posts = []
        message = 'Invalid post data format' if not message else message
        
    return render_template('feed.html', title="Feed", posts=posts, message=message)

# 🧪 Lancement local
if __name__ == '__main__':
    os.makedirs("templates", exist_ok=True)
    os.makedirs("static", exist_ok=True)
    app.run(host='0.0.0.0', port=5000, debug=True)
