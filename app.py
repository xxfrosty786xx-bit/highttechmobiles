import os
from flask import Flask, render_template, session, g, send_file
from config import Config
from database import close_db, get_setting, format_inr, query_db

def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)
    
    # Teardown
    app.teardown_appcontext(close_db)
    
    # Register blueprints
    from routes.store import store_bp
    from routes.auth import auth_bp
    from routes.admin import admin_bp
    from routes.api import api_bp
    
    app.register_blueprint(store_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(api_bp)
    
    # Jinja filters
    @app.template_filter('inr')
    def inr_filter(value):
        return format_inr(value)
        
    @app.template_filter('discount_pct')
    def discount_pct_filter(product):
        if product.get('original_price') and product['original_price'] > product['price']:
            return int(round(((product['original_price'] - product['price']) / product['original_price']) * 100))
        return 0

    # Global Context Processor
    @app.context_processor
    def inject_global_settings():
        cart_count = 0
        try:
            cart_sess = session.get('cart_session_id')
            user_id = session.get('user_id')
            if cart_sess or user_id:
                row = query_db(
                    """SELECT COALESCE(SUM(ci.quantity), 0) as total_qty
                       FROM cart_items ci
                       JOIN carts c ON ci.cart_id = c.id
                       WHERE c.session_id = ? OR (c.user_id IS NOT NULL AND c.user_id = ?)""",
                    (cart_sess, user_id), one=True
                )
                if row:
                    cart_count = row['total_qty']
        except Exception:
            cart_count = 0
            
        wishlist_count = 0
        try:
            if 'user_id' in session:
                w_row = query_db("SELECT count(*) as c FROM wishlists WHERE user_id = ?", (session['user_id'],), one=True)
                if w_row:
                    wishlist_count = w_row['c']
        except Exception:
            wishlist_count = 0

        return {
            'store_name': get_setting('store_name', 'HIGH TECH MOBILE'),
            'store_tagline': get_setting('store_tagline', 'Upgrade Your Mobile Experience'),
            'contact_email': get_setting('contact_email', 'support@hightechmobile.in'),
            'contact_phone': get_setting('contact_phone', '+91 98765 43210'),
            'store_address': get_setting('store_address', 'Ruheri, Hathras, Uttar Pradesh - 204101, India'),
            'store_map_url': get_setting('store_map_url', 'https://www.google.com/maps?q=27.643748,78.063498'),
            'store_live_location': get_setting('store_live_location', 'https://www.where-am-i.co/@27.643748,78.063498,z14'),
            'store_coordinates': get_setting('store_coordinates', '27.643748, 78.063498'),
            'store_city': get_setting('store_city', 'Ruheri, Hathras'),
            'store_state': get_setting('store_state', 'Uttar Pradesh'),
            'announcement_text': get_setting('announcement_text', '📍 Showroom Pickup Only: Reserve Online & Collect at HIGH TECH MOBILE (Ruheri, Hathras, Uttar Pradesh) • 100% Sealed Box & Spot Verification!'),
            'announcement_active': get_setting('announcement_active', '1') == '1',
            'hero_badge': get_setting('hero_badge', 'LATEST SMARTPHONES & ACCESSORIES'),
            'hero_title': get_setting('hero_title', 'Upgrade Your Mobile Experience'),
            'hero_subtitle': get_setting('hero_subtitle', 'Top brands. Best prices. Unmatched quality. Your next smartphone is just a click away.'),
            'hero_primary_btn_text': get_setting('hero_primary_btn_text', 'Shop Smartphones'),
            'hero_primary_btn_url': get_setting('hero_primary_btn_url', '/shop?category=smartphones'),
            'hero_secondary_btn_text': get_setting('hero_secondary_btn_text', 'Explore Latest Deals'),
            'hero_secondary_btn_url': get_setting('hero_secondary_btn_url', '/shop?deals=true'),
            'cart_count': cart_count,
            'wishlist_count': wishlist_count,
            'current_user': {
                'id': session.get('user_id'),
                'name': session.get('user_name'),
                'email': session.get('user_email'),
                'role': session.get('user_role')
            } if 'user_id' in session else None
        }
        
    @app.route('/download-package')
    def download_package():
        zip_path = os.path.join(os.path.dirname(__file__), 'high_tech_mobile_production.zip')
        if not os.path.exists(zip_path):
            from make_production_zip import create_zip
            create_zip()
        return send_file(zip_path, as_attachment=True, download_name='high_tech_mobile_production.zip', mimetype='application/zip')

    @app.errorhandler(404)
    def page_not_found(e):
        return render_template('pages/404.html'), 404

    @app.errorhandler(500)
    def server_error(e):
        return render_template('pages/500.html'), 500

    return app

app = create_app()

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    print(f"[*] HIGH TECH MOBILE running on http://127.0.0.1:{port}")
    app.run(host='0.0.0.0', port=port, debug=False)
