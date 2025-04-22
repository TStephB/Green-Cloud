from flask import Flask, request, jsonify
import json
import os
from datetime import datetime

app = Flask(__name__)

# Emplacements des fichiers (relatifs à /data/)
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../data'))
USER_FILE = os.path.join(BASE_DIR, "users.json")
POST_FILE = os.path.join(BASE_DIR, "posts.json")

def load_json(filepath):
    if not os.path.exists(filepath):
        return []
    with open(filepath, "r") as f:
        return json.load(f)

def save_json(filepath, data):
    with open(filepath, "w") as f:
        json.dump(data, f, indent=2)

@app.route('/register', methods=['POST'])
def register():
    users = load_json(USER_FILE)
    data = request.get_json()
    if any(u['username'] == data['username'] for u in users):
        return jsonify({"message": "Username already exists"}), 409
    users.append({"username": data['username'], "password": data['password']})
    save_json(USER_FILE, users)
    return jsonify({"message": "Registered successfully"}), 201

@app.route('/login', methods=['POST'])
def login():
    users = load_json(USER_FILE)
    data = request.get_json()
    user = next((u for u in users if u['username'] == data['username'] and u['password'] == data['password']), None)
    if user:
        return jsonify({"message": "Login successful"}), 200
    return jsonify({"message": "Invalid credentials"}), 401

@app.route('/post', methods=['POST'])
def post():
    posts = load_json(POST_FILE)
    data = request.get_json()
    new_post = {
        "username": data['username'],
        "text": data['text'],
        "timestamp": datetime.now().isoformat()
    }
    posts.insert(0, new_post)
    save_json(POST_FILE, posts)
    return jsonify({"message": "Post created"}), 201

@app.route('/posts', methods=['GET'])
def get_posts():
    posts = load_json(POST_FILE)
    return jsonify(posts), 200

if __name__ == '__main__':
    os.makedirs(BASE_DIR, exist_ok=True)
    app.run(host="0.0.0.0", port=5001, debug=True)
