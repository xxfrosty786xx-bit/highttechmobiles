import json
import os
import re
from datetime import datetime, timedelta
from flask import Blueprint, render_template, request, redirect, url_for, flash, session, jsonify
from database import query_db, execute_db, log_audit, get_setting, set_setting, format_inr
from routes.auth import admin_required

admin_bp = Blueprint('admin', __name__, url_prefix='/admin')

@admin_bp.before_request
def check_admin_auth():
    # Allow login route through
    if request.endpoint == 'auth.admin_login':
        return
    if 'user_id' not in session or session.get('user_role') != 'admin':
        flash('Administrator authentication required to access this portal.', 'warning')
        return redirect(url_for('auth.admin_login', next=request.url))

@admin_bp.route('/')
def dashboard():
    # 1. KPI Stats
    # Revenue from eligible non-cancelled orders
    rev_row = query_db(
        "SELECT COALESCE(SUM(total_amount), 0) as total_rev FROM orders WHERE fulfilment_status != 'cancelled' AND payment_status != 'failed'",
        one=True
    )
    total_revenue = rev_row['total_rev'] if rev_row else 0.0
    
    total_orders = query_db("SELECT count(*) as c FROM orders", one=True)['c']
    pending_orders = query_db("SELECT count(*) as c FROM orders WHERE fulfilment_status IN ('pending', 'confirmed', 'processing')", one=True)['c']
    completed_orders = query_db("SELECT count(*) as c FROM orders WHERE fulfilment_status = 'delivered'", one=True)['c']
    cancelled_orders = query_db("SELECT count(*) as c FROM orders WHERE fulfilment_status = 'cancelled'", one=True)['c']
    
    total_customers = query_db("SELECT count(*) as c FROM users WHERE role = 'customer'", one=True)['c']
    active_products = query_db("SELECT count(*) as c FROM products WHERE is_published = 1", one=True)['c']
    low_stock = query_db("SELECT count(*) as c FROM products WHERE stock_quantity <= 5 AND is_published = 1", one=True)['c']
    
    # Recent orders
    recent_orders = query_db(
        "SELECT * FROM orders ORDER BY id DESC LIMIT 6"
    )
    
    # Low stock products list
    low_stock_products = query_db(
        """SELECT p.*, b.name as brand_name, pi.image_url
           FROM products p
           LEFT JOIN brands b ON p.brand_id = b.id
           LEFT JOIN product_images pi ON pi.product_id = p.id AND pi.is_primary = 1
           WHERE p.stock_quantity <= 5 AND p.is_published = 1
           ORDER BY p.stock_quantity ASC LIMIT 5"""
    )
    
    # Best-selling products from order_items
    top_selling = query_db(
        """SELECT p.name, p.slug, p.price, pi.image_url, SUM(oi.quantity) as units_sold, SUM(oi.total_price) as total_sales
           FROM order_items oi
           JOIN products p ON oi.product_id = p.id
           LEFT JOIN product_images pi ON pi.product_id = p.id AND pi.is_primary = 1
           GROUP BY p.id
           ORDER BY units_sold DESC LIMIT 5"""
    )
    
    # Recent audit logs
    recent_logs = query_db("SELECT * FROM audit_logs ORDER BY id DESC LIMIT 5")
    
    return render_template(
        'admin/dashboard.html',
        total_revenue=total_revenue,
        total_orders=total_orders,
        pending_orders=pending_orders,
        completed_orders=completed_orders,
        cancelled_orders=cancelled_orders,
        total_customers=total_customers,
        active_products=active_products,
        low_stock=low_stock,
        recent_orders=recent_orders,
        low_stock_products=low_stock_products,
        top_selling=top_selling,
        recent_logs=recent_logs,
        admin_name=session.get('user_name', 'Avid Malik & Danish Malik')
    )

# ----------------- PRODUCT MANAGEMENT -----------------
@admin_bp.route('/products')
def products():
    search = request.args.get('q', '').strip()
    category_id = request.args.get('category_id')
    brand_id = request.args.get('brand_id')
    status = request.args.get('status')
    
    sql = """
        SELECT p.*, b.name as brand_name, c.name as category_name, pi.image_url
        FROM products p
        LEFT JOIN brands b ON p.brand_id = b.id
        LEFT JOIN categories c ON p.category_id = c.id
        LEFT JOIN product_images pi ON pi.product_id = p.id AND pi.is_primary = 1
        WHERE 1=1
    """
    params = []
    
    if search:
        sql += " AND (p.name LIKE ? OR p.sku LIKE ? OR b.name LIKE ?)"
        term = f"%{search}%"
        params.extend([term, term, term])
    if category_id:
        sql += " AND p.category_id = ?"
        params.append(category_id)
    if brand_id:
        sql += " AND p.brand_id = ?"
        params.append(brand_id)
    if status == 'published':
        sql += " AND p.is_published = 1"
    elif status == 'draft':
        sql += " AND p.is_published = 0"
    elif status == 'low_stock':
        sql += " AND p.stock_quantity <= 5"
        
    sql += " ORDER BY p.id DESC"
    products_list = query_db(sql, params)
    
    categories = query_db("SELECT * FROM categories ORDER BY name ASC")
    brands = query_db("SELECT * FROM brands ORDER BY name ASC")
    
    return render_template(
        'admin/products.html',
        products=products_list,
        categories=categories,
        brands=brands,
        search=search,
        selected_category=category_id,
        selected_brand=brand_id,
        selected_status=status
    )

@admin_bp.route('/products/new', methods=['GET', 'POST'])
def product_new():
    categories = query_db("SELECT * FROM categories WHERE is_active = 1 ORDER BY name ASC")
    brands = query_db("SELECT * FROM brands WHERE is_active = 1 ORDER BY name ASC")
    
    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        sku = request.form.get('sku', '').strip().upper()
        brand_id = request.form.get('brand_id') or None
        category_id = request.form.get('category_id') or None
        price = float(request.form.get('price', 0))
        original_price = float(request.form.get('original_price')) if request.form.get('original_price') else None
        cost_price = float(request.form.get('cost_price')) if request.form.get('cost_price') else None
        stock = int(request.form.get('stock_quantity', 0))
        short_desc = request.form.get('short_description', '').strip()
        full_desc = request.form.get('full_description', '').strip()
        is_featured = 1 if request.form.get('is_featured') else 0
        is_bestseller = 1 if request.form.get('is_bestseller') else 0
        is_new = 1 if request.form.get('is_new') else 0
        is_published = 1 if request.form.get('is_published') else 0
        seo_title = request.form.get('seo_title', '').strip() or f"{name} - High Tech Mobile"
        seo_desc = request.form.get('seo_description', '').strip() or short_desc[:150]
        
        # Specs parsing from dynamic lines
        specs = {}
        spec_keys = request.form.getlist('spec_key[]')
        spec_vals = request.form.getlist('spec_val[]')
        for k, v in zip(spec_keys, spec_vals):
            if k.strip() and v.strip():
                specs[k.strip()] = v.strip()
                
        # Generate slug
        slug = re.sub(r'[^a-zA-Z0-9]+', '-', name.lower()).strip('-')
        # Check uniqueness
        existing = query_db("SELECT id FROM products WHERE slug = ?", (slug,), one=True)
        if existing:
            slug = f"{slug}-{sku.lower()}"
            
        product_id, _ = execute_db(
            """INSERT INTO products (
                name, slug, sku, brand_id, category_id, price, original_price, cost_price,
                stock_quantity, short_description, full_description, specifications_json,
                is_featured, is_bestseller, is_new, is_published, seo_title, seo_description
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                name, slug, sku, brand_id, category_id, price, original_price, cost_price,
                stock, short_desc, full_desc, json.dumps(specs),
                is_featured, is_bestseller, is_new, is_published, seo_title, seo_desc
            )
        )
        
        # Images
        image_urls = request.form.getlist('image_url[]')
        for idx, img in enumerate(image_urls):
            if img.strip():
                execute_db(
                    "INSERT INTO product_images (product_id, image_url, sort_order, is_primary) VALUES (?, ?, ?, ?)",
                    (product_id, img.strip(), idx, 1 if idx == 0 else 0)
                )
                
        # Variants
        var_colors = request.form.getlist('var_color[]')
        var_storages = request.form.getlist('var_storage[]')
        var_prices = request.form.getlist('var_price[]')
        var_stocks = request.form.getlist('var_stock[]')
        
        for c, s, p, st in zip(var_colors, var_storages, var_prices, var_stocks):
            if c.strip() or s.strip():
                add_p = float(p) if p else 0.0
                stk = int(st) if st else 0
                v_sku = f"{sku}-{c[:3].upper()}-{s}".replace(' ', '')
                execute_db(
                    """INSERT INTO product_variants (product_id, color_name, storage, additional_price, stock_quantity, sku)
                       VALUES (?, ?, ?, ?, ?, ?)""",
                    (product_id, c.strip(), s.strip(), add_p, stk, v_sku)
                )
                
        log_audit(session['user_id'], session['user_name'], 'CREATE_PRODUCT', 'PRODUCT', product_id, {'name': name, 'sku': sku})
        flash(f"Product '{name}' created successfully!", 'success')
        return redirect(url_for('admin.products'))
        
    return render_template('admin/product_form.html', product=None, categories=categories, brands=brands, images=[], variants=[], specs={})

@admin_bp.route('/products/<int:id>/edit', methods=['GET', 'POST'])
def product_edit(id):
    product = query_db("SELECT * FROM products WHERE id = ?", (id,), one=True)
    if not product:
        flash('Product not found.', 'danger')
        return redirect(url_for('admin.products'))
        
    categories = query_db("SELECT * FROM categories WHERE is_active = 1 ORDER BY name ASC")
    brands = query_db("SELECT * FROM brands WHERE is_active = 1 ORDER BY name ASC")
    images = query_db("SELECT * FROM product_images WHERE product_id = ? ORDER BY sort_order ASC", (id,))
    variants = query_db("SELECT * FROM product_variants WHERE product_id = ? ORDER BY id ASC", (id,))
    
    specs = {}
    if product['specifications_json']:
        try:
            specs = json.loads(product['specifications_json'])
        except Exception:
            specs = {}
            
    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        sku = request.form.get('sku', '').strip().upper()
        brand_id = request.form.get('brand_id') or None
        category_id = request.form.get('category_id') or None
        price = float(request.form.get('price', 0))
        original_price = float(request.form.get('original_price')) if request.form.get('original_price') else None
        cost_price = float(request.form.get('cost_price')) if request.form.get('cost_price') else None
        stock = int(request.form.get('stock_quantity', 0))
        short_desc = request.form.get('short_description', '').strip()
        full_desc = request.form.get('full_description', '').strip()
        is_featured = 1 if request.form.get('is_featured') else 0
        is_bestseller = 1 if request.form.get('is_bestseller') else 0
        is_new = 1 if request.form.get('is_new') else 0
        is_published = 1 if request.form.get('is_published') else 0
        seo_title = request.form.get('seo_title', '').strip()
        seo_desc = request.form.get('seo_description', '').strip()
        
        # Specs
        new_specs = {}
        spec_keys = request.form.getlist('spec_key[]')
        spec_vals = request.form.getlist('spec_val[]')
        for k, v in zip(spec_keys, spec_vals):
            if k.strip() and v.strip():
                new_specs[k.strip()] = v.strip()
                
        execute_db(
            """UPDATE products SET
                name = ?, sku = ?, brand_id = ?, category_id = ?, price = ?, original_price = ?,
                cost_price = ?, stock_quantity = ?, short_description = ?, full_description = ?,
                specifications_json = ?, is_featured = ?, is_bestseller = ?, is_new = ?,
                is_published = ?, seo_title = ?, seo_description = ?, updated_at = CURRENT_TIMESTAMP
               WHERE id = ?""",
            (
                name, sku, brand_id, category_id, price, original_price, cost_price,
                stock, short_desc, full_desc, json.dumps(new_specs),
                is_featured, is_bestseller, is_new, is_published, seo_title, seo_desc, id
            )
        )
        
        # Update images
        execute_db("DELETE FROM product_images WHERE product_id = ?", (id,))
        image_urls = request.form.getlist('image_url[]')
        for idx, img in enumerate(image_urls):
            if img.strip():
                execute_db(
                    "INSERT INTO product_images (product_id, image_url, sort_order, is_primary) VALUES (?, ?, ?, ?)",
                    (id, img.strip(), idx, 1 if idx == 0 else 0)
                )
                
        # Update variants
        execute_db("DELETE FROM product_variants WHERE product_id = ?", (id,))
        var_colors = request.form.getlist('var_color[]')
        var_storages = request.form.getlist('var_storage[]')
        var_prices = request.form.getlist('var_price[]')
        var_stocks = request.form.getlist('var_stock[]')
        for c, s, p, st in zip(var_colors, var_storages, var_prices, var_stocks):
            if c.strip() or s.strip():
                add_p = float(p) if p else 0.0
                stk = int(st) if st else 0
                v_sku = f"{sku}-{c[:3].upper()}-{s}".replace(' ', '')
                execute_db(
                    """INSERT INTO product_variants (product_id, color_name, storage, additional_price, stock_quantity, sku)
                       VALUES (?, ?, ?, ?, ?, ?)""",
                    (id, c.strip(), s.strip(), add_p, stk, v_sku)
                )
                
        log_audit(session['user_id'], session['user_name'], 'UPDATE_PRODUCT', 'PRODUCT', id, {'name': name, 'sku': sku})
        flash(f"Product '{name}' updated successfully!", 'success')
        return redirect(url_for('admin.products'))
        
    return render_template(
        'admin/product_form.html',
        product=product,
        categories=categories,
        brands=brands,
        images=images,
        variants=variants,
        specs=specs
    )

@admin_bp.route('/products/<int:id>/delete', methods=['POST'])
def product_delete(id):
    product = query_db("SELECT name FROM products WHERE id = ?", (id,), one=True)
    if product:
        execute_db("DELETE FROM products WHERE id = ?", (id,))
        log_audit(session['user_id'], session['user_name'], 'DELETE_PRODUCT', 'PRODUCT', id, {'name': product['name']})
        flash(f"Product '{product['name']}' has been permanently deleted.", 'success')
    return redirect(url_for('admin.products'))

# ----------------- ORDERS MANAGEMENT -----------------
@admin_bp.route('/orders')
def orders():
    status = request.args.get('status')
    search = request.args.get('q', '').strip()
    
    sql = "SELECT * FROM orders WHERE 1=1"
    params = []
    
    if status:
        sql += " AND fulfilment_status = ?"
        params.append(status)
    if search:
        sql += " AND (order_number LIKE ? OR customer_name LIKE ? OR customer_email LIKE ? OR customer_phone LIKE ?)"
        term = f"%{search}%"
        params.extend([term, term, term, term])
        
    sql += " ORDER BY id DESC"
    orders_list = query_db(sql, params)
    
    # Parse pickup info for each order
    formatted_orders = []
    for o in orders_list:
        od = dict(o)
        try:
            pickup_data = json.loads(od['shipping_address_json'])
            od['pickup_date'] = pickup_data.get('preferred_date', 'N/A')
            od['pickup_time'] = pickup_data.get('preferred_time', '')
        except Exception:
            od['pickup_date'] = 'Showroom Visit'
            od['pickup_time'] = ''
        formatted_orders.append(od)
        
    return render_template('admin/orders.html', orders=formatted_orders, current_status=status, search=search)

@admin_bp.route('/orders/<int:id>')
def order_detail(id):
    order = query_db("SELECT * FROM orders WHERE id = ?", (id,), one=True)
    if not order:
        flash('Order not found.', 'danger')
        return redirect(url_for('admin.orders'))
        
    items = query_db("SELECT * FROM order_items WHERE order_id = ?", (id,))
    history = query_db("SELECT * FROM order_status_history WHERE order_id = ? ORDER BY id ASC", (id,))
    address = json.loads(order['shipping_address_json'])
    
    return render_template('admin/order_detail.html', order=order, items=items, history=history, address=address)

@admin_bp.route('/orders/<int:id>/update-status', methods=['POST'])
def order_update_status(id):
    order = query_db("SELECT * FROM orders WHERE id = ?", (id,), one=True)
    if not order:
        flash('Order not found.', 'danger')
        return redirect(url_for('admin.orders'))
        
    new_fulfilment = request.form.get('fulfilment_status')
    new_payment = request.form.get('payment_status')
    courier_name = request.form.get('courier_name', '').strip()
    tracking_number = request.form.get('tracking_number', '').strip()
    notes = request.form.get('notes', '').strip()
    
    if new_fulfilment and new_fulfilment != order['fulfilment_status']:
        execute_db(
            """INSERT INTO order_status_history (order_id, old_status, new_status, changed_by, notes)
               VALUES (?, ?, ?, ?, ?)""",
            (id, order['fulfilment_status'], new_fulfilment, session['user_name'], notes or f"Status changed to {new_fulfilment}")
        )
        
    execute_db(
        """UPDATE orders SET
            fulfilment_status = COALESCE(?, fulfilment_status),
            payment_status = COALESCE(?, payment_status),
            courier_name = COALESCE(?, courier_name),
            tracking_number = COALESCE(?, tracking_number),
            notes = COALESCE(?, notes),
            updated_at = CURRENT_TIMESTAMP
           WHERE id = ?""",
        (new_fulfilment, new_payment, courier_name, tracking_number, notes, id)
    )
    
    log_audit(
        session['user_id'], session['user_name'], 'UPDATE_ORDER_STATUS', 'ORDER', id,
        {'order_number': order['order_number'], 'new_status': new_fulfilment, 'courier': courier_name, 'tracking': tracking_number}
    )
    
    flash(f"Order #{order['order_number']} status updated successfully.", 'success')
    return redirect(url_for('admin.order_detail', id=id))

# ----------------- CATEGORIES & BRANDS -----------------
@admin_bp.route('/categories', methods=['GET', 'POST'])
def categories():
    if request.method == 'POST':
        action = request.form.get('action')
        if action == 'add_category':
            name = request.form.get('name', '').strip()
            slug = re.sub(r'[^a-zA-Z0-9]+', '-', name.lower()).strip('-')
            desc = request.form.get('description', '').strip()
            img = request.form.get('image_url', '').strip()
            order = int(request.form.get('sort_order', 0))
            execute_db(
                "INSERT INTO categories (name, slug, description, image_url, sort_order) VALUES (?, ?, ?, ?, ?)",
                (name, slug, desc, img, order)
            )
            flash(f"Category '{name}' created.", 'success')
        elif action == 'add_brand':
            name = request.form.get('name', '').strip()
            slug = re.sub(r'[^a-zA-Z0-9]+', '-', name.lower()).strip('-')
            logo = request.form.get('logo_url', '').strip()
            execute_db("INSERT INTO brands (name, slug, logo_url) VALUES (?, ?, ?)", (name, slug, logo))
            flash(f"Brand '{name}' added.", 'success')
        return redirect(url_for('admin.categories'))
        
    cats = query_db("SELECT c.*, count(p.id) as product_count FROM categories c LEFT JOIN products p ON c.id = p.category_id GROUP BY c.id ORDER BY c.sort_order ASC")
    brands_list = query_db("SELECT b.*, count(p.id) as product_count FROM brands b LEFT JOIN products p ON b.id = p.brand_id GROUP BY b.id ORDER BY b.name ASC")
    return render_template('admin/categories.html', categories=cats, brands=brands_list)

@admin_bp.route('/categories/<int:id>/toggle', methods=['POST'])
def category_toggle(id):
    cat = query_db("SELECT is_active, name FROM categories WHERE id = ?", (id,), one=True)
    if cat:
        new_state = 0 if cat['is_active'] else 1
        execute_db("UPDATE categories SET is_active = ? WHERE id = ?", (new_state, id))
        flash(f"Category '{cat['name']}' status updated.", 'info')
    return redirect(url_for('admin.categories'))

# ----------------- CUSTOMERS -----------------
@admin_bp.route('/customers')
def customers():
    search = request.args.get('q', '').strip()
    sql = """
        SELECT u.id, u.name, u.email, u.phone, u.created_at, u.is_active,
               count(o.id) as order_count, COALESCE(SUM(o.total_amount), 0) as total_spent
        FROM users u
        LEFT JOIN orders o ON u.id = o.user_id AND o.fulfilment_status != 'cancelled'
        WHERE u.role = 'customer'
    """
    params = []
    if search:
        sql += " AND (u.name LIKE ? OR u.email LIKE ? OR u.phone LIKE ?)"
        term = f"%{search}%"
        params.extend([term, term, term])
    sql += " GROUP BY u.id ORDER BY u.id DESC"
    
    customers_list = query_db(sql, params)
    return render_template('admin/customers.html', customers=customers_list, search=search)

# ----------------- COUPONS -----------------
@admin_bp.route('/coupons', methods=['GET', 'POST'])
def coupons():
    if request.method == 'POST':
        code = request.form.get('code', '').strip().upper()
        dtype = request.form.get('discount_type', 'percentage')
        dval = float(request.form.get('discount_value', 0))
        min_order = float(request.form.get('min_order_amount', 0))
        max_disc = float(request.form.get('max_discount_amount')) if request.form.get('max_discount_amount') else None
        limit = int(request.form.get('usage_limit')) if request.form.get('usage_limit') else None
        expires_at = request.form.get('expires_at') or None
        
        execute_db(
            """INSERT INTO coupons (code, discount_type, discount_value, min_order_amount, max_discount_amount, usage_limit, expires_at)
               VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (code, dtype, dval, min_order, max_disc, limit, expires_at)
        )
        flash(f"Coupon '{code}' created successfully.", 'success')
        return redirect(url_for('admin.coupons'))
        
    coupons_list = query_db("SELECT * FROM coupons ORDER BY id DESC")
    return render_template('admin/coupons.html', coupons=coupons_list)

@admin_bp.route('/coupons/<int:id>/toggle', methods=['POST'])
def coupon_toggle(id):
    c = query_db("SELECT is_active, code FROM coupons WHERE id = ?", (id,), one=True)
    if c:
        execute_db("UPDATE coupons SET is_active = ? WHERE id = ?", (0 if c['is_active'] else 1, id))
        flash(f"Coupon '{c['code']}' status updated.", 'info')
    return redirect(url_for('admin.coupons'))

# ----------------- HOMEPAGE & PROMOTIONS EDITOR -----------------
@admin_bp.route('/homepage', methods=['GET', 'POST'])
def homepage_editor():
    if request.method == 'POST':
        set_setting('announcement_text', request.form.get('announcement_text', ''))
        set_setting('announcement_active', '1' if request.form.get('announcement_active') else '0')
        set_setting('hero_badge', request.form.get('hero_badge', ''))
        set_setting('hero_title', request.form.get('hero_title', ''))
        set_setting('hero_subtitle', request.form.get('hero_subtitle', ''))
        set_setting('hero_primary_btn_text', request.form.get('hero_primary_btn_text', ''))
        set_setting('hero_primary_btn_url', request.form.get('hero_primary_btn_url', ''))
        set_setting('hero_secondary_btn_text', request.form.get('hero_secondary_btn_text', ''))
        set_setting('hero_secondary_btn_url', request.form.get('hero_secondary_btn_url', ''))
        
        log_audit(session['user_id'], session['user_name'], 'UPDATE_HOMEPAGE_SETTINGS', 'SETTINGS')
        flash('Homepage content updated instantly!', 'success')
        return redirect(url_for('admin.homepage_editor'))
        
    settings = {
        'announcement_text': get_setting('announcement_text', ''),
        'announcement_active': get_setting('announcement_active', '1'),
        'hero_badge': get_setting('hero_badge', ''),
        'hero_title': get_setting('hero_title', ''),
        'hero_subtitle': get_setting('hero_subtitle', ''),
        'hero_primary_btn_text': get_setting('hero_primary_btn_text', ''),
        'hero_primary_btn_url': get_setting('hero_primary_btn_url', ''),
        'hero_secondary_btn_text': get_setting('hero_secondary_btn_text', ''),
        'hero_secondary_btn_url': get_setting('hero_secondary_btn_url', '')
    }
    return render_template('admin/homepage_editor.html', settings=settings)

# ----------------- STORE SETTINGS -----------------
@admin_bp.route('/settings', methods=['GET', 'POST'])
def settings():
    if request.method == 'POST':
        set_setting('store_name', request.form.get('store_name', 'HIGH TECH MOBILE'))
        set_setting('store_tagline', request.form.get('store_tagline', ''))
        set_setting('contact_email', request.form.get('contact_email', ''))
        set_setting('contact_phone', request.form.get('contact_phone', ''))
        set_setting('store_address', request.form.get('store_address', ''))
        set_setting('free_shipping_threshold', request.form.get('free_shipping_threshold', '999'))
        set_setting('default_shipping_fee', request.form.get('default_shipping_fee', '99'))
        set_setting('cod_enabled', '1' if request.form.get('cod_enabled') else '0')
        set_setting('cod_fee', request.form.get('cod_fee', '0'))
        set_setting('tax_rate', request.form.get('tax_rate', '18'))
        set_setting('razorpay_enabled', '1' if request.form.get('razorpay_enabled') else '0')
        
        log_audit(session['user_id'], session['user_name'], 'UPDATE_STORE_SETTINGS', 'SETTINGS')
        flash('Store configurations and settings updated successfully.', 'success')
        return redirect(url_for('admin.settings'))
        
    keys = [
        'store_name', 'store_tagline', 'contact_email', 'contact_phone', 'store_address',
        'free_shipping_threshold', 'default_shipping_fee', 'cod_enabled', 'cod_fee', 'tax_rate',
        'razorpay_enabled'
    ]
    store_config = {k: get_setting(k, '') for k in keys}
    return render_template('admin/settings.html', config=store_config)

# ----------------- AUDIT LOGS -----------------
@admin_bp.route('/audit-logs')
def audit_logs():
    logs = query_db("SELECT * FROM audit_logs ORDER BY id DESC LIMIT 100")
    return render_template('admin/audit_logs.html', logs=logs)
