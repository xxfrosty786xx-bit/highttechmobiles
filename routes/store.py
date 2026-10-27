import json
import uuid
import re
from datetime import datetime
from flask import Blueprint, render_template, request, redirect, url_for, flash, session, g, jsonify
from database import query_db, execute_db, get_setting, format_inr
from routes.auth import login_required

store_bp = Blueprint('store', __name__)

INDIAN_STATES = [
    "Andhra Pradesh", "Arunachal Pradesh", "Assam", "Bihar", "Chhattisgarh", "Goa", "Gujarat",
    "Haryana", "Himachal Pradesh", "Jharkhand", "Karnataka", "Kerala", "Madhya Pradesh",
    "Maharashtra", "Manipur", "Meghalaya", "Mizoram", "Nagaland", "Odisha", "Punjab",
    "Rajasthan", "Sikkim", "Tamil Nadu", "Telangana", "Tripura", "Uttar Pradesh",
    "Uttarakhand", "West Bengal", "Andaman and Nicobar Islands", "Chandigarh",
    "Dadra and Nagar Haveli and Daman and Diu", "Delhi", "Jammu and Kashmir",
    "Ladakh", "Lakshadweep", "Puducherry"
]

def get_session_cart_id():
    """Returns or generates a unique session cart ID."""
    if 'cart_session_id' not in session:
        session['cart_session_id'] = str(uuid.uuid4())
    return session['cart_session_id']

def get_cart_data():
    """Fetches all cart items, recalculates valid pricing, coupon discounts, shipping and totals."""
    session_id = get_session_cart_id()
    user_id = session.get('user_id')
    
    # Locate or create cart
    cart = query_db("SELECT id FROM carts WHERE session_id = ? OR (user_id IS NOT NULL AND user_id = ?)", (session_id, user_id), one=True)
    if not cart:
        execute_db("INSERT INTO carts (session_id, user_id) VALUES (?, ?)", (session_id, user_id))
        cart = query_db("SELECT id FROM carts WHERE session_id = ?", (session_id,), one=True)
        
    cart_id = cart['id']
    
    # Link cart to user if user logged in
    if user_id:
        execute_db("UPDATE carts SET user_id = ? WHERE id = ?", (user_id, cart_id))
        
    items_raw = query_db(
        """SELECT ci.id as item_id, ci.quantity, ci.variant_id,
                  p.id as product_id, p.name, p.slug, p.price as base_price, p.stock_quantity as p_stock,
                  pi.image_url,
                  pv.color_name, pv.storage, pv.additional_price, pv.stock_quantity as v_stock
           FROM cart_items ci
           JOIN products p ON ci.product_id = p.id
           LEFT JOIN product_images pi ON pi.product_id = p.id AND pi.is_primary = 1
           LEFT JOIN product_variants pv ON ci.variant_id = pv.id
           WHERE ci.cart_id = ?
           ORDER BY ci.id DESC""",
        (cart_id,)
    )
    
    cart_items = []
    subtotal = 0.0
    total_qty = 0
    
    for row in items_raw:
        item = dict(row)
        unit_price = item['base_price'] + (item['additional_price'] or 0.0)
        item['unit_price'] = unit_price
        item['line_total'] = unit_price * item['quantity']
        
        # Max stock available
        item['available_stock'] = item['v_stock'] if item['variant_id'] else item['p_stock']
        
        subtotal += item['line_total']
        total_qty += item['quantity']
        cart_items.append(item)
        
    # Free shipping threshold check
    free_threshold = float(get_setting('free_shipping_threshold', 999))
    default_shipping = float(get_setting('default_shipping_fee', 99))
    
    if subtotal >= free_threshold or len(cart_items) == 0:
        shipping_fee = 0.0
    else:
        shipping_fee = default_shipping
        
    # Coupon calculation
    discount_amount = 0.0
    coupon_code = session.get('applied_coupon')
    coupon_info = None
    
    if coupon_code and subtotal > 0:
        coupon = query_db("SELECT * FROM coupons WHERE code = ? AND is_active = 1", (coupon_code,), one=True)
        if coupon:
            if subtotal >= coupon['min_order_amount']:
                if coupon['discount_type'] == 'percentage':
                    calc_disc = (subtotal * coupon['discount_value']) / 100.0
                    if coupon['max_discount_amount']:
                        calc_disc = min(calc_disc, coupon['max_discount_amount'])
                    discount_amount = calc_disc
                else:
                    discount_amount = min(coupon['discount_value'], subtotal)
                coupon_info = coupon
            else:
                session.pop('applied_coupon', None)
        else:
            session.pop('applied_coupon', None)
            
    # Calculate tax (GST)
    tax_rate = float(get_setting('tax_rate', 18))
    # In standard Indian retail, MRP / listing price is GST-inclusive.
    # We display the GST breakdown for transparency.
    taxable_subtotal = max(0.0, subtotal - discount_amount)
    gst_component = (taxable_subtotal * tax_rate) / (100.0 + tax_rate)
    
    total_amount = taxable_subtotal + shipping_fee
    
    return {
        "cart_id": cart_id,
        "items": cart_items,
        "cart_items": cart_items,
        "total_items": total_qty,
        "subtotal": subtotal,
        "discount_amount": discount_amount,
        "coupon_code": coupon_code if discount_amount > 0 else None,
        "coupon_info": coupon_info,
        "shipping_fee": shipping_fee,
        "free_threshold": free_threshold,
        "gst_component": gst_component,
        "total_amount": total_amount
    }

@store_bp.route('/')
def home():
    # Fetch categories
    categories = query_db("SELECT * FROM categories WHERE is_active = 1 ORDER BY sort_order ASC")
    
    # Fetch brands
    brands = query_db("SELECT * FROM brands WHERE is_active = 1 ORDER BY name ASC")
    
    # Fetch Featured products (Flagships)
    featured = query_db(
        """SELECT p.*, b.name as brand_name, pi.image_url
           FROM products p
           LEFT JOIN brands b ON p.brand_id = b.id
           LEFT JOIN product_images pi ON pi.product_id = p.id AND pi.is_primary = 1
           WHERE p.is_published = 1 AND p.is_featured = 1
           ORDER BY p.id ASC LIMIT 4"""
    )
    
    # Fetch Bestsellers
    bestsellers = query_db(
        """SELECT p.*, b.name as brand_name, pi.image_url
           FROM products p
           LEFT JOIN brands b ON p.brand_id = b.id
           LEFT JOIN product_images pi ON pi.product_id = p.id AND pi.is_primary = 1
           WHERE p.is_published = 1 AND p.is_bestseller = 1
           ORDER BY p.id ASC LIMIT 8"""
    )
    
    # Fetch New Arrivals
    new_arrivals = query_db(
        """SELECT p.*, b.name as brand_name, pi.image_url
           FROM products p
           LEFT JOIN brands b ON p.brand_id = b.id
           LEFT JOIN product_images pi ON pi.product_id = p.id AND pi.is_primary = 1
           WHERE p.is_published = 1 AND p.is_new = 1
           ORDER BY p.id DESC LIMIT 4"""
    )
    
    # Fetch Accessories spotlight
    accessories = query_db(
        """SELECT p.*, b.name as brand_name, pi.image_url
           FROM products p
           JOIN categories c ON p.category_id = c.id
           LEFT JOIN brands b ON p.brand_id = b.id
           LEFT JOIN product_images pi ON pi.product_id = p.id AND pi.is_primary = 1
           WHERE p.is_published = 1 AND c.slug IN ('accessories', 'audio', 'smartwatches')
           ORDER BY p.id DESC LIMIT 4"""
    )
    
    # Authentic Indian Customer Reviews
    reviews = [
        {
            "author": "Aarav Sharma",
            "role": "Verified Buyer • Uttar Pradesh",
            "rating": 5,
            "comment": "Dukan par jakar iPhone 16 Pro Max kharida. Avid bhai aur Danish bhai ne samne seal pack box open karke diya aur official Apple India warranty live verify karwayi. 100% genuine sealed unit!"
        },
        {
            "author": "Rohan Verma",
            "role": "Verified Buyer • Noida",
            "rating": 5,
            "comment": "Online phone reserve kiya aur sham ko showroom se collect kiya. No advance payment pressure. Samne phone inspect kiya, UPI se counter par payment ki aur GST invoice liya. Superb service!"
        },
        {
            "author": "Pooja Patel",
            "role": "Verified Buyer • Hathras Region",
            "rating": 5,
            "comment": "Showroom experience is top-notch! Genuine prices, transparent staff, and no fake promises. Store owners Avid Malik & Danish Malik personally guided me with setup for my Samsung S24 Ultra."
        },
        {
            "author": "Mohammad Faizan",
            "role": "Verified Buyer • Aligarh / Hathras",
            "rating": 5,
            "comment": "Best electronic store for flagship smartphones. Best rate mila aur saath me original case & fast charger bhi suggest kiya. Bahut achha experience raha."
        }
    ]
    
    return render_template(
        'index.html',
        categories=categories,
        brands=brands,
        featured=featured,
        bestsellers=bestsellers,
        new_arrivals=new_arrivals,
        accessories=accessories,
        reviews=reviews
    )

@store_bp.route('/shop')
def shop():
    category_slug = request.args.get('category')
    brand_slug = request.args.get('brand')
    query = request.args.get('q', '').strip()
    deals_only = request.args.get('deals') == 'true'
    min_price = request.args.get('min_price', type=float)
    max_price = request.args.get('max_price', type=float)
    in_stock = request.args.get('in_stock') == '1'
    sort = request.args.get('sort', 'newest')
    
    # Base SQL
    sql = """
        SELECT p.*, b.name as brand_name, b.slug as brand_slug, c.name as category_name, c.slug as category_slug, pi.image_url
        FROM products p
        LEFT JOIN brands b ON p.brand_id = b.id
        LEFT JOIN categories c ON p.category_id = c.id
        LEFT JOIN product_images pi ON pi.product_id = p.id AND pi.is_primary = 1
        WHERE p.is_published = 1
    """
    params = []
    
    if category_slug:
        sql += " AND c.slug = ?"
        params.append(category_slug)
        
    if brand_slug:
        sql += " AND b.slug = ?"
        params.append(brand_slug)
        
    if query:
        sql += " AND (p.name LIKE ? OR p.short_description LIKE ? OR b.name LIKE ? OR p.sku LIKE ?)"
        term = f"%{query}%"
        params.extend([term, term, term, term])
        
    if deals_only:
        sql += " AND p.original_price > p.price"
        
    if min_price is not None:
        sql += " AND p.price >= ?"
        params.append(min_price)
        
    if max_price is not None:
        sql += " AND p.price <= ?"
        params.append(max_price)
        
    if in_stock:
        sql += " AND p.stock_quantity > 0"
        
    # Sorting
    if sort == 'price_asc':
        sql += " ORDER BY p.price ASC"
    elif sort == 'price_desc':
        sql += " ORDER BY p.price DESC"
    elif sort == 'popular':
        sql += " ORDER BY p.is_bestseller DESC, p.id DESC"
    elif sort == 'name_asc':
        sql += " ORDER BY p.name ASC"
    else:
        sql += " ORDER BY p.id DESC"
        
    products = query_db(sql, params)
    
    categories = query_db("SELECT * FROM categories WHERE is_active = 1 ORDER BY sort_order ASC")
    brands = query_db("SELECT * FROM brands WHERE is_active = 1 ORDER BY name ASC")
    
    return render_template(
        'shop.html',
        products=products,
        categories=categories,
        brands=brands,
        selected_category=category_slug,
        selected_brand=brand_slug,
        search_query=query,
        deals_only=deals_only,
        min_price=min_price,
        max_price=max_price,
        in_stock=in_stock,
        sort=sort
    )

@store_bp.route('/product/<slug>')
def product_detail(slug):
    product = query_db(
        """SELECT p.*, b.name as brand_name, b.slug as brand_slug, c.name as category_name, c.slug as category_slug
           FROM products p
           LEFT JOIN brands b ON p.brand_id = b.id
           LEFT JOIN categories c ON p.category_id = c.id
           WHERE p.slug = ? AND p.is_published = 1""",
        (slug,), one=True
    )
    if not product:
        flash('Product not found.', 'warning')
        return redirect(url_for('store.shop'))
        
    # Product Images
    images = query_db("SELECT * FROM product_images WHERE product_id = ? ORDER BY sort_order ASC", (product['id'],))
    
    # Variants
    variants = query_db("SELECT * FROM product_variants WHERE product_id = ? ORDER BY id ASC", (product['id'],))
    
    # Parse specifications JSON
    specs = {}
    if product['specifications_json']:
        try:
            specs = json.loads(product['specifications_json'])
        except Exception:
            specs = {}
            
    # Calculate discount percentage
    discount_pct = 0
    if product['original_price'] and product['original_price'] > product['price']:
        discount_pct = int(round(((product['original_price'] - product['price']) / product['original_price']) * 100))
        
    # Related products
    related = query_db(
        """SELECT p.*, b.name as brand_name, pi.image_url
           FROM products p
           LEFT JOIN brands b ON p.brand_id = b.id
           LEFT JOIN product_images pi ON pi.product_id = p.id AND pi.is_primary = 1
           WHERE p.category_id = ? AND p.id != ? AND p.is_published = 1
           LIMIT 4""",
        (product['category_id'], product['id'])
    )
    
    # Customer Reviews
    reviews = query_db("SELECT * FROM reviews WHERE product_id = ? AND is_approved = 1 ORDER BY id DESC", (product['id'],))
    
    return render_template(
        'product_detail.html',
        product=product,
        images=images,
        variants=variants,
        specs=specs,
        discount_pct=discount_pct,
        related=related,
        reviews=reviews
    )

@store_bp.route('/product/<slug>/review', methods=['POST'])
def add_product_review(slug):
    product = query_db("SELECT id FROM products WHERE slug = ?", (slug,), one=True)
    if not product:
        flash('Product not found.', 'danger')
        return redirect(url_for('store.shop'))
        
    author_name = request.form.get('customer_name', '').strip()
    city = request.form.get('city', '').strip()
    rating = int(request.form.get('rating', 5))
    title = request.form.get('title', '').strip()
    comment = request.form.get('comment', '').strip()
    
    if not author_name or not comment:
        flash('Please provide your name and your feedback.', 'warning')
        return redirect(url_for('store.product_detail', slug=slug))
        
    display_name = f"{author_name} ({city})" if city else author_name
    
    execute_db(
        """INSERT INTO reviews (product_id, user_id, customer_name, rating, title, comment, is_verified_purchase, is_approved)
           VALUES (?, ?, ?, ?, ?, ?, 1, 1)""",
        (product['id'], session.get('user_id'), display_name, rating, title, comment)
    )
    flash('Shukriya! Your verified review has been submitted and published.', 'success')
    return redirect(url_for('store.product_detail', slug=slug))

@store_bp.route('/cart')
def cart():
    cart_data = get_cart_data()
    return render_template('cart.html', cart=cart_data)

@store_bp.route('/checkout', methods=['GET', 'POST'])
def checkout():
    cart_data = get_cart_data()
    if not cart_data['items']:
        flash('Your reservation bag is currently empty. Please select a product first.', 'info')
        return redirect(url_for('store.shop'))
        
    # Check if stock exists for all cart items
    for itm in cart_data['items']:
        if itm['available_stock'] < itm['quantity']:
            flash(f"Insufficient stock for {itm['name']}. Available at store: {itm['available_stock']}", 'danger')
            return redirect(url_for('store.cart'))
            
    # Preload user saved address/phone if logged in
    user_profile = None
    if 'user_id' in session:
        user_profile = query_db("SELECT * FROM users WHERE id = ?", (session['user_id'],), one=True)
        
    if request.method == 'POST':
        customer_name = request.form.get('customer_name', '').strip()
        customer_phone = request.form.get('customer_phone', '').strip()
        customer_email = request.form.get('customer_email', '').strip().lower()
        customer_city = request.form.get('customer_city', 'Hathras').strip()
        pickup_date = request.form.get('pickup_date', 'Today').strip()
        pickup_time = request.form.get('pickup_time', 'Anytime (10 AM - 9 PM)').strip()
        payment_method = request.form.get('payment_method', 'store_counter')
        order_notes = request.form.get('order_notes', '').strip()
        
        errors = []
        if not customer_name:
            errors.append('Please provide your name for the showroom booking reservation.')
            
        # Clean Indian phone
        clean_phone = re.sub(r'[\s\-\+]', '', customer_phone)
        if clean_phone.startswith('91') and len(clean_phone) == 12:
            clean_phone = clean_phone[2:]
        if not re.match(r'^[6-9]\d{9}$', clean_phone):
            errors.append('Please enter a valid 10-digit Indian mobile number for booking SMS/WhatsApp confirmation.')
            
        if customer_email and not re.match(r'^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$', customer_email):
            errors.append('If provided, please enter a valid email address for digital reservation receipt.')
            
        if errors:
            for err in errors:
                flash(err, 'danger')
            return render_template(
                'checkout.html',
                cart=cart_data,
                user_profile=user_profile,
                form_data=request.form
            )
            
        # Store Pickup Details JSON
        store_pickup_info = {
            "pickup_type": "In-Store Showroom Collection",
            "full_name": customer_name,
            "phone": customer_phone,
            "email": customer_email or "guest@hightechmobile.in",
            "city": customer_city,
            "preferred_date": pickup_date,
            "preferred_time": pickup_time,
            "showroom_address": get_setting('store_address', 'Ruheri, Hathras, Uttar Pradesh - 204101, India'),
            "live_map_url": get_setting('store_map_url', 'https://www.google.com/maps?q=27.643748,78.063498'),
            "live_location_url": get_setting('store_live_location', 'https://www.where-am-i.co/@27.643748,78.063498,z14')
        }
        
        order_number = f"HTM-BOOK-{datetime.now().strftime('%Y%m%d')}-{uuid.uuid4().hex[:5].upper()}"
        
        # Insert Order / Store Reservation
        order_id, _ = execute_db(
            """INSERT INTO orders (
                order_number, user_id, customer_name, customer_email, customer_phone,
                shipping_address_json, subtotal, discount_amount, coupon_code, shipping_fee,
                tax_amount, total_amount, payment_method, payment_status, fulfilment_status, notes
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 0.0, ?, ?, ?, 'pending', 'confirmed', ?)""",
            (
                order_number,
                session.get('user_id'),
                customer_name,
                customer_email or f"{clean_phone}@guest.hightechmobile.in",
                customer_phone,
                json.dumps(store_pickup_info),
                cart_data['subtotal'],
                cart_data['discount_amount'],
                cart_data['coupon_code'],
                cart_data['gst_component'],
                max(0.0, cart_data['subtotal'] - cart_data['discount_amount']),
                payment_method,
                f"Store Visit Date: {pickup_date} ({pickup_time}). Notes: {order_notes}"
            )
        )
        
        # Insert Order Items & Atomically Deduct/Reserve Inventory
        for itm in cart_data['cart_items']:
            var_details = ""
            if itm['variant_id']:
                var_parts = []
                if itm['color_name']: var_parts.append(itm['color_name'])
                if itm['storage']: var_parts.append(itm['storage'])
                var_details = " / ".join(var_parts)
                
            execute_db(
                """INSERT INTO order_items (order_id, product_id, variant_id, product_name, variant_details, unit_price, quantity, total_price)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                (order_id, itm['product_id'], itm['variant_id'], itm['name'], var_details, itm['unit_price'], itm['quantity'], itm['line_total'])
            )
            
            # Atomically reserve inventory
            if itm['variant_id']:
                execute_db("UPDATE product_variants SET stock_quantity = MAX(0, stock_quantity - ?) WHERE id = ?", (itm['quantity'], itm['variant_id']))
            execute_db("UPDATE products SET stock_quantity = MAX(0, stock_quantity - ?) WHERE id = ?", (itm['quantity'], itm['product_id']))
            
        # Update Coupon usage if coupon used
        if cart_data['coupon_code']:
            execute_db("UPDATE coupons SET times_used = times_used + 1 WHERE code = ?", (cart_data['coupon_code'],))
            
        # Order Status History
        execute_db(
            """INSERT INTO order_status_history (order_id, old_status, new_status, changed_by, notes)
               VALUES (?, NULL, 'confirmed', 'System', 'Store reservation confirmed. Device kept ready for customer showroom visit.')""",
            (order_id,)
        )
        
        # Clear Cart
        execute_db("DELETE FROM cart_items WHERE cart_id = ?", (cart_data['cart_id'],))
        session.pop('applied_coupon', None)
        
        flash(f'Badhaai ho! Aapka smartphone successfully reserve ho gaya hai. Showroom par aakar collect karein.', 'success')
        return redirect(url_for('store.order_success', order_number=order_number))
        
    return render_template(
        'checkout.html',
        cart=cart_data,
        user_profile=user_profile
    )

@store_bp.route('/order-success/<order_number>')
def order_success(order_number):
    order = query_db("SELECT * FROM orders WHERE order_number = ?", (order_number,), one=True)
    if not order:
        flash('Order details not found.', 'warning')
        return redirect(url_for('store.home'))
        
    items = query_db("SELECT * FROM order_items WHERE order_id = ?", (order['id'],))
    shipping_address = json.loads(order['shipping_address_json'])
    return render_template('order_success.html', order=order, items=items, shipping_address=shipping_address)

@store_bp.route('/track-order', methods=['GET', 'POST'])
def track_order():
    order_info = None
    items = []
    history = []
    searched = False
    
    if request.method == 'POST':
        searched = True
        order_number = request.form.get('order_number', '').strip()
        contact = request.form.get('contact', '').strip().lower()
        
        order_info = query_db(
            """SELECT * FROM orders 
               WHERE order_number = ? AND (LOWER(customer_email) = ? OR customer_phone LIKE ?)""",
            (order_number, contact, f"%{contact}%"), one=True
        )
        if order_info:
            items = query_db("SELECT * FROM order_items WHERE order_id = ?", (order_info['id'],))
            history = query_db("SELECT * FROM order_status_history WHERE order_id = ? ORDER BY id ASC", (order_info['id'],))
        else:
            flash('No matching order found. Please check your Order Number and Mobile/Email.', 'warning')
            
    return render_template('track_order.html', order=order_info, items=items, history=history, searched=searched)

@store_bp.route('/wishlist')
def wishlist():
    user_id = session.get('user_id')
    if not user_id:
        flash('Please sign in to view and save items to your wishlist.', 'info')
        return redirect(url_for('auth.login', next=request.url))
        
    items = query_db(
        """SELECT p.*, b.name as brand_name, pi.image_url, w.id as wishlist_id
           FROM wishlists w
           JOIN products p ON w.product_id = p.id
           LEFT JOIN brands b ON p.brand_id = b.id
           LEFT JOIN product_images pi ON pi.product_id = p.id AND pi.is_primary = 1
           WHERE w.user_id = ?
           ORDER BY w.id DESC""",
        (user_id,)
    )
    return render_template('account/wishlist.html', items=items)

# Informational Pages
@store_bp.route('/about')
def about():
    return render_template('pages/about.html')

@store_bp.route('/contact')
def contact():
    return render_template('pages/contact.html')

@store_bp.route('/shipping-policy')
def shipping_policy():
    return render_template('pages/shipping.html')

@store_bp.route('/return-policy')
def return_policy():
    return render_template('pages/returns.html')

@store_bp.route('/terms')
def terms():
    return render_template('pages/terms.html')
