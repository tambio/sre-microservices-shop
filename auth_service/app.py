from flask import Flask, jsonify, request
from prometheus_flask_exporter import PrometheusMetrics
import os

app = Flask(__name__)
metrics = PrometheusMetrics(app)
metrics.info('auth_service_info', 'Auth Service', version='1.0')

users = {
    "user1": "pass1",
    "admin": "admin123"
}

@app.route('/health')
def health():
    return jsonify({"status": "healthy", "service": "auth"})

@app.route('/auth/login', methods=['POST'])
def login():
    data = request.json
    username = data.get('username')
    password = data.get('password')
    
    if username in users and users[username] == password:
        return jsonify({"status": "success", "token": f"token_{username}"}), 200
    return jsonify({"status": "error", "message": "Invalid credentials"}), 401

@app.route('/auth/verify', methods=['POST'])
def verify():
    token = request.json.get('token')
    if token and token.startswith('token_'):
        return jsonify({"status": "valid"}), 200
    return jsonify({"status": "invalid"}), 401

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)