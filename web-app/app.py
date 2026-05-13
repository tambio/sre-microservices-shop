from flask import Flask, render_template, request, redirect, url_for
import psycopg2
from psycopg2.extras import RealDictCursor
from prometheus_flask_exporter import PrometheusMetrics

app = Flask(__name__)
app.static_folder = 'static'

# metriki
metrics = PrometheusMetrics(app)
metrics.info('app_info', 'SneakStore Online Store', version='1.0')

def get_db_connection():
    return psycopg2.connect(
        host="host.docker.internal",
        database="sneakstore",
        user="postgres",
        password="postgres"
    )

def init_db():
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute('''
        CREATE TABLE IF NOT EXISTS products (
            id SERIAL PRIMARY KEY,
            name TEXT NOT NULL,
            price NUMERIC(10,2) NOT NULL,
            description TEXT,
            image TEXT
        )
    ''')
    cur.execute("SELECT COUNT(*) FROM products")
    if cur.fetchone()[0] == 0:
        products = [
            ("Nike Air Max 270", 129.99, "Мегакомфортные кроссовки", "nike270.jpg"),
            ("Adidas Ultraboost", 159.99, "Лучшие беговые кроссовки", "ultraboost.jpg"),
            ("Puma RS-X", 89.99, "Стильные городские", "rsx.jpg"),
            ("New Balance 550", 109.99, "Ретро-дизайн", "nb550.jpg"),
            ("Yeezy Boost 350", 219.99, "Легендарные", "yeezy.jpg"),
        ]
        for p in products:
            cur.execute("INSERT INTO products (name, price, description, image) VALUES (%s, %s, %s, %s)", p)
        conn.commit()
    cur.close()
    conn.close()

init_db()

@app.route('/')
def home():
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    cur.execute("SELECT * FROM products")
    products = cur.fetchall()
    cur.close()
    conn.close()
    return render_template('index.html', products=products, search_query="")

@app.route('/search')
def search():
    query = request.args.get('q', '').strip()
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    cur.execute("SELECT * FROM products WHERE name ILIKE %s OR description ILIKE %s", (f'%{query}%', f'%{query}%'))
    products = cur.fetchall()
    cur.close()
    conn.close()
    return render_template('index.html', products=products, search_query=query)

@app.route('/product/<int:product_id>')
def product_detail(product_id):
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    cur.execute("SELECT * FROM products WHERE id = %s", (product_id,))
    product = cur.fetchone()
    cur.close()
    conn.close()
    if not product:
        return "Товар не найден", 404
    return render_template('product.html', product=product)

@app.route('/add-to-cart/<int:product_id>')
def add_to_cart(product_id):
    return redirect(url_for('home'))

@app.route('/metrics')
def metrics_route():
    return metrics.generate_latest()

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)