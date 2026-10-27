import re
from functools import wraps
from flask import Blueprint, render_template, request, redirect, url_for, flash, session, g
from werkzeug.security import generate_password_hash, check_password_hash
from database import query_db, execute_db, log_audit

auth_bp = Blueprint('auth', __name__)

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please sign in to access your account.', 'info')
            return redirect(url_for('auth.login', next=request.url))
        return f(*args, **kwargs)
    return decorated_function

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session or session.get('user_role') != 'admin':
            flash('Administrator privileges required to access this resource.', 'danger')
            return redirect(url_for('auth.admin_login', next=request.url))
        return f(*args, **kwargs)
    return decorated_function

def is_valid_indian_phone(phone: str) -> bool:
    clean = re.sub(r'[\s\-\+]', '', phone)
    if clean.startswith('91') and len(clean) == 12:
        clean = clean[2:]
    return bool(re.match(r'^[6-9]\d{9}$', clean))

def is_valid_email(email: str) -> bool:
    return bool(re.match(r'^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$', email.strip()))

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if 'user_id' in session:
        return redirect(url_for('store.home'))
        
    next_url = request.args.get('next') or url_for('store.home')
    
    if request.method == 'POST':
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')
        
        if not email or not password:
            flash('Please enter both email and password.', 'warning')
            return render_template('account/login.html', email=email, next=next_url)
            
        user = query_db("SELECT * FROM users WHERE LOWER(email) = ? AND is_active = 1", (email,), one=True)
        if user and check_password_hash(user['password_hash'], password):
            session['user_id'] = user['id']
            session['user_name'] = user['name']
            session['user_email'] = user['email']
            session['user_role'] = user['role']
            session.permanent = True
            
            flash(f"Welcome back, {user['name']}!", 'success')
            if user['role'] == 'admin':
                return redirect(url_for('admin.dashboard'))
            return redirect(next_url)
        else:
            flash('Invalid email or password. Please try again.', 'danger')
            
    return render_template('account/login.html', next=next_url)

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    if 'user_id' in session:
        return redirect(url_for('store.home'))
        
    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        email = request.form.get('email', '').strip().lower()
        phone = request.form.get('phone', '').strip()
        password = request.form.get('password', '')
        confirm_password = request.form.get('confirm_password', '')
        
        errors = []
        if not name or len(name) < 2:
            errors.append('Please provide your full name.')
        if not is_valid_email(email):
            errors.append('Please provide a valid email address.')
        if phone and not is_valid_indian_phone(phone):
            errors.append('Please enter a valid 10-digit Indian mobile number.')
        if len(password) < 6:
            errors.append('Password must be at least 6 characters long.')
        if password != confirm_password:
            errors.append('Passwords do not match.')
            
        if not errors:
            existing = query_db("SELECT id FROM users WHERE email = ?", (email,), one=True)
            if existing:
                errors.append('An account with this email address already exists.')
                
        if errors:
            for err in errors:
                flash(err, 'danger')
            return render_template('account/register.html', name=name, email=email, phone=phone)
            
        hashed = generate_password_hash(password, method='scrypt')
        user_id, _ = execute_db(
            """INSERT INTO users (name, email, phone, password_hash, role, is_active)
               VALUES (?, ?, ?, ?, 'customer', 1)""",
            (name, email, phone, hashed)
        )
        
        session['user_id'] = user_id
        session['user_name'] = name
        session['user_email'] = email
        session['user_role'] = 'customer'
        session.permanent = True
        
        flash(f'Account created successfully! Welcome to High Tech Mobile, {name}.', 'success')
        return redirect(url_for('store.home'))
        
    return render_template('account/register.html')

@auth_bp.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    if session.get('user_role') == 'admin':
        return redirect(url_for('admin.dashboard'))
        
    if request.method == 'POST':
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')
        
        user = query_db("SELECT * FROM users WHERE LOWER(email) = ? AND role = 'admin' AND is_active = 1", (email,), one=True)
        if user and check_password_hash(user['password_hash'], password):
            session['user_id'] = user['id']
            session['user_name'] = user['name']
            session['user_email'] = user['email']
            session['user_role'] = 'admin'
            session.permanent = True
            
            log_audit(user['id'], user['name'], 'ADMIN_LOGIN', 'AUTH', user['id'], {'email': email})
            flash(f"Welcome back Administrator, {user['name']}.", 'success')
            return redirect(url_for('admin.dashboard'))
        else:
            flash('Access denied. Invalid administrator credentials.', 'danger')
            
    return render_template('admin/login.html')

@auth_bp.route('/logout')
def logout():
    name = session.get('user_name', '')
    session.clear()
    flash('You have been securely signed out.', 'info')
    return redirect(url_for('store.home'))

@auth_bp.route('/admin/logout')
def admin_logout():
    session.clear()
    flash('Administrator signed out securely.', 'info')
    return redirect(url_for('auth.admin_login'))

@auth_bp.route('/account')
@login_required
def account():
    user = query_db("SELECT * FROM users WHERE id = ?", (session['user_id'],), one=True)
    orders = query_db("SELECT * FROM orders WHERE user_id = ? ORDER BY id DESC LIMIT 5", (session['user_id'],))
    addresses = query_db("SELECT * FROM user_addresses WHERE user_id = ? ORDER BY is_default DESC, id DESC", (session['user_id'],))
    return render_template('account/profile.html', user=user, orders=orders, addresses=addresses)

@auth_bp.route('/account/orders')
@login_required
def account_orders():
    orders = query_db("SELECT * FROM orders WHERE user_id = ? ORDER BY id DESC", (session['user_id'],))
    return render_template('account/orders.html', orders=orders)

@auth_bp.route('/account/order/<order_number>')
@login_required
def account_order_detail(order_number):
    order = query_db("SELECT * FROM orders WHERE order_number = ? AND user_id = ?", (order_number, session['user_id']), one=True)
    if not order:
        flash('Order not found or unauthorized.', 'warning')
        return redirect(url_for('auth.account_orders'))
        
    items = query_db("SELECT * FROM order_items WHERE order_id = ?", (order['id'],))
    history = query_db("SELECT * FROM order_status_history WHERE order_id = ? ORDER BY id ASC", (order['id'],))
    return render_template('account/order_detail.html', order=order, items=items, history=history)

@auth_bp.route('/account/address/add', methods=['POST'])
@login_required
def add_address():
    full_name = request.form.get('full_name', '').strip()
    phone = request.form.get('phone', '').strip()
    address_line1 = request.form.get('address_line1', '').strip()
    address_line2 = request.form.get('address_line2', '').strip()
    landmark = request.form.get('landmark', '').strip()
    city = request.form.get('city', '').strip()
    state = request.form.get('state', '').strip()
    pincode = request.form.get('pincode', '').strip()
    is_default = 1 if request.form.get('is_default') else 0
    
    if is_default:
        execute_db("UPDATE user_addresses SET is_default = 0 WHERE user_id = ?", (session['user_id'],))
        
    execute_db(
        """INSERT INTO user_addresses (user_id, full_name, phone, address_line1, address_line2, landmark, city, state, pincode, is_default)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        (session['user_id'], full_name, phone, address_line1, address_line2, landmark, city, state, pincode, is_default)
    )
    flash('Address saved successfully!', 'success')
    return redirect(url_for('auth.account'))

@auth_bp.route('/account/profile/update', methods=['POST'])
@login_required
def update_profile():
    name = request.form.get('name', '').strip()
    phone = request.form.get('phone', '').strip()
    new_password = request.form.get('new_password', '').strip()
    
    if not name:
        flash('Full name cannot be empty.', 'warning')
        return redirect(url_for('auth.account'))
        
    if new_password:
        if len(new_password) < 6:
            flash('New password must be at least 6 characters.', 'danger')
            return redirect(url_for('auth.account'))
        hashed = generate_password_hash(new_password, method='scrypt')
        execute_db(
            "UPDATE users SET name = ?, phone = ?, password_hash = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
            (name, phone, hashed, session['user_id'])
        )
    else:
        execute_db(
            "UPDATE users SET name = ?, phone = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
            (name, phone, session['user_id'])
        )
    session['user_name'] = name
    flash('Profile updated successfully!', 'success')
    return redirect(url_for('auth.account'))
