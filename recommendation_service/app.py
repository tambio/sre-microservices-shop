from flask import Flask, render_template, jsonify
from prometheus_flask_exporter import PrometheusMetrics
import psycopg2
import random

app = Flask(__name__)
metrics = PrometheusMetrics(app)
metrics.info('recommendation_service_info', 'Recommendation Service', version='1.0')

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

def get_recommendations():
    """Получить 3 случайных товара"""
    try:
        conn = get_db()
        cur = conn.cursor()
        
        # Сначала проверим, какие колонки есть
        cur.execute("SELECT column_name FROM information_schema.columns WHERE table_name='products'")
        columns = [row[0] for row in cur.fetchall()]
        print(f"Columns in products: {columns}")
        
        # Строим запрос в зависимости от наличия колонок
        select_fields = "id, name, price, stock"
        if 'image_url' in columns:
            select_fields += ", COALESCE(image_url, '')"
        else:
            select_fields += ", '' as image_url"
        
        cur.execute(f"SELECT {select_fields} FROM products")
        all_products = cur.fetchall()
        cur.close()
        conn.close()
        
        if not all_products:
            return []
        
        # показываем 3 товара
        selected = random.sample(all_products, min(3, len(all_products)))
        
        recommendations = []
        for p in selected:
            recommendations.append({
                "id": p[0],
                "name": p[1],
                "price": float(p[2]),
                "stock": p[3],
                "image_url": p[4] if len(p) > 4 else ''
            })
        
        return recommendations
    except Exception as e:
        print(f"get_recommendations error: {e}")
        return []

@app.route('/health')
def health():
    try:
        db = get_db()
        db.close()
        return {"status": "healthy", "service": "recommendation"}
    except:
        return {"status": "unhealthy", "service": "recommendation"}

@app.route('/')
def index():
    recommendations = get_recommendations()
    return render_template('recommendations.html', recommendations=recommendations)

@app.route('/recommendations')
def api_recommendations():
    return jsonify(get_recommendations())

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)