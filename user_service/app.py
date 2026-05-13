from flask import Flask, jsonify
from prometheus_flask_exporter import PrometheusMetrics

app = Flask(__name__)
metrics = PrometheusMetrics(app)
metrics.info('user_service_info', 'User Service', version='1.0')

users = {
    1: {"id": 1, "name": "John Doe", "email": "john@example.com"},
    2: {"id": 2, "name": "Jane Smith", "email": "jane@example.com"}
}

@app.route('/health')
def health():
    return jsonify({"status": "healthy", "service": "user"})

@app.route('/users')
def get_users():
    return jsonify(list(users.values()))

@app.route('/users/<int:user_id>')
def get_user(user_id):
    user = users.get(user_id)
    if user:
        return jsonify(user)
    return jsonify({"error": "User not found"}), 404

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)