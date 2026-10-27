import sqlite3
import json
import os
from flask import g, request, current_app
from config import Config

def get_db():
    """Returns a database connection scoped to the current Flask application context."""
    if 'db' not in g:
        db_path = current_app.config.get('DATABASE_PATH', Config.DATABASE_PATH)
        g.db = sqlite3.connect(db_path, detect_types=sqlite3.PARSE_DECLTYPES)
        g.db.row_factory = sqlite3.Row
        g.db.execute("PRAGMA foreign_keys = ON;")
    return g.db

def close_db(e=None):
    """Closes the active database connection if open."""
    db = g.pop('db', None)
    if db is not None:
        db.close()

def init_db(app=None):
    """Initializes the database using schema.sql."""
    db_path = Config.DATABASE_PATH if app is None else app.config.get('DATABASE_PATH', Config.DATABASE_PATH)
    schema_path = os.path.join(os.path.dirname(__file__), 'schema.sql')
    
    conn = sqlite3.connect(db_path)
    with open(schema_path, 'r', encoding='utf-8') as f:
        conn.executescript(f.read())
    conn.commit()
    conn.close()

def query_db(query, args=(), one=False):
    """Execute a SELECT query and return results as list of dicts (or single dict if one=True)."""
    cur = get_db().execute(query, args)
    rv = cur.fetchall()
    cur.close()
    if rv:
        if one:
            return dict(rv[0])
        return [dict(r) for r in rv]
    return None if one else []

def execute_db(query, args=(), commit=True):
    """Execute an INSERT/UPDATE/DELETE query and return the lastrowid and rowcount."""
    db = get_db()
    cur = db.execute(query, args)
    if commit:
        db.commit()
    last_id = cur.lastrowid
    row_count = cur.rowcount
    cur.close()
    return last_id, row_count

def log_audit(admin_user_id, admin_name, action, entity_type, entity_id=None, details=None, ip=None):
    """Safely log administrator actions for compliance and traceability."""
    try:
        ip_addr = ip or (request.remote_addr if request else '127.0.0.1')
        details_str = json.dumps(details) if details else None
        execute_db(
            """INSERT INTO audit_logs (admin_user_id, admin_name, action, entity_type, entity_id, details_json, ip_address)
               VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (admin_user_id, admin_name, action, entity_type, str(entity_id) if entity_id else None, details_str, ip_addr)
        )
    except Exception as e:
        print(f"[Audit Log Warning] Failed to write audit log: {e}")

def get_setting(key, default=None):
    """Fetch setting value from store_settings."""
    try:
        row = query_db("SELECT setting_value FROM store_settings WHERE setting_key = ?", (key,), one=True)
        if row and row['setting_value'] is not None:
            return row['setting_value']
    except Exception:
        pass
    return default

def set_setting(key, value, description=None):
    """Update or insert setting value into store_settings."""
    execute_db(
        """INSERT INTO store_settings (setting_key, setting_value, description, updated_at)
           VALUES (?, ?, ?, CURRENT_TIMESTAMP)
           ON CONFLICT(setting_key) DO UPDATE SET
               setting_value = excluded.setting_value,
               description = COALESCE(excluded.description, store_settings.description),
               updated_at = CURRENT_TIMESTAMP""",
        (key, str(value), description)
    )

def format_inr(amount):
    """Format numbers into Indian Rupee style, e.g. 144900 -> ₹1,44,900."""
    try:
        amt = float(amount)
        if amt < 0:
            return f"-₹{format_inr(abs(amt))}"
        
        # Split integer and decimal parts
        parts = f"{amt:.2f}".split('.')
        int_part = parts[0]
        dec_part = parts[1]
        
        if len(int_part) <= 3:
            formatted_int = int_part
        else:
            last_three = int_part[-3:]
            remaining = int_part[:-3]
            # Group by 2 digits from right
            groups = []
            while len(remaining) > 2:
                groups.insert(0, remaining[-2:])
                remaining = remaining[:-2]
            if remaining:
                groups.insert(0, remaining)
            formatted_int = ','.join(groups) + ',' + last_three
            
        if dec_part == '00':
            return f"₹{formatted_int}"
        return f"₹{formatted_int}.{dec_part}"
    except (ValueError, TypeError):
        return f"₹{amount}"
