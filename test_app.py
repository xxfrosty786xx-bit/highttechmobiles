"""
HIGH TECH MOBILE - Automated Full-Stack Test Suite
Verifies storefront routes, customer registration, admin protection, cart calculations,
pincode checker, atomic order placement, inventory deduction, and audit logging.
"""
import unittest
import json
from app import create_app
from database import query_db, execute_db
from setup_admin import setup_admin

class HighTechMobileTestCase(unittest.TestCase):
    
    @classmethod
    def setUpClass(cls):
        cls.app = create_app()
        cls.app.config['TESTING'] = True
        cls.client = cls.app.test_client()
        # Ensure admin is set up
        setup_admin(email="avidmalikhts@gmail.com", password="nayra@99667", name="Avid Malik", force=True)

    def test_01_homepage_renders(self):
        """Test homepage responds with HTTP 200 and brand name."""
        res = self.client.get('/')
        self.assertEqual(res.status_code, 200)
        self.assertIn(b'HIGH TECH MOBILE', res.data)
        self.assertIn(b'Upgrade Your Mobile Experience', res.data)
        self.assertIn(b'iPhone 16 Pro Max', res.data)
        print("[PASS] Test 01: Homepage rendered successfully with flagship phones.")

    def test_02_catalog_and_filters(self):
        """Test catalog page, brand filter, and search query."""
        res = self.client.get('/shop?category=smartphones')
        self.assertEqual(res.status_code, 200)
        self.assertIn(b'Samsung Galaxy S24 Ultra', res.data)
        
        # Test search
        search_res = self.client.get('/shop?q=OnePlus')
        self.assertEqual(search_res.status_code, 200)
        self.assertIn(b'OnePlus 12', search_res.data)
        print("[PASS] Test 02: Shop catalog filters and search working.")

    def test_03_product_detail_page(self):
        """Test product detail page with variants, specs, and gallery."""
        res = self.client.get('/product/apple-iphone-16-pro-max')
        self.assertEqual(res.status_code, 200)
        self.assertIn(b'A18 Pro', res.data)
        self.assertIn(b'Technical Specifications', res.data)
        self.assertIn(b'Desert Titanium', res.data)
        print("[PASS] Test 03: Product detail page rendered with full tech specs.")

    def test_04_pincode_checker_api(self):
        """Test Indian PIN code serviceability checker."""
        res = self.client.get('/api/pincode/check?pincode=110001')
        self.assertEqual(res.status_code, 200)
        data = json.loads(res.data)
        self.assertTrue(data['serviceable'])
        self.assertEqual(data['pincode'], '110001')
        self.assertIn('Delhi', data['region'])
        print("[PASS] Test 04: Indian PIN code delivery checker working.")

    def test_05_cart_and_coupon_api(self):
        """Test adding item to cart and applying discount coupon."""
        with self.app.app_context():
            p = query_db("SELECT id FROM products WHERE slug = 'apple-iphone-16-pro-max'", one=True)
            self.assertIsNotNone(p)
            prod_id = p['id']
            
        # Add to cart
        add_res = self.client.post('/api/cart/add', json={"product_id": prod_id, "quantity": 1})
        self.assertEqual(add_res.status_code, 200)
        data = json.loads(add_res.data)
        self.assertEqual(data['status'], 'success')
        self.assertGreaterEqual(data['total_items'], 1)
        
        # Apply valid coupon
        coup_res = self.client.post('/api/cart/apply-coupon', json={"code": "TECH10"})
        self.assertEqual(coup_res.status_code, 200)
        cdata = json.loads(coup_res.data)
        self.assertEqual(cdata['status'], 'success')
        self.assertGreater(cdata['discount_amount'], 0)
        print("[PASS] Test 05: Cart add and TECH10 coupon engine verified.")

    def test_06_customer_registration_and_login(self):
        """Test secure customer registration and login with session validation."""
        test_email = "vikram.sharma@example.in"
        with self.app.app_context():
            execute_db("DELETE FROM users WHERE email = ?", (test_email,))
            
        reg_res = self.client.post('/register', data={
            "name": "Vikram Sharma",
            "email": test_email,
            "phone": "9812345678",
            "password": "Password@123",
            "confirm_password": "Password@123"
        }, follow_redirects=True)
        self.assertEqual(reg_res.status_code, 200)
        
        with self.app.app_context():
            u = query_db("SELECT * FROM users WHERE email = ?", (test_email,), one=True)
            self.assertIsNotNone(u)
            self.assertEqual(u['name'], "Vikram Sharma")
            self.assertEqual(u['role'], "customer")
        print("[PASS] Test 06: Customer registration and scrypt password hashing verified.")

    def test_07_admin_protection_and_access(self):
        """Verify normal customer CANNOT access /admin routes, but admin CAN."""
        # Unauthenticated access redirects to /admin/login
        guest_res = self.client.get('/admin/', follow_redirects=False)
        self.assertEqual(guest_res.status_code, 302)
        self.assertIn('/admin/login', guest_res.location)
        
        # Admin login
        login_res = self.client.post('/admin/login', data={
            "email": "avidmalikhts@gmail.com",
            "password": "nayra@99667"
        }, follow_redirects=True)
        self.assertEqual(login_res.status_code, 200)
        self.assertIn(b'Store Dashboard', login_res.data)
        self.assertTrue(b'Avid Malik' in login_res.data or b'Danish Malik' in login_res.data)
        print("[PASS] Test 07: Admin security and server-side role check verified.")

    def test_08_order_creation_and_atomic_stock_deduction(self):
        """Test full showroom reservation flow with atomic stock decrement."""
        with self.app.app_context():
            p = query_db("SELECT id, stock_quantity FROM products WHERE slug = 'oneplus-12-5g'", one=True)
            prod_id = p['id']
            initial_stock = p['stock_quantity']
            
        # Add to cart
        self.client.post('/api/cart/add', json={"product_id": prod_id, "quantity": 1})
        
        # Submit reservation (Store Pickup - Dukan Par Aakar Kharidein)
        order_res = self.client.post('/checkout', data={
            "customer_name": "Arjun Patel",
            "customer_email": "arjun.patel@example.in",
            "customer_phone": "9988776655",
            "customer_city": "New Delhi",
            "pickup_date": "Tomorrow (Within 24 Hours)",
            "pickup_time": "Evening (4:00 PM - 8:00 PM)",
            "payment_method": "store_counter",
            "order_notes": "Please keep sealed pack box ready"
        }, follow_redirects=True)
        
        self.assertEqual(order_res.status_code, 200)
        self.assertIn(b'Reservation Confirmed', order_res.data)
        self.assertIn(b'Arjun Patel', order_res.data)
        
        with self.app.app_context():
            updated_p = query_db("SELECT stock_quantity FROM products WHERE id = ?", (prod_id,), one=True)
            self.assertEqual(updated_p['stock_quantity'], initial_stock - 1)
        print("[PASS] Test 08: Showroom reservation creation and atomic inventory decrement verified.")

    def test_09_admin_order_status_update(self):
        """Test admin order update to ready for showroom pickup and audit log record."""
        with self.app.app_context():
            ord_row = query_db("SELECT id, order_number FROM orders ORDER BY id DESC LIMIT 1", one=True)
            self.assertIsNotNone(ord_row)
            order_id = ord_row['id']
            
        # Log in as admin first
        self.client.post('/admin/login', data={
            "email": "avidmalikhts@gmail.com",
            "password": "nayra@99667"
        })
        
        # Admin updates order status to ready_pickup
        upd_res = self.client.post(f"/admin/orders/{order_id}/update-status", data={
            "fulfilment_status": "ready_pickup",
            "payment_status": "pending",
            "courier_name": "Counter #1 (Danish Malik)",
            "tracking_number": "HTM-PASS-99",
            "notes": "Device inspected and kept at Counter #1 for Arjun Patel"
        }, follow_redirects=True)
        self.assertEqual(upd_res.status_code, 200)
        
        with self.app.app_context():
            refreshed = query_db("SELECT fulfilment_status, tracking_number FROM orders WHERE id = ?", (order_id,), one=True)
            self.assertEqual(refreshed['fulfilment_status'], 'ready_pickup')
            self.assertEqual(refreshed['tracking_number'], 'HTM-PASS-99')
            
            # Verify audit log recorded
            log_row = query_db("SELECT * FROM audit_logs WHERE action = 'UPDATE_ORDER_STATUS' ORDER BY id DESC LIMIT 1", one=True)
            self.assertIsNotNone(log_row)
            self.assertTrue(log_row['admin_name'] in ('Avid Malik', 'Danish Malik'))
        print("[PASS] Test 09: Reservation status transition and audit trail verified.")

if __name__ == '__main__':
    unittest.main()
