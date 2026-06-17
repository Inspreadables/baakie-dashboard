from flask import Flask, jsonify
import json
import os

app = Flask(__name__)
DATA_DIR = "data"
SPACES_FILE = os.path.join(DATA_DIR, "spaces.json")
LOGS_FILE = os.path.join(DATA_DIR, "logs.json")

@app.route('/')
def dashboard():
    return '''
    <!DOCTYPE html>
    <html>
    <head>
        <title>Space Status</title>
        <style>
            body { font-family: Arial; padding: 20px; background: #f0f2f5; }
            .card { background: white; padding: 20px; margin: 10px 0; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
            .online { color: #4CAF50; }
            .degraded { color: #FFC107; }
            .offline { color: #F44336; }
            .status { display: inline-block; padding: 5px 15px; border-radius: 20px; font-weight: bold; }
            .status.online { background: #4CAF50; color: white; }
            .status.degraded { background: #FFC107; color: black; }
            .status.offline { background: #F44336; color: white; }
            .stats { display: flex; gap: 20px; margin-bottom: 20px; }
            .stat { background: white; padding: 20px; border-radius: 10px; text-align: center; flex: 1; }
            .stat .number { font-size: 2em; font-weight: bold; }
        </style>
    </head>
    <body>
        <h1>Space Status Dashboard</h1>
        <div id="stats" class="stats"></div>
        <div id="spaces"></div>
        <script>
            fetch('/api/stats')
                .then(r => r.json())
                .then(data => {
                    document.getElementById('stats').innerHTML = 
                        '<div class="stat"><div class="number">' + data.total + '</div>Total</div>' +
                        '<div class="stat"><div class="number" style="color:#4CAF50;">' + data.online + '</div>Online</div>' +
                        '<div class="stat"><div class="number" style="color:#FFC107;">' + data.degraded + '</div>Degraded</div>' +
                        '<div class="stat"><div class="number" style="color:#F44336;">' + data.offline + '</div>Offline</div>';
                });
            fetch('/api/spaces')
                .then(r => r.json())
                .then(spaces => {
                    let html = '';
                    spaces.forEach(s => {
                        html += '<div class="card">';
                        html += '<h2>' + s.name + '</h2>';
                        html += '<div class="status ' + s.status + '">' + s.status.toUpperCase() + '</div>';
                        html += '<p>ID: ' + s.id + '</p>';
                        html += '<p>Response: ' + (s.response_time_ms || 'N/A') + 'ms</p>';
                        html += '<p>Last Check: ' + new Date(s.last_check).toLocaleString() + '</p>';
                        if (s.last_error) {
                            html += '<p style="color:red;">Error: ' + s.last_error + '</p>';
                        }
                        html += '</div>';
                    });
                    document.getElementById('spaces').innerHTML = html;
                });
        </script>
    </body>
    </html>
    '''

@app.route('/api/spaces')
def get_spaces():
    if os.path.exists(SPACES_FILE):
        with open(SPACES_FILE, 'r') as f:
            return jsonify(json.load(f))
    return jsonify([])

@app.route('/api/logs')
def get_logs():
    if os.path.exists(LOGS_FILE):
        with open(LOGS_FILE, 'r') as f:
            return jsonify(json.load(f)[-20:])
    return jsonify([])

@app.route('/api/stats')
def get_stats():
    if os.path.exists(SPACES_FILE):
        with open(SPACES_FILE, 'r') as f:
            spaces = json.load(f)
            total = len(spaces)
            online = sum(1 for s in spaces if s.get('status') == 'online')
            degraded = sum(1 for s in spaces if s.get('status') == 'degraded')
            offline = sum(1 for s in spaces if s.get('status') == 'offline')
            return jsonify({'total': total, 'online': online, 'degraded': degraded, 'offline': offline})
    return jsonify({'total': 0, 'online': 0, 'degraded': 0, 'offline': 0})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=False)
