"""
HIGH TECH MOBILE - Secure Administrator Setup Utility
Initializes or resets the primary store administrator.
"""
import os
import sys
import re
import argparse
import sqlite3
from werkzeug.security import generate_password_hash
from config import Config

def is_valid_email(email: str) -> bool:
    pattern = r'^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$'
    return bool(re.match(pattern, email.strip()))

def setup_admin(email=None, password=None, name=None, force=False):
    db_path = Config.DATABASE_PATH
    
    # 1. Determine admin credentials from parameters or environment
    admin_name = name or os.environ.get('ADMIN_NAME', Config.ADMIN_NAME)
    admin_email = (email or os.environ.get('ADMIN_EMAIL', Config.ADMIN_EMAIL)).strip().lower()
    admin_password = password or os.environ.get('ADMIN_PASSWORD', Config.ADMIN_DEFAULT_PASSWORD)
    
    # 2. Validate email syntax
    if not is_valid_email(admin_email):
        print(f"[ERROR] The provided admin identifier '{admin_email}' is not a valid email address format.")
        sys.exit(1)
        
    if len(admin_password) < 8:
        print("[ERROR] Administrator password must be at least 8 characters long.")
        sys.exit(1)
        
    print(f"[*] Initializing Administrator:")
    print(f"    - Display Name: {admin_name}")
    print(f"    - Email:        {admin_email}")
    print(f"    - Security:     Werkzeug PBKDF2:SHA256 salted hash")
    
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    
    # Ensure tables exist
    schema_path = os.path.join(os.path.dirname(__file__), 'schema.sql')
    if os.path.exists(schema_path):
        with open(schema_path, 'r', encoding='utf-8') as f:
            cur.executescript(f.read())
            
    # Check if admin already exists
    cur.execute("SELECT id, name, email, role FROM users WHERE email = ?", (admin_email,))
    existing_user = cur.fetchone()
    
    hashed_pwd = generate_password_hash(admin_password, method='scrypt')
    
    if existing_user:
        if existing_user['role'] == 'admin' and not force:
            print(f"[!] Admin user already exists with ID #{existing_user['id']}. Updating credentials.")
        cur.execute(
            """UPDATE users 
               SET name = ?, password_hash = ?, role = 'admin', is_active = 1, updated_at = CURRENT_TIMESTAMP 
               WHERE id = ?""",
            (admin_name, hashed_pwd, existing_user['id'])
        )
        admin_id = existing_user['id']
        print(f"[SUCCESS] Administrator #{admin_id} credentials updated successfully.")
    else:
        cur.execute(
            """INSERT INTO users (name, email, password_hash, role, is_active)
               VALUES (?, ?, ?, 'admin', 1)""",
            (admin_name, admin_email, hashed_pwd)
        )
        admin_id = cur.lastrowid
        print(f"[SUCCESS] New Administrator #{admin_id} created successfully.")
        
    # Log to audit table
    cur.execute(
        """INSERT INTO audit_logs (admin_user_id, admin_name, action, entity_type, entity_id, details_json, ip_address)
           VALUES (?, ?, 'ADMIN_SETUP', 'USER', ?, '{"note": "Admin created/updated via CLI"}', '127.0.0.1')""",
        (admin_id, admin_name, str(admin_id))
    )
    
    conn.commit()
    conn.close()
    return admin_id

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Initialize or update High Tech Mobile admin user.")
    parser.add_argument('--email', help="Admin email address")
    parser.add_argument('--password', help="Admin password")
    parser.add_argument('--name', help="Admin full display name")
    parser.add_argument('--force', action='store_true', help="Force update existing user")
    
    args = parser.parse_args()
    setup_admin(email=args.email, password=args.password, name=args.name, force=args.force)
