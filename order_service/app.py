from flask import Flask, jsonify, request
from prometheus_flask_exporter import PrometheusMetrics
import psycopg2
import os

app = Flask(__name__)
metrics = PrometheusMetrics(app)
metrics.info('order_service_info', 'Order Service', version='1.0')

DB_HOST = os.environ.get('DB_HOST', 'postgres')
DB_NAME = os.environ.get('DB_NAME', 'sneakstore')
DB_USER = os.environ.get('DB_USER', 'postgres')
DB_PASSWORD = os.environ.get('DB_PASSWORD', 'postgres')

def get_db():
    try:
        conn = psycopg2.connect(
            host=DB_HOST,
            database=DB_NAME,
            user=DB_USER,
            password=DB_PASSWORD
        )
        return conn
    except Exception as e:
        print(f"Database connection error: {e}")
        return None

@app.route('/health')
def health():
    db = get_db()
    if db:
        db.close()
        return jsonify({"status": "healthy", "service": "order"}), 200
    return jsonify({"status": "unhealthy", "service": "order", "error": "DB connection failed"}), 503

@app.route('/orders', methods=['POST'])
def create_order():
    data = request.json
    db = get_db()
    if not db:
        return jsonify({"error": "Service unavailable"}), 503
    
    try:
        cur = db.cursor()
        cur.execute(
            "INSERT INTO orders (user_id, product_id, quantity) VALUES (%s, %s, %s) RETURNING id",
            (data.get('user_id'), data.get('product_id'), data.get('quantity', 1))
        )
        order_id = cur.fetchone()[0]
        db.commit()
        cur.close()
        db.close()
        return jsonify({"status": "success", "order_id": order_id}), 201
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/orders')
def get_orders():
    db = get_db()
    if not db:
        return jsonify({"error": "Service unavailable"}), 503
    try:
        cur = db.cursor()
        cur.execute("SELECT * FROM orders")
        orders = cur.fetchall()
        cur.close()
        db.close()
        return jsonify([{"id": o[0], "user_id": o[1], "product_id": o[2], "quantity": o[3]} for o in orders])
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)