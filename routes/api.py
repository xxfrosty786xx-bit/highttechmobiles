import re
import json
from datetime import datetime, timedelta
from flask import Blueprint, request, jsonify, session
from database import query_db, execute_db, get_setting, format_inr
from routes.store import get_session_cart_id, get_cart_data

api_bp = Blueprint('api', __name__, url_prefix='/api')

@api_bp.route('/cart/count', methods=['GET'])
def cart_count():
    cart_data = get_cart_data()
    return jsonify({
        "status": "success",
        "total_items": cart_data['total_items'],
        "subtotal": cart_data['subtotal'],
        "subtotal_formatted": format_inr(cart_data['subtotal'])
    })

@api_bp.route('/cart/add', methods=['POST'])
def cart_add():
    data = request.get_json() or request.form
    product_id = data.get('product_id')
    variant_id = data.get('variant_id') or None
    try:
        quantity = int(data.get('quantity', 1))
        if quantity <= 0:
            quantity = 1
    except (ValueError, TypeError):
        quantity = 1
        
    if not product_id:
        return jsonify({"status": "error", "message": "Product ID is required."}), 400
        
    # Verify product exists and published
    product = query_db("SELECT * FROM products WHERE id = ? AND is_published = 1", (product_id,), one=True)
    if not product:
        return jsonify({"status": "error", "message": "Product not found or unavailable."}), 404
        
    # Check variant if provided
    available_stock = product['stock_quantity']
    if variant_id:
        variant = query_db("SELECT * FROM product_variants WHERE id = ? AND product_id = ?", (variant_id, product_id), one=True)
        if not variant:
            return jsonify({"status": "error", "message": "Specified variant not found."}), 404
        available_stock = variant['stock_quantity']
        
    if available_stock <= 0:
        return jsonify({"status": "error", "message": "Sorry, this product variant is currently out of stock."}), 400
        
    # Get or create cart
    cart_data = get_cart_data()
    cart_id = cart_data['cart_id']
    
    # Check if item already in cart
    existing_item = query_db(
        "SELECT id, quantity FROM cart_items WHERE cart_id = ? AND product_id = ? AND (variant_id = ? OR (variant_id IS NULL AND ? IS NULL))",
        (cart_id, product_id, variant_id, variant_id), one=True
    )
    
    if existing_item:
        new_qty = existing_item['quantity'] + quantity
        if new_qty > available_stock:
            new_qty = available_stock
            msg = f"Quantity adjusted to available stock limit ({available_stock} units)."
        else:
            msg = f"Added {quantity} more to your cart."
        execute_db("UPDATE cart_items SET quantity = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?", (new_qty, existing_item['id']))
    else:
        if quantity > available_stock:
            quantity = available_stock
        execute_db(
            "INSERT INTO cart_items (cart_id, product_id, variant_id, quantity) VALUES (?, ?, ?, ?)",
            (cart_id, product_id, variant_id, quantity)
        )
        msg = f"'{product['name']}' added to your shopping cart."
        
    # Return fresh cart data
    updated_cart = get_cart_data()
    return jsonify({
        "status": "success",
        "message": msg,
        "total_items": updated_cart['total_items'],
        "subtotal": updated_cart['subtotal'],
        "subtotal_formatted": format_inr(updated_cart['subtotal'])
    })

@api_bp.route('/cart/update', methods=['POST'])
def cart_update():
    data = request.get_json() or request.form
    item_id = data.get('item_id')
    try:
        quantity = int(data.get('quantity', 1))
    except (ValueError, TypeError):
        quantity = 1
        
    cart_data = get_cart_data()
    cart_id = cart_data['cart_id']
    
    item = query_db(
        """SELECT ci.*, p.stock_quantity as p_stock, pv.stock_quantity as v_stock, p.name
           FROM cart_items ci
           JOIN products p ON ci.product_id = p.id
           LEFT JOIN product_variants pv ON ci.variant_id = pv.id
           WHERE ci.id = ? AND ci.cart_id = ?""",
        (item_id, cart_id), one=True
    )
    
    if not item:
        return jsonify({"status": "error", "message": "Cart item not found."}), 404
        
    if quantity <= 0:
        execute_db("DELETE FROM cart_items WHERE id = ?", (item_id,))
        msg = f"Removed item from cart."
    else:
        max_stock = item['v_stock'] if item['variant_id'] else item['p_stock']
        if quantity > max_stock:
            quantity = max_stock
            msg = f"Maximum available quantity is {max_stock}."
        else:
            msg = "Cart updated."
        execute_db("UPDATE cart_items SET quantity = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?", (quantity, item_id))
        
    updated = get_cart_data()
    return jsonify({
        "status": "success",
        "message": msg,
        "total_items": updated['total_items'],
        "subtotal": updated['subtotal'],
        "subtotal_formatted": format_inr(updated['subtotal']),
        "discount_amount": updated['discount_amount'],
        "discount_formatted": format_inr(updated['discount_amount']),
        "shipping_fee": updated['shipping_fee'],
        "shipping_formatted": format_inr(updated['shipping_fee']),
        "total_amount": updated['total_amount'],
        "total_formatted": format_inr(updated['total_amount'])
    })

@api_bp.route('/cart/remove', methods=['POST'])
def cart_remove():
    data = request.get_json() or request.form
    item_id = data.get('item_id')
    cart_data = get_cart_data()
    
    execute_db("DELETE FROM cart_items WHERE id = ? AND cart_id = ?", (item_id, cart_data['cart_id']))
    updated = get_cart_data()
    
    return jsonify({
        "status": "success",
        "message": "Item removed from cart.",
        "total_items": updated['total_items'],
        "subtotal": updated['subtotal'],
        "subtotal_formatted": format_inr(updated['subtotal']),
        "total_amount": updated['total_amount'],
        "total_formatted": format_inr(updated['total_amount'])
    })

@api_bp.route('/cart/apply-coupon', methods=['POST'])
def apply_coupon():
    data = request.get_json() or request.form
    code = (data.get('code') or '').strip().upper()
    
    if not code:
        return jsonify({"status": "error", "message": "Please enter a coupon code."}), 400
        
    cart_data = get_cart_data()
    if cart_data['subtotal'] <= 0:
        return jsonify({"status": "error", "message": "Your cart is empty."}), 400
        
    coupon = query_db("SELECT * FROM coupons WHERE code = ? AND is_active = 1", (code,), one=True)
    if not coupon:
        return jsonify({"status": "error", "message": "Invalid or expired coupon code."}), 404
        
    if coupon['expires_at']:
        try:
            exp_time = datetime.strptime(coupon['expires_at'], '%Y-%m-%d %H:%M:%S')
            if datetime.now() > exp_time:
                return jsonify({"status": "error", "message": "This coupon code has expired."}), 400
        except Exception:
            pass
            
    if coupon['usage_limit'] and coupon['times_used'] >= coupon['usage_limit']:
        return jsonify({"status": "error", "message": "This coupon usage limit has been reached."}), 400
        
    if cart_data['subtotal'] < coupon['min_order_amount']:
        return jsonify({
            "status": "error",
            "message": f"Coupon requires a minimum order value of {format_inr(coupon['min_order_amount'])}."
        }), 400
        
    # Valid coupon
    session['applied_coupon'] = code
    updated = get_cart_data()
    
    return jsonify({
        "status": "success",
        "message": f"Coupon '{code}' applied successfully!",
        "discount_amount": updated['discount_amount'],
        "discount_formatted": format_inr(updated['discount_amount']),
        "total_amount": updated['total_amount'],
        "total_formatted": format_inr(updated['total_amount'])
    })

@api_bp.route('/cart/remove-coupon', methods=['POST'])
def remove_coupon():
    session.pop('applied_coupon', None)
    updated = get_cart_data()
    return jsonify({
        "status": "success",
        "message": "Coupon removed.",
        "total_amount": updated['total_amount'],
        "total_formatted": format_inr(updated['total_amount'])
    })

@api_bp.route('/pincode/check', methods=['POST', 'GET'])
def check_pincode():
    pincode = request.args.get('pincode') or (request.get_json() or {}).get('pincode') or request.form.get('pincode')
    if not pincode or not re.match(r'^\d{6}$', str(pincode).strip()):
        return jsonify({"status": "error", "message": "Please enter a valid 6-digit Indian PIN code."}), 400
        
    code_int = int(pincode)
    prefix = int(str(pincode)[0])
    
    # Accurate Indian Postal circle mapping
    zone_map = {
        1: ("Delhi, Haryana, Punjab, Himachal Pradesh, J&K, Chandigarh", 2),
        2: ("Uttar Pradesh, Uttarakhand", 2),
        3: ("Rajasthan, Gujarat, Daman & Diu, Dadra & Nagar Haveli", 3),
        4: ("Maharashtra, Goa, Madhya Pradesh, Chhattisgarh", 3),
        5: ("Andhra Pradesh, Telangana, Karnataka", 3),
        6: ("Tamil Nadu, Kerala, Lakshadweep, Puducherry", 4),
        7: ("West Bengal, Odisha, North Eastern States, Andaman & Nicobar", 4),
        8: ("Bihar, Jharkhand", 3),
        9: ("Army Post Office", 5)
    }
    
    region_info, days = zone_map.get(prefix, ("Pan-India Fast Delivery", 3))
    est_date = (datetime.now() + timedelta(days=days)).strftime("%A, %d %B")
    
    return jsonify({
        "status": "success",
        "serviceable": True,
        "pincode": pincode,
        "region": region_info,
        "estimated_days": f"{days} Business Days",
        "estimated_delivery": est_date,
        "cod_available": True,
        "courier": "BlueDart Express / Delhivery Express"
    })

@api_bp.route('/wishlist/toggle', methods=['POST'])
def wishlist_toggle():
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({"status": "auth_required", "message": "Please log in to add items to your wishlist."}), 401
        
    data = request.get_json() or request.form
    product_id = data.get('product_id')
    if not product_id:
        return jsonify({"status": "error", "message": "Product ID required."}), 400
        
    existing = query_db("SELECT id FROM wishlists WHERE user_id = ? AND product_id = ?", (user_id, product_id), one=True)
    if existing:
        execute_db("DELETE FROM wishlists WHERE id = ?", (existing['id'],))
        in_wishlist = False
        msg = "Product removed from wishlist."
    else:
        execute_db("INSERT INTO wishlists (user_id, product_id) VALUES (?, ?)", (user_id, product_id))
        in_wishlist = True
        msg = "Product saved to your wishlist."
        
    count = query_db("SELECT count(*) as c FROM wishlists WHERE user_id = ?", (user_id,), one=True)['c']
    return jsonify({
        "status": "success",
        "in_wishlist": in_wishlist,
        "message": msg,
        "wishlist_count": count
    })

@api_bp.route('/search/suggestions', methods=['GET'])
def search_suggestions():
    q = request.args.get('q', '').strip()
    if len(q) < 2:
        return jsonify([])
        
    term = f"%{q}%"
    rows = query_db(
        """SELECT p.id, p.name, p.slug, p.price, pi.image_url, b.name as brand_name
           FROM products p
           LEFT JOIN brands b ON p.brand_id = b.id
           LEFT JOIN product_images pi ON pi.product_id = p.id AND pi.is_primary = 1
           WHERE p.is_published = 1 AND (p.name LIKE ? OR b.name LIKE ? OR p.short_description LIKE ?)
           ORDER BY p.is_featured DESC, p.id DESC
           LIMIT 5""",
        (term, term, term)
    )
    
    results = []
    for r in rows:
        results.append({
            "name": r['name'],
            "slug": r['slug'],
            "brand": r['brand_name'],
            "price": format_inr(r['price']),
            "image": r['image_url'] or '/static/images/placeholder.svg'
        })
    return jsonify(results)
