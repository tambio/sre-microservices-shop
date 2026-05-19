from flask import Flask, render_template, jsonify, request, redirect
from prometheus_flask_exporter import PrometheusMetrics
import psycopg2

app = Flask(__name__)
metrics = PrometheusMetrics(app)
metrics.info('inventory_service_info', 'Inventory Service', version='1.0')

DB_HOST = 'postgres_db'
DB_NAME = 'sneakstore'
DB_USER = 'postgres'
DB_PASSWORD = 'postgres'

def get_db():
    return psycopg2.connect(
        host=DB_HOST,
        database=DB_NAME,
        user=DB_USER,
        password=DB_PASSWORD
    )

def get_all_products():
    try:
        conn = get_db()
        cur = conn.cursor()
        cur.execute("SELECT id, name, stock FROM products ORDER BY id")
        products = cur.fetchall()
        cur.close()
        conn.close()
        return products
    except Exception as e:
        print(f"get_all_products error: {e}")
        return []

def get_stock(product_id):
    try:
        conn = get_db()
        cur = conn.cursor()
        cur.execute("SELECT stock FROM products WHERE id = %s", (product_id,))
        result = cur.fetchone()
        cur.close()
        conn.close()
        return result[0] if result else 0
    except Exception as e:
        print(f"get_stock error: {e}")
        return 0

def decrease_stock(product_id):
    try:
        conn = get_db()
        cur = conn.cursor()
        cur.execute("UPDATE products SET stock = stock - 1 WHERE id = %s AND stock > 0", (product_id,))
        conn.commit()
        updated = cur.rowcount
        cur.close()
        conn.close()
        return updated > 0
    except Exception as e:
        print(f"decrease_stock error: {e}")
        return False

@app.route('/health')
def health():
    db = get_db()
    if db:
        db.close()
        return {"status": "healthy", "service": "inventory"}
    return {"status": "unhealthy", "service": "inventory"}

@app.route('/')
def index():
    products = get_all_products()
    items = [{"id": p[0], "name": p[1], "stock": p[2]} for p in products]
    return render_template('inventory.html', items=items)

@app.route('/inventory/<int:product_id>')
def check_stock(product_id):
    stock = get_stock(product_id)
    return jsonify({"product_id": product_id, "stock": stock, "available": stock > 0})

@app.route('/inventory/<int:product_id>/reserve', methods=['POST'])
def reserve_stock(product_id):
    success = decrease_stock(product_id)
    if success:
        stock_left = get_stock(product_id)
        return jsonify({"success": True, "product_id": product_id, "stock_left": stock_left})
    return jsonify({"success": False, "error": "Товар закончился, скоро будет!"})

@app.route('/order/<int:product_id>', methods=['POST'])
def order_from_page(product_id):
    success = decrease_stock(product_id)
    if success:
        return redirect('/')
    products = get_all_products()
    items = [{"id": p[0], "name": p[1], "stock": p[2]} for p in products]
    return render_template('inventory.html', items=items, message="Товар закончился, скоро будет!", msg_type="error")

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)