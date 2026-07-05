#!/usr/bin/env python3
"""
FamilyCal - Raspberry Pi Family Calendar Server
Run with: python3 server.py
Then visit: http://<your-pi-ip>:5000
"""

import argparse
import json
import os
import shutil
import threading
import uuid
from datetime import datetime
from flask import Flask, jsonify, request, send_from_directory

app = Flask(__name__, static_folder='static')

DATA_FILE   = os.path.join(os.path.dirname(__file__), 'calendar.json')
BACKUP_DIR  = os.path.join(os.path.dirname(__file__), 'backups')
BACKUP_SECS = 7 * 24 * 60 * 60   # one week


# ── Backup ────────────────────────────────────────────────────────────────────

def do_backup():
    """Copy calendar.json → backups/calendar-YYYY-MM-DD.json, then reschedule."""
    if os.path.exists(DATA_FILE):
        os.makedirs(BACKUP_DIR, exist_ok=True)
        stamp = datetime.now().strftime('%Y-%m-%d')
        dest  = os.path.join(BACKUP_DIR, f'calendar-{stamp}.json')
        shutil.copy2(DATA_FILE, dest)
        print(f'  📦 Backup saved: backups/calendar-{stamp}.json')
    # Reschedule for next week
    t = threading.Timer(BACKUP_SECS, do_backup)
    t.daemon = True
    t.start()

# ── Default data ──────────────────────────────────────────────────────────────

def default_data():
    today = datetime.today()
    y, m, d = today.year, today.month, today.day

    def date_offset(days):
        from datetime import timedelta
        return (today + timedelta(days=days)).strftime('%Y-%m-%d')

    return {
        "members": [
            {"id": "m1", "name": "Mum",  "color": "#E07A5F", "visible": True},
            {"id": "m2", "name": "Dad",  "color": "#3D9BE9", "visible": True},
            {"id": "m3", "name": "Kids", "color": "#7FB069", "visible": True},
        ],
        "events": [
            {"id": str(uuid.uuid4()), "title": "School run",       "date": date_offset(0),  "time": "08:30", "endTime": "09:00", "memberId": "m1", "location": "School",       "notes": "",                    "recurrence": "daily"},
            {"id": str(uuid.uuid4()), "title": "Football training", "date": date_offset(1),  "time": "16:00", "endTime": "17:30", "memberId": "m3", "location": "Sports ground", "notes": "",                    "recurrence": "weekly"},
            {"id": str(uuid.uuid4()), "title": "Dentist",           "date": date_offset(3),  "time": "10:00", "endTime": "10:30", "memberId": "m2", "location": "Dental clinic", "notes": "Bring insurance card","recurrence": "none"},
            {"id": str(uuid.uuid4()), "title": "Family dinner",     "date": date_offset(5),  "time": "18:30", "endTime": "20:00", "memberId": "m1", "location": "Home",          "notes": "Grandparents coming!","recurrence": "none"},
            {"id": str(uuid.uuid4()), "title": "Grocery shopping",  "date": date_offset(2),  "time": "10:00", "endTime": "11:00", "memberId": "m2", "location": "Supermarket",   "notes": "",                    "recurrence": "weekly"},
            {"id": str(uuid.uuid4()), "title": "Piano lesson",      "date": date_offset(4),  "time": "15:00", "endTime": "16:00", "memberId": "m3", "location": "",              "notes": "",                    "recurrence": "weekly"},
        ]
    }


# ── Persistence ───────────────────────────────────────────────────────────────

def load_data():
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, 'r') as f:
                return json.load(f)
        except Exception:
            pass
    data = default_data()
    save_data(data)
    return data


def save_data(data):
    with open(DATA_FILE, 'w') as f:
        json.dump(data, f, indent=2)


# ── Routes ────────────────────────────────────────────────────────────────────

@app.route('/')
def index():
    return send_from_directory('static', 'index.html')


# --- State (full load/save) ---

@app.route('/api/state', methods=['GET'])
def get_state():
    return jsonify(load_data())


# --- Events ---

@app.route('/api/events', methods=['GET'])
def get_events():
    return jsonify(load_data()['events'])


@app.route('/api/events', methods=['POST'])
def create_event():
    data = load_data()
    ev = request.get_json()
    ev['id'] = str(uuid.uuid4())
    data['events'].append(ev)
    save_data(data)
    return jsonify(ev), 201


@app.route('/api/events/<event_id>', methods=['PUT'])
def update_event(event_id):
    data = load_data()
    ev = request.get_json()
    ev['id'] = event_id
    data['events'] = [ev if e['id'] == event_id else e for e in data['events']]
    save_data(data)
    return jsonify(ev)


@app.route('/api/events/<event_id>', methods=['DELETE'])
def delete_event(event_id):
    data = load_data()
    data['events'] = [e for e in data['events'] if e['id'] != event_id]
    save_data(data)
    return jsonify({'ok': True})


# --- Members ---

@app.route('/api/members', methods=['GET'])
def get_members():
    return jsonify(load_data()['members'])


@app.route('/api/members', methods=['POST'])
def create_member():
    data = load_data()
    m = request.get_json()
    m['id'] = str(uuid.uuid4())
    m.setdefault('visible', True)
    data['members'].append(m)
    save_data(data)
    return jsonify(m), 201


@app.route('/api/members/<member_id>', methods=['PUT'])
def update_member(member_id):
    data = load_data()
    m = request.get_json()
    m['id'] = member_id
    data['members'] = [m if x['id'] == member_id else x for x in data['members']]
    save_data(data)
    return jsonify(m)


@app.route('/api/members/<member_id>', methods=['DELETE'])
def delete_member(member_id):
    data = load_data()
    data['members'] = [x for x in data['members'] if x['id'] != member_id]
    # Unassign events belonging to deleted member
    for ev in data['events']:
        if ev.get('memberId') == member_id:
            ev['memberId'] = ''
    save_data(data)
    return jsonify({'ok': True})


# --- Todos ---

@app.route('/api/todos', methods=['GET'])
def get_todos():
    return jsonify(load_data().get('todos', []))


@app.route('/api/todos', methods=['POST'])
def create_todo():
    data = load_data()
    todo = request.get_json()
    todo['id'] = str(uuid.uuid4())
    todo.setdefault('done', False)
    todo.setdefault('memberId', '')
    todo.setdefault('priority', 'normal')
    data.setdefault('todos', []).append(todo)
    save_data(data)
    return jsonify(todo), 201


@app.route('/api/todos/<todo_id>', methods=['PUT'])
def update_todo(todo_id):
    data = load_data()
    todo = request.get_json()
    todo['id'] = todo_id
    data['todos'] = [todo if t['id'] == todo_id else t for t in data.get('todos', [])]
    save_data(data)
    return jsonify(todo)


@app.route('/api/todos/<todo_id>', methods=['DELETE'])
def delete_todo(todo_id):
    data = load_data()
    data['todos'] = [t for t in data.get('todos', []) if t['id'] != todo_id]
    save_data(data)
    return jsonify({'ok': True})


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='FamilyCal server')
    parser.add_argument(
        '--port', '-p',
        type=int,
        default=int(os.environ.get('PORT', 5000)),
        help='Port to listen on (default: 5000, or $PORT env var)',
    )
    args = parser.parse_args()

    print("━" * 50)
    print("  🏠 FamilyCal server starting…")
    print(f"  Open http://localhost:{args.port} in your browser")
    print(f"  Or from other devices: http://<pi-ip>:{args.port}")
    print("━" * 50)
    do_backup()   # run once now, then weekly
    app.run(host='0.0.0.0', port=args.port, debug=False)
