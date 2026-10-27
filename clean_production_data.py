"""
HIGH TECH MOBILE - Production Cleanup Utility
Removes all dummy orders, test sales data, and dummy test customer logins
while preserving the product catalog, categories, brands, settings, and administrator accounts.
"""
import sqlite3
from config import Config

def clean_database():
    conn = sqlite3.connect(Config.DATABASE_PATH)
    cur = conn.cursor()
    
    print("[*] Cleaning up dummy test sales and orders...")
    cur.execute("DELETE FROM order_items")
    cur.execute("DELETE FROM order_status_history")
    cur.execute("DELETE FROM orders")
    
    print("[*] Resetting coupon usage statistics...")
    cur.execute("UPDATE coupons SET times_used = 0")
    
    print("[*] Cleaning up carts and guest checkout sessions...")
    cur.execute("DELETE FROM cart_items")
    cur.execute("DELETE FROM carts")
    
    print("[*] Removing dummy test customers (preserving admin accounts)...")
    cur.execute("DELETE FROM user_addresses WHERE user_id IN (SELECT id FROM users WHERE role != 'admin')")
    cur.execute("DELETE FROM users WHERE role != 'admin'")
    
    print("[*] Cleaning test order audit logs...")
    cur.execute("DELETE FROM audit_logs WHERE action IN ('CREATE_ORDER', 'UPDATE_ORDER_STATUS')")
    
    # Reset product inventory to standard showroom quantities
    cur.execute("UPDATE products SET stock_quantity = 25 WHERE stock_quantity < 25")
    cur.execute("UPDATE product_variants SET stock_quantity = 10 WHERE stock_quantity < 10")
    
    conn.commit()
    
    # Verification
    cur.execute("SELECT COUNT(*) FROM orders")
    order_count = cur.fetchone()[0]
    cur.execute("SELECT id, name, email, role FROM users")
    admins = cur.fetchall()
    cur.execute("SELECT COUNT(*) FROM products")
    product_count = cur.fetchone()[0]
    
    conn.close()
    
    print(f"\n[SUCCESS] Production Database Ready!")
    print(f" - Orders Count: {order_count} (Clean slate for real showroom reservations)")
    print(f" - Active Products: {product_count} (Catalog preserved)")
    print(f" - Active Admin Accounts:")
    for a in admins:
        print(f"    • ID #{a[0]}: {a[1]} ({a[2]}) - Role: {a[3]}")

if __name__ == '__main__':
    clean_database()
