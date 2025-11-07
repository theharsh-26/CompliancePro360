"""
CompliancePro360 - Production SaaS Application
License-based multi-tenant compliance management system

Run: python app_production.py
Access: http://localhost:5000 (local) or http://YOUR_IP:5000 (network)
"""

from flask import Flask, render_template, jsonify, request, redirect, url_for, session, flash
from flask_cors import CORS
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
import requests
import os
import secrets
from datetime import datetime, timedelta
from functools import wraps
import logging
from logging.handlers import RotatingFileHandler

# Initialize Flask app
app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY', secrets.token_hex(32))

# CORS configuration
CORS(app, resources={
    r"/api/*": {
        "origins": "*",
        "methods": ["GET", "POST", "PUT", "DELETE"],
        "allow_headers": ["Content-Type", "Authorization"]
    }
})

# Rate limiting
limiter = Limiter(
    app=app,
    key_func=get_remote_address,
    default_limits=["200 per day", "50 per hour"],
    storage_uri="memory://"
)

# Configuration
class Config:
    API_BASE_URL = os.getenv('API_URL', 'http://localhost:8000/api/v1')
    APP_NAME = "CompliancePro360"
    APP_VERSION = "2.0.0"
    APP_ENV = os.getenv('APP_ENV', 'production')
    
    # Pricing configuration
    PRICING_PLANS = {
        'trial': {
            'name': 'Free Trial',
            'monthly_fee': 0,
            'duration_days': 15,
            'max_companies': 5,
            'max_clients': 2,
            'features': ['basic_compliance', 'manual_entry']
        },
        'starter': {
            'name': 'Starter',
            'monthly_fee': 2999,  # INR
            'setup_fee': 0,
            'adhoc_per_company': 50,
            'max_companies': 50,
            'max_clients': 5,
            'features': ['ai_automation', 'data_scraping', 'basic_analytics']
        },
        'professional': {
            'name': 'Professional',
            'monthly_fee': 5999,
            'setup_fee': 0,
            'adhoc_per_company': 40,
            'max_companies': 200,
            'max_clients': 20,
            'features': ['ai_automation', 'data_scraping', 'advanced_analytics', 'risk_prediction', 'client_portal']
        },
        'enterprise': {
            'name': 'Enterprise',
            'monthly_fee': 14999,
            'setup_fee': 5000,
            'adhoc_per_company': 30,
            'max_companies': 1000,
            'max_clients': 100,
            'features': ['all_features', 'whatsapp_notifications', 'api_access', 'priority_support']
        }
    }

config = Config()

# Logging setup
if not os.path.exists('logs'):
    os.makedirs('logs')

file_handler = RotatingFileHandler('logs/compliancepro360.log', maxBytes=10240000, backupCount=10)
file_handler.setFormatter(logging.Formatter(
    '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
))
file_handler.setLevel(logging.INFO)
app.logger.addHandler(file_handler)
app.logger.setLevel(logging.INFO)
app.logger.info('CompliancePro360 startup')


# Decorators
def login_required(f):
    """Require user to be logged in"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'access_token' not in session:
            flash('Please log in to access this page.', 'warning')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function


def license_required(f):
    """Require valid license"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'license' not in session or not session['license'].get('is_valid'):
            flash('Valid license required. Please purchase or activate a license.', 'error')
            return redirect(url_for('pricing'))
        return f(*args, **kwargs)
    return decorated_function


def admin_required(f):
    """Require admin role"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if session.get('user', {}).get('role') not in ['system_admin', 'tenant_admin']:
            flash('Admin access required.', 'error')
            return redirect(url_for('dashboard'))
        return f(*args, **kwargs)
    return decorated_function


# API helper functions
def api_request(method, endpoint, data=None, auth=True):
    """Make API request to backend"""
    url = f"{config.API_BASE_URL}{endpoint}"
    headers = {}
    
    if auth and 'access_token' in session:
        headers['Authorization'] = f"Bearer {session['access_token']}"
    
    try:
        if method == 'GET':
            response = requests.get(url, headers=headers, timeout=10)
        elif method == 'POST':
            response = requests.post(url, json=data, headers=headers, timeout=10)
        elif method == 'PUT':
            response = requests.put(url, json=data, headers=headers, timeout=10)
        elif method == 'DELETE':
            response = requests.delete(url, headers=headers, timeout=10)
        
        if response.status_code < 400:
            return response.json()
        else:
            app.logger.error(f"API Error {response.status_code}: {response.text}")
            return None
    except requests.exceptions.RequestException as e:
        app.logger.error(f"API Request failed: {e}")
        return None


# Routes
@app.route('/')
def index():
    """Landing page"""
    if 'access_token' in session:
        return redirect(url_for('dashboard'))
    return render_template('index.html', config=config)


@app.route('/pricing')
def pricing():
    """Pricing plans page"""
    return render_template('pricing.html', plans=config.PRICING_PLANS)


@app.route('/purchase/<plan_type>')
@limiter.limit("5 per hour")
def purchase_license(plan_type):
    """Purchase license"""
    if plan_type not in config.PRICING_PLANS:
        flash('Invalid plan selected.', 'error')
        return redirect(url_for('pricing'))
    
    plan = config.PRICING_PLANS[plan_type]
    return render_template('purchase.html', plan_type=plan_type, plan=plan)


@app.route('/activate', methods=['GET', 'POST'])
def activate_license():
    """Activate license with key"""
    if request.method == 'POST':
        data = request.get_json()
        license_key = data.get('license_key')
        email = data.get('email')
        
        # Validate license key via API
        result = api_request('POST', '/licenses/activate', {
            'license_key': license_key,
            'email': email
        }, auth=False)
        
        if result and result.get('success'):
            session['license'] = result.get('license')
            session['shareable_link'] = result.get('shareable_link')
            return jsonify({'success': True, 'redirect': '/dashboard'})
        
        return jsonify({'success': False, 'error': 'Invalid license key or email'}), 400
    
    return render_template('activate.html')


@app.route('/login', methods=['GET', 'POST'])
@limiter.limit("10 per minute")
def login():
    """Login page"""
    if request.method == 'POST':
        data = request.get_json()
        response = api_request('POST', '/auth/login', data, auth=False)
        
        if response and 'access_token' in response:
            session['access_token'] = response['access_token']
            session['refresh_token'] = response['refresh_token']
            session['user'] = response['user']
            
            # Fetch license info
            license_info = api_request('GET', '/licenses/my-license')
            if license_info:
                session['license'] = license_info
            
            app.logger.info(f"User logged in: {data.get('email')}")
            return jsonify({'success': True, 'redirect': '/dashboard'})
        
        app.logger.warning(f"Failed login attempt: {data.get('email')}")
        return jsonify({'success': False, 'error': 'Invalid credentials'}), 401
    
    return render_template('login.html')


@app.route('/register', methods=['GET', 'POST'])
@limiter.limit("5 per hour")
def register():
    """Register new user"""
    if request.method == 'POST':
        data = request.get_json()
        
        # Register via API
        response = api_request('POST', '/auth/register', {
            'email': data.get('email'),
            'password': data.get('password'),
            'first_name': data.get('first_name'),
            'last_name': data.get('last_name'),
            'firm_name': data.get('firm_name'),
            'phone': data.get('phone', '')
        }, auth=False)
        
        if response and ('user' in response or 'message' in response):
            app.logger.info(f"New user registered: {data.get('email')}")
            return jsonify({'success': True, 'redirect': '/login'})
        
        error_msg = response.get('detail', 'Registration failed') if response else 'Backend API not reachable. Please ensure backend is running.'
        app.logger.warning(f"Registration failed: {data.get('email')} - {error_msg}")
        return jsonify({'success': False, 'error': error_msg}), 400
    
    return render_template('register.html')


@app.route('/logout')
def logout():
    """Logout"""
    user_email = session.get('user', {}).get('email', 'Unknown')
    session.clear()
    app.logger.info(f"User logged out: {user_email}")
    flash('You have been logged out successfully.', 'success')
    return redirect(url_for('index'))


@app.route('/dashboard')
@login_required
@license_required
def dashboard():
    """Main dashboard"""
    return render_template('dashboard_pro.html', user=session.get('user'), license=session.get('license'))


@app.route('/invite-client', methods=['GET', 'POST'])
@login_required
@license_required
def invite_client():
    """Invite client to access portal"""
    if request.method == 'POST':
        data = request.get_json()
        
        # Check if can add more clients
        license_info = session.get('license', {})
        if license_info.get('clients_count', 0) >= license_info.get('max_clients', 0):
            return jsonify({'success': False, 'error': 'Client limit reached. Upgrade your plan.'}), 400
        
        # Create invitation
        result = api_request('POST', '/clients/invite', data)
        
        if result and result.get('success'):
            app.logger.info(f"Client invitation sent to: {data.get('client_email')}")
            return jsonify({
                'success': True,
                'invitation_link': result.get('invitation_link'),
                'message': 'Invitation sent successfully!'
            })
        
        return jsonify({'success': False, 'error': 'Failed to create invitation'}), 400
    
    return render_template('invite_client.html', license=session.get('license'))


@app.route('/client/join/<license_key>/<token>')
def join_as_client(license_key, token):
    """Client joins via invitation link"""
    # Validate invitation
    result = api_request('POST', '/clients/join', {
        'license_key': license_key,
        'token': token
    }, auth=False)
    
    if result and result.get('valid'):
        return render_template('client_signup.html', invitation=result)
    
    flash('Invalid or expired invitation link.', 'error')
    return redirect(url_for('index'))


@app.route('/my-license')
@login_required
@license_required
def my_license():
    """View license details and billing"""
    license_info = api_request('GET', '/licenses/my-license')
    invoices = api_request('GET', '/licenses/invoices')
    
    return render_template('my_license.html', 
                         license=license_info, 
                         invoices=invoices,
                         shareable_link=session.get('shareable_link'))


@app.route('/admin/licenses')
@login_required
@admin_required
def admin_licenses():
    """Admin: Manage all licenses"""
    licenses = api_request('GET', '/admin/licenses')
    return render_template('admin_licenses.html', licenses=licenses)


# API Proxy Routes (same as before, but with license checks)
@app.route('/api/dashboard/stats')
@login_required
@license_required
def api_dashboard_stats():
    """Dashboard statistics"""
    # Mock data - replace with actual API calls
    stats = {
        'totalCompanies': session.get('license', {}).get('companies_count', 0),
        'pendingTasks': 23,
        'completedTasks': 156,
        'overdueTasks': 5,
        'averageComplianceScore': 87,
        'monthlyBill': session.get('license', {}).get('monthly_bill', 0),
        'licensePlan': session.get('license', {}).get('license_type', 'trial').title()
    }
    return jsonify(stats)


# Error handlers
@app.errorhandler(404)
def not_found(error):
    return render_template('404.html'), 404


@app.errorhandler(500)
def internal_error(error):
    app.logger.error(f'Server Error: {error}')
    return render_template('500.html'), 500


@app.errorhandler(429)
def ratelimit_handler(e):
    return jsonify({'error': 'Rate limit exceeded. Please try again later.'}), 429


# Main
if __name__ == '__main__':
    import socket
    
    print("\n" + "="*70)
    print("  🚀 CompliancePro360 - Production SaaS Platform")
    print("="*70)
    print(f"\n📊 Application: {config.APP_NAME} v{config.APP_VERSION}")
    print(f"🌍 Environment: {config.APP_ENV}")
    print(f"🔗 Backend API: {config.API_BASE_URL}")
    
    print("\n🌐 Access URLs:")
    print(f"   Local:    http://localhost:5000")
    print(f"   Local:    http://127.0.0.1:5000")
    
    try:
        hostname = socket.gethostname()
        local_ip = socket.gethostbyname(hostname)
        print(f"   Network:  http://{local_ip}:5000")
        print(f"\n📱 Share this link with clients:")
        print(f"   http://{local_ip}:5000")
    except:
        print(f"   Network:  http://YOUR_IP:5000")
    
    print("\n📝 Main Pages:")
    print("   Landing:        http://localhost:5000/")
    print("   Pricing:        http://localhost:5000/pricing")
    print("   Purchase:       http://localhost:5000/purchase/professional")
    print("   Activate:       http://localhost:5000/activate")
    print("   Login:          http://localhost:5000/login")
    print("   Dashboard:      http://localhost:5000/dashboard")
    print("   My License:     http://localhost:5000/my-license")
    print("   Invite Client:  http://localhost:5000/invite-client")
    
    print("\n💰 Pricing Plans:")
    for plan_type, plan in config.PRICING_PLANS.items():
        if plan_type != 'trial':
            print(f"   {plan['name']:15} ₹{plan['monthly_fee']}/month + ₹{plan.get('adhoc_per_company', 0)}/company")
    
    print("\n" + "="*70)
    print("  ✅ Server Starting... Press CTRL+C to stop")
    print("="*70 + "\n")
    
    # Run Flask server
    app.run(
        host='0.0.0.0',
        port=5000,
        debug=(config.APP_ENV == 'development'),
        use_reloader=True
    )
