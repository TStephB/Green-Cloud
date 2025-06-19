from flask import Flask, request, jsonify
import threading
import time
import random
import string

app = Flask(__name__)

simulation = {
    'running': False,
    'user_count': 0,
    'post_rate': 0,       # posts per minute
    'post_length': 0,
    'duration': 0,        # minutes
    'random_users': True,
    'time_elapsed': 0,    # seconds
    'active_users': 0,
    'posts_per_min': 0,
    'total_posts': 0,
    'activity_feed': [],
    'post_accumulator': 0.0  # to accumulate fractional posts per second
}

simulation_lock = threading.Lock()
simulation_thread = None

def generate_random_post(length):
    letters = string.ascii_letters + string.digits + ' '
    return ''.join(random.choice(letters) for _ in range(length))

def simulation_loop():
    global simulation
    while True:
        with simulation_lock:
            if not simulation['running']:
                break
            if simulation['time_elapsed'] >= simulation['duration'] * 60:
                simulation['running'] = False
                break

            simulation['time_elapsed'] += 1

            # Update active users
            if simulation['random_users']:
                simulation['active_users'] = int(simulation['user_count'] * (0.3 + random.random() * 0.7))
            else:
                simulation['active_users'] = simulation['user_count']

            # Calculate posts per second as float
            posts_per_sec = simulation['post_rate'] / 60.0
            simulation['post_accumulator'] += posts_per_sec

            # Determine how many posts to generate this second
            posts_this_second = int(simulation['post_accumulator'])
            simulation['post_accumulator'] -= posts_this_second

            simulation['posts_per_min'] = posts_this_second * 60  # approximate for frontend display
            simulation['total_posts'] += posts_this_second

            # Generate activity feed entries
            for _ in range(posts_this_second):
                user_id = random.randint(1, simulation['user_count']) if simulation['random_users'] else 1
                post_text = generate_random_post(simulation['post_length'])
                simulation['activity_feed'].insert(0, {
                    'user': f'user{user_id}',
                    'text': post_text,
                    'timestamp': time.time()
                })
                # Keep feed size reasonable
                if len(simulation['activity_feed']) > 100:
                    simulation['activity_feed'].pop()

        time.sleep(1)


@app.route('/start', methods=['POST'])
def start_simulation():
    global simulation, simulation_thread
    data = request.json
    required_fields = ['user_count', 'post_rate', 'post_length', 'duration', 'random_users']
    if not data or not all(field in data for field in required_fields):
        return jsonify({'error': 'Missing parameters'}), 400

    with simulation_lock:
        if simulation['running']:
            return jsonify({'error': 'Simulation already running'}), 400

        simulation.update({
            'running': True,
            'user_count': int(data['user_count']),
            'post_rate': int(data['post_rate']),
            'post_length': int(data['post_length']),
            'duration': int(data['duration']),
            'random_users': bool(data['random_users']),
            'time_elapsed': 0,
            'active_users': 0,
            'posts_per_min': 0,
            'total_posts': 0,
            'activity_feed': [],
            'post_accumulator': 0.0
        })

    simulation_thread = threading.Thread(target=simulation_loop, daemon=True)
    simulation_thread.start()

    return jsonify({'message': 'Simulation started'})

@app.route('/stop', methods=['POST'])
def stop_simulation():
    global simulation
    with simulation_lock:
        if not simulation['running']:
            return jsonify({'error': 'No simulation running'}), 400
        simulation['running'] = False
    return jsonify({'message': 'Simulation stopped'})

@app.route('/status', methods=['GET'])
def get_status():
    with simulation_lock:
        if not simulation['running']:
            return jsonify({'running': False})
        return jsonify({
            'running': True,
            'active_users': simulation['active_users'],
            'posts_per_min': simulation['posts_per_min'],
            'total_posts': simulation['total_posts'],
            'activity_feed': simulation['activity_feed'][:20]  # limit feed size
        })

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5005)
