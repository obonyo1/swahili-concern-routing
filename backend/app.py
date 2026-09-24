from flask import Flask, jsonify
from flask_socketio import SocketIO
from flask_cors import CORS
from dotenv import load_dotenv
import os

load_dotenv()

app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('FLASK_SECRET_KEY', 'dev-secret')
CORS(app)
socketio = SocketIO(app, cors_allowed_origins="*")


@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint. Confirms backend is running."""
    return jsonify({
        'status': 'running',
        'message': 'Swahili Concern Classification API is live'
    }), 200


@app.route('/api/categories', methods=['GET'])
def get_categories():
    """Returns the four predefined concern categories."""
    categories = ['Food Security', 'Health', 'Shelter', 'Safety']
    return jsonify({'categories': categories}), 200


@socketio.on('connect')
def handle_connect():
    print('Client connected')


@socketio.on('disconnect')
def handle_disconnect():
    print('Client disconnected')


if __name__ == '__main__':
    port = int(os.getenv('FLASK_PORT', 5000))
    socketio.run(app, host='0.0.0.0', port=port, debug=True, allow_unsafe_werkzeug=True)
