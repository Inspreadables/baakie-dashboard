import os
from flask import Flask, render_template, jsonify
import json
import traceback

# Get the absolute path
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
TEMPLATE_DIR = os.path.join(BASE_DIR, 'templates')

app = Flask(__name__, template_folder=TEMPLATE_DIR)

DATA_DIR = os.path.join(BASE_DIR, "data")
SPACES_FILE = os.path.join(DATA_DIR, "spaces.json")
LOGS_FILE = os.path.join(DATA_DIR, "logs.json")

def load_data(file_path):
    try:
        if os.path.exists(file_path):
            with open(file_path, 'r') as f:
                return json.load(f)
        return []
    except Exception as e:
        print(f"Error loading {file_path}: {e}")
        return []

@app.route('/')
def dashboard():
    try:
        return render_template('dashboard.html')
    except Exception as e:
        error_msg = f"Template error: {e}"
        print(error_msg)
        return f"<h1>Error</h1><p>{error_msg}</p><pre>{traceback.format_exc()}</pre>", 500

@app.route('/api/spaces')
def get_spaces():
    try:
        spaces = load_data(SPACES_FILE)
        return jsonify(spaces)
    except Exception as e:
        print(f"API error: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/logs')
def get_logs():
    try:
        logs = load_data(LOGS_FILE)
        return jsonify(logs[-20:])
    except Exception as e:
        print(f"API error: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/stats')
def get_stats():
    try:
        spaces = load_data(SPACES_FILE)
        total = len(spaces)
        online = sum(1 for s in spaces if s.get('status') == 'online')
        degraded = sum(1 for s in spaces if s.get('status') == 'degraded')
        offline = sum(1 for s in spaces if s.get('status') == 'offline')
        
        return jsonify({
            'total': total,
            'online': online,
            'degraded': degraded,
            'offline': offline,
            'uptime_percentage': round((online / total * 100) if total > 0 else 0, 1)
        })
    except Exception as e:
        print(f"Stats error: {e}")
        return jsonify({'error': str(e)}), 500

@app.errorhandler(500)
def internal_error(error):
    return f"<h1>Internal Server Error</h1><p>{error}</p><pre>{traceback.format_exc()}</pre>", 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)  # Turn debug ON temporarily to see errors
