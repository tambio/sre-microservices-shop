from flask import Flask, render_template, request, redirect, session
from prometheus_flask_exporter import PrometheusMetrics
import psycopg2
import os

app = Flask(__name__)
app.secret_key = 'sneakstore-secret-key-2024'

metrics = PrometheusMetrics(app)
metrics.info('product_service_info', 'Product Service', version='1.0')

DB_HOST = 'host.docker.internal'
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

def get_products():
    try:
        conn = get_db()
        cur = conn.cursor()
        cur.execute("SELECT id, name, price, stock, COALESCE(image_url, '') FROM products ORDER BY id")
        products = cur.fetchall()
        cur.close()
        conn.close()
        return products
    except Exception as e:
        print(f"get_products error: {e}")
        return []

def get_orders(user_id):
    try:
        conn = get_db()
        cur = conn.cursor()
        cur.execute("SELECT * FROM orders WHERE user_id = %s ORDER BY id DESC", (user_id,))
        orders = cur.fetchall()
        cur.close()
        conn.close()
        return orders
    except Exception as e:
        print(f"get_orders error: {e}")
        return []

def create_order(user_id, product_id):
    try:
        conn = get_db()
        cur = conn.cursor()
        cur.execute(
            "INSERT INTO orders (user_id, product_id, quantity) VALUES (%s, %s, 1)",
            (user_id, product_id)
        )
        conn.commit()
        cur.close()
        conn.close()
        return True
    except Exception as e:
        print(f"create_order error: {e}")
        return False

def register_user(username, password):
    try:
        conn = get_db()
        cur = conn.cursor()
        
        # чек на наличие 
        cur.execute("SELECT id FROM users WHERE username = %s", (username,))
        existing = cur.fetchone()
        
        if existing:
            cur.close()
            conn.close()
            return "exists" 
        
        cur.execute("INSERT INTO users (username, password) VALUES (%s, %s)", (username, password))
        conn.commit()
        cur.close()
        conn.close()
        return "success"
    except Exception as e:
        print(f"register_user error: {e}")
        return "error"

def login_user(username, password):
    try:
        conn = get_db()
        cur = conn.cursor()
        cur.execute("SELECT id, username FROM users WHERE username = %s AND password = %s", (username, password))
        user = cur.fetchone()
        cur.close()
        conn.close()
        return user  
    except Exception as e:
        print(f"login_user error: {e}")
        return None

@app.route('/')
def index():
    products = get_products()
    return render_template('index.html', products=products, user=session.get('username'))

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '').strip()
        
        if not username or not password:
            return render_template('register.html', message='Заполните все поля', msg_type='error')
        
        result = register_user(username, password)
        
        if result == 'success':
            return render_template('register.html', message='Регистрация успешна! Теперь войдите.', msg_type='success')
        elif result == 'exists':
            return render_template('register.html', message='Пользователь уже существует', msg_type='error')
        else:
            return render_template('register.html', message='Ошибка сервера, попробуйте позже', msg_type='error')
    
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '').strip()
        
        user = login_user(username, password)
        if user:
            session['user_id'] = user[0]
            session['username'] = user[1]
            return redirect('/')
        else:
            return render_template('login.html', message='Неверный логин или пароль', msg_type='error')
    
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect('/')

@app.route('/orders')
def orders_page():
    if 'user_id' not in session:
        return redirect('/login')
    
    orders = get_orders(session['user_id'])
    return render_template('orders.html', orders=orders, user=session.get('username'))


@app.route('/buy', methods=['POST'])
def buy():
    if 'user_id' not in session:
        return redirect('/login')
    
    product_id = request.form.get('product_id')
    products = get_products()
    
    #  чек остатка Inventory Service
    try:
        import requests
        response = requests.post(f'http://inventory_service_tf:5000/inventory/{product_id}/reserve', timeout=5)
        result = response.json()
        
        if not result.get('success'):
            return render_template('index.html', products=products, user=session.get('username'), 
                                 message=result.get('error', 'Товар закончился, скоро будет!'), msg_type='error')
    except Exception as e:
        print(f"Inventory error: {e}")
        # обход если инвентори недоступен, но товар есть в БД
        pass
    
    if create_order(session['user_id'], product_id):
        return render_template('index.html', products=products, user=session.get('username'), 
                             message='Заказ успешно создан!', msg_type='success')
    
    return render_template('index.html', products=products, user=session.get('username'), 
                         message='Ошибка создания заказа', msg_type='error')

@app.route('/health')
def health():
    db = get_db()
    if db:
        db.close()
        return {"status": "healthy", "service": "product"}
    return {"status": "unhealthy", "service": "product"}

@app.route('/products')
def api_products():
    products = get_products()
    return [{"id": p[0], "name": p[1], "price": float(p[2]), "stock": p[3], "image_url": p[4]} for p in products]

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
