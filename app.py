from flask import Flask, render_template, request, jsonify
from database import get_db_connection
import os

app = Flask(__name__)

@app.route('/')
def index():
    conn = get_db_connection()
    services = conn.execute('SELECT * FROM services').fetchall()
    conn.close()
    return render_template('index.html', services=services)

@app.route('/buy', methods=['POST'])
def buy():
    data = request.json
    service_id = data.get('service_id')
    user_id = data.get('user_id') # In a real app, get this from Telegram Web App data validation
    
    if not service_id or not user_id:
        return jsonify({'success': False, 'message': 'Missing data'}), 400

    conn = get_db_connection()
    conn.execute('INSERT INTO orders (user_id, service_id, status) VALUES (?, ?, ?)',
                 (user_id, service_id, 'pending'))
    conn.commit()
    conn.close()

    return jsonify({'success': True, 'message': 'Order placed successfully!'})

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
