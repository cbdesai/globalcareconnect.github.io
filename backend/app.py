from flask import Flask, request, jsonify, Response
import os
import datetime
from flask_cors import CORS
import sqlite3
import csv
import io
from typing import Dict

app = Flask(__name__)
CORS(app)  # allow local front-end to call the API during development

ROOT_DIR = os.path.dirname(__file__)
DATA_DIR = os.path.normpath(os.path.join(ROOT_DIR, '..', 'submissions'))
os.makedirs(DATA_DIR, exist_ok=True)
DB_FILE = os.path.join(DATA_DIR, 'submissions.db')


# CSV/JSON archival removed — submissions are persisted to SQLite only.


def get_db_connection():
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_db_connection()
    cur = conn.cursor()
    # facilities table
    cur.execute('''
        CREATE TABLE IF NOT EXISTS facilities (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT,
            facilityName TEXT,
            contactPerson TEXT,
            email TEXT,
            phone TEXT,
            city TEXT,
            service TEXT,
            description TEXT
        )
    ''')
    # providers table
    cur.execute('''
        CREATE TABLE IF NOT EXISTS providers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT,
            providerName TEXT,
            businessName TEXT,
            email TEXT,
            phone TEXT,
            city TEXT,
            service TEXT,
            description TEXT
        )
    ''')
    # volunteers table
    cur.execute('''
        CREATE TABLE IF NOT EXISTS volunteers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT,
            name TEXT,
            email TEXT,
            phone TEXT,
            city TEXT,
            availability TEXT,
            interests TEXT
        )
    ''')
    conn.commit()
    conn.close()


def insert_facility_db(row: Dict[str, str]):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute('''
        INSERT INTO facilities (timestamp, facilityName, contactPerson, email, phone, city, service, description)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    ''', (row.get('timestamp'), row.get('facilityName'), row.get('contactPerson'), row.get('email'), row.get('phone'), row.get('city'), row.get('service'), row.get('description')))
    conn.commit()
    conn.close()


def insert_provider_db(row: Dict[str, str]):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute('''
        INSERT INTO providers (timestamp, providerName, businessName, email, phone, city, service, description)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    ''', (row.get('timestamp'), row.get('providerName'), row.get('businessName'), row.get('email'), row.get('phone'), row.get('city'), row.get('service'), row.get('description')))
    conn.commit()
    conn.close()


def insert_volunteer_db(row: Dict[str, str]):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute('''
        INSERT INTO volunteers (timestamp, name, email, phone, city, availability, interests)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    ''', (row.get('timestamp'), row.get('name'), row.get('email'), row.get('phone'), row.get('city'), row.get('availability'), row.get('interests')))
    conn.commit()
    conn.close()


# CSV/JSON archival removed for providers — using SQLite as sole storage.


@app.route('/register-facility', methods=['POST'])
def register_facility():
    payload = request.get_json()
    if not payload:
        return jsonify({'success': False, 'error': 'Invalid JSON payload'}), 400

    name = (payload.get('facilityName') or '').strip()
    email = (payload.get('email') or '').strip()
    if not name or not email:
        return jsonify({'success': False, 'error': 'Missing facilityName or email'}), 400

    timestamp = datetime.datetime.utcnow().isoformat()
    row = {
        'timestamp': timestamp,
        'facilityName': name,
        'contactPerson': (payload.get('contactPerson') or '').strip(),
        'email': email,
        'phone': (payload.get('phone') or '').strip(),
        'city': (payload.get('city') or '').strip(),
        'service': (payload.get('service') or '').strip(),
        'description': (payload.get('description') or '').strip(),
    }

    try:
        # persist to sqlite
        insert_facility_db(row)
        # persisted to SQLite
    except Exception as exc:
        return jsonify({'success': False, 'error': str(exc)}), 500

    return jsonify({'success': True, 'message': 'Registration received'}), 201


@app.route('/register-provider', methods=['POST'])
def register_provider():
    payload = request.get_json()
    if not payload:
        return jsonify({'success': False, 'error': 'Invalid JSON payload'}), 400

    name = (payload.get('providerName') or '').strip()
    email = (payload.get('email') or '').strip()
    if not name or not email:
        return jsonify({'success': False, 'error': 'Missing providerName or email'}), 400

    timestamp = datetime.datetime.utcnow().isoformat()
    row = {
        'timestamp': timestamp,
        'providerName': name,
        'businessName': (payload.get('businessName') or '').strip(),
        'email': email,
        'phone': (payload.get('phone') or '').strip(),
        'city': (payload.get('city') or '').strip(),
        'service': (payload.get('service') or '').strip(),
        'description': (payload.get('description') or '').strip(),
    }

    try:
        # persist to sqlite
        insert_provider_db(row)
        # persisted to SQLite
    except Exception as exc:
        return jsonify({'success': False, 'error': str(exc)}), 500

    return jsonify({'success': True, 'message': 'Provider profile received'}), 201


@app.route('/register-volunteer', methods=['POST'])
def register_volunteer():
    payload = request.get_json()
    if not payload:
        return jsonify({'success': False, 'error': 'Invalid JSON payload'}), 400

    name = (payload.get('name') or '').strip()
    email = (payload.get('email') or '').strip()
    if not name or not email:
        return jsonify({'success': False, 'error': 'Missing name or email'}), 400

    timestamp = datetime.datetime.utcnow().isoformat()
    row = {
        'timestamp': timestamp,
        'name': name,
        'email': email,
        'phone': (payload.get('phone') or '').strip(),
        'city': (payload.get('city') or '').strip(),
        'availability': (payload.get('availability') or '').strip(),
        'interests': (payload.get('interests') or '').strip(),
    }

    try:
        insert_volunteer_db(row)
    except Exception as exc:
        return jsonify({'success': False, 'error': str(exc)}), 500

    return jsonify({'success': True, 'message': 'Volunteer registration received'}), 201


@app.route('/submissions', methods=['GET'])
def list_submissions():
    # Prefer reading from sqlite
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute('SELECT * FROM facilities ORDER BY id DESC')
        rows = cur.fetchall()
        data = [dict(r) for r in rows]
        conn.close()
    except Exception:
        # On failure return empty list
        data = []
    return jsonify({'count': len(data), 'submissions': data})


@app.route('/submissions/providers', methods=['GET'])
def list_provider_submissions():
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute('SELECT * FROM providers ORDER BY id DESC')
        rows = cur.fetchall()
        data = [dict(r) for r in rows]
        conn.close()
    except Exception:
        data = []
    return jsonify({'count': len(data), 'submissions': data})


### Admin UI routes (local-only) ###


def rows_to_html_table(rows):
    if not rows:
        return '<p>No records</p>'
    # columns from first row
    cols = list(rows[0].keys())
    out = ['<table border="1" cellpadding="6" cellspacing="0">']
    out.append('<thead><tr>' + ''.join(f'<th>{c}</th>' for c in cols) + '</tr></thead>')
    out.append('<tbody>')
    for r in rows:
        out.append('<tr>' + ''.join(f'<td>{(r.get(c) if isinstance(r, dict) else r[c])}</td>' for c in cols) + '</tr>')
    out.append('</tbody></table>')
    return '\n'.join(out)


@app.route('/admin')
def admin_index():
    html = '''
    <h1>CareConnect — Admin</h1>
    <ul>
            <li><a href="/admin/facilities">View Facilities</a> — <a href="/admin/download/facilities.csv">Download CSV</a></li>
            <li><a href="/admin/providers">View Providers</a> — <a href="/admin/download/providers.csv">Download CSV</a></li>
            <li><a href="/admin/volunteers">View Volunteers</a> — <a href="/admin/download/volunteers.csv">Download CSV</a></li>
    </ul>
    <p><em>Local development only. Do not expose this endpoint publicly.</em></p>
    '''
    return Response(html, mimetype='text/html')


@app.route('/admin/facilities')
def admin_facilities():
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute('SELECT * FROM facilities ORDER BY id DESC')
    rows = [dict(r) for r in cur.fetchall()]
    conn.close()
    html = '<h1>Facilities</h1>' + rows_to_html_table(rows) + '<p><a href="/admin">Back</a></p>'
    return Response(html, mimetype='text/html')


@app.route('/admin/providers')
def admin_providers():
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute('SELECT * FROM providers ORDER BY id DESC')
    rows = [dict(r) for r in cur.fetchall()]
    conn.close()
    html = '<h1>Providers</h1>' + rows_to_html_table(rows) + '<p><a href="/admin">Back</a></p>'
    return Response(html, mimetype='text/html')


@app.route('/admin/volunteers')
def admin_volunteers():
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute('SELECT * FROM volunteers ORDER BY id DESC')
    rows = [dict(r) for r in cur.fetchall()]
    conn.close()
    html = '<h1>Volunteers</h1>' + rows_to_html_table(rows) + '<p><a href="/admin">Back</a></p>'
    return Response(html, mimetype='text/html')


@app.route('/admin/download/providers.csv')
def download_providers_csv():
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute('SELECT * FROM providers ORDER BY id DESC')
    rows = [dict(r) for r in cur.fetchall()]
    conn.close()

    si = io.StringIO()
    if rows:
        cols = list(rows[0].keys())
        writer = csv.DictWriter(si, fieldnames=cols)
        writer.writeheader()
        for r in rows:
            writer.writerow(r)
    else:
        si.write('')

    output = si.getvalue()
    return Response(output, mimetype='text/csv', headers={
        'Content-Disposition': 'attachment; filename=providers.csv'
    })


@app.route('/admin/download/facilities.csv')
def download_facilities_csv():
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute('SELECT * FROM facilities ORDER BY id DESC')
    rows = [dict(r) for r in cur.fetchall()]
    conn.close()

    si = io.StringIO()
    if rows:
        cols = list(rows[0].keys())
        writer = csv.DictWriter(si, fieldnames=cols)
        writer.writeheader()
        for r in rows:
            writer.writerow(r)
    else:
        si.write('')

    output = si.getvalue()
    return Response(output, mimetype='text/csv', headers={
        'Content-Disposition': 'attachment; filename=facilities.csv'
    })


@app.route('/admin/download/volunteers.csv')
def download_volunteers_csv():
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute('SELECT * FROM volunteers ORDER BY id DESC')
    rows = [dict(r) for r in cur.fetchall()]
    conn.close()

    si = io.StringIO()
    if rows:
        cols = list(rows[0].keys())
        writer = csv.DictWriter(si, fieldnames=cols)
        writer.writeheader()
        for r in rows:
            writer.writerow(r)
    else:
        si.write('')

    output = si.getvalue()
    return Response(output, mimetype='text/csv', headers={
        'Content-Disposition': 'attachment; filename=volunteers.csv'
    })


if __name__ == '__main__':
    # Development server only. For production use a proper WSGI server.
    # initialize sqlite DB if not present
    init_db()
    app.run(host='0.0.0.0', port=5000, debug=True)
