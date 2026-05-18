from flask import Flask, request, jsonify
from elasticsearch import Elasticsearch

app = Flask(__name__)
es = Elasticsearch(['http://localhost:9200'])

@app.route('/health')
def health():
    return {"status": "healthy", "service": "search"}

@app.route('/search')
def search():
    query = request.args.get('q', '')
    if not query:
        return jsonify({"error": "Что то не так с параметром 'q'"}), 400
    
    result = es.search(
        index='products',
        query={
            "match": {
                "name": {
                    "query": query,
                    "fuzziness": "AUTO"
                }
            }
        },
        size=10
    )
    
    hits = []
    for hit in result['hits']['hits']:
        hits.append({
            'id': hit['_id'],
            'name': hit['_source']['name'],
            'price': hit['_source']['price'],
            'stock': hit['_source']['stock'],
            'image_url': hit['_source']['image_url'],
            'score': hit['_score']
        })
    
    return jsonify({
        'query': query,
        'total': result['hits']['total']['value'],
        'results': hits
    })

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5008)
