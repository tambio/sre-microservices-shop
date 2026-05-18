import psycopg2
from elasticsearch import Elasticsearch
import json

DB_CONFIG = {
    'host': 'localhost',
    'database': 'sneakstore',
    'user': 'postgres',
    'password': 'postgres',
    'port': 5432
}

es = Elasticsearch(['http://localhost:9200'])

if not es.ping():
    print("Elasticsearch is not running!")
    exit(1)

print("Connected to Elasticsearch")

mapping = {
    "mappings": {
        "properties": {
            "name": {"type": "text", "analyzer": "standard"},
            "price": {"type": "float"},
            "stock": {"type": "integer"},
            "image_url": {"type": "keyword"},
            "category": {"type": "keyword"}
        }
    }
}

if es.indices.exists(index='products'):
    es.indices.delete(index='products')
    print("Deleted old index")

es.indices.create(index='products', body=mapping)
print("Created index 'products'")

conn = psycopg2.connect(**DB_CONFIG)
cur = conn.cursor()
cur.execute("SELECT id, name, price, stock, COALESCE(image_url, '') FROM products")
products = cur.fetchall()
cur.close()
conn.close()

print(f"Found {len(products)} products in PostgreSQL")

for p in products:
    doc = {
    'name': p[1],
    'price': float(p[2]),
    'stock': p[3],
    'image_url': p[4]
}
    es.index(index='products', id=p[0], document=doc)

print(f"Indexed {len(products)} products in Elasticsearch")

es.indices.refresh(index='products')
result = es.search(index='products', query={"match_all": {}})
print(f"Total documents in index: {result['hits']['total']['value']}")
