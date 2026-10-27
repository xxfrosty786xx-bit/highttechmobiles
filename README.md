# HIGH TECH MOBILE - Production E-Commerce Platform

> **Store Name:** HIGH TECH MOBILE  
> **Administrator:** Danish Malik  
> **Brand Style:** Luxury Tech Navy (`#06152B`), Electric Blue (`#1677FF`), Crisp White  
> **Target Market:** Indian Customers (INR ₹, 18% GST, Indian PIN Code validation, 36 States/UTs, Pan-India Courier Logistics)  
> **Timezone:** Asia/Kolkata  

HIGH TECH MOBILE is a production-grade smartphone and consumer electronics e-commerce web platform backed by a relational database, secure role-based authentication, real-time inventory decrement, Indian address and PIN code serviceability validation, coupon engine, dynamic cart, order management, and a dedicated, protected administrator dashboard.

---

## 🌟 Key Features

### Customer-Facing Storefront
1. **Design Parity:** Inspired by high-end technology retailers. Features deep navy futuristic surfaces, glowing pedestals, floating smartphone showcases, crisp typography, and responsive layouts across mobile, tablet, and desktop.
2. **Announcement Bar:** Top promotional bar for active discounts (e.g. `TECH10`) and free shipping threshold alerts, editable from the admin dashboard.
3. **Product Catalog & Filters:** Live instant search with auto-suggestions, category filters (Smartphones, Tablets, Laptops, Smartwatches, Audio, Accessories, Gaming), brand filters (Apple, Samsung, Google, OnePlus, Xiaomi, Sony, Anker, Spigen), price range filters, and sorting.
4. **Product Details Page:** Multi-image gallery with zoom preview, live variant selector (Color and Storage with dynamic price calculation), stock indicators, full technical specifications table, Indian PIN code delivery checker, genuine customer reviews, and related recommendations.
5. **Dynamic Cart & Checkout:** Real-time quantity adjustments, free shipping progress bar, promo code validation with server-side rate limits, GST breakdown, full Indian address validation (all 28 states + 8 UTs), Cash on Delivery (COD) and Razorpay online payment integration.
6. **Order Confirmation & Tracking:** Generated unique invoice references (e.g. `HTM-20261024-XXXX`), printable official tax invoices, and public order consignment tracking with live carrier updates (BlueDart, Delhivery).
7. **Customer Accounts:** Secure registration with Indian mobile number validation, password hashing via scrypt/PBKDF2, order history, address book, and persistent wishlist.

### Protected Administrator Dashboard (`/admin`)
1. **Administrator Identity:** Managed by **Danish Malik** (`DanishMalikhts@gmail.com`).
2. **Live KPI Analytics:** Real-time revenue (excluding cancelled orders), total orders, pending/processing orders awaiting shipment, completed orders, registered customer counts, published catalog items, and warehouse low-stock warnings (&le; 5 units).
3. **Interactive Sales Graph:** Dynamic visual revenue trajectory calculated from real order items.
4. **Product Management (CRUD):** Add, edit, delete/archive products with multi-image support, variants (color, storage, RAM, price deltas, stock), specs JSON builder, SEO tags, and badge controls.
5. **Category & Brand Management:** Reorder, enable/disable categories and manage brand partnerships.
6. **Order Fulfilment:** Filter orders by status (Confirmed, Processing, Shipped, Delivered, Cancelled), record logistics partner (BlueDart, Delhivery), update tracking AWB numbers, and add internal notes.
7. **Coupons & Deals:** Create percentage or fixed-amount discounts with expiration dates and minimum order constraints.
8. **Homepage & Banner Editor:** Update announcement bar text, visibility, and hero headlines without touching code.
9. **Store Settings:** Configure free shipping threshold, delivery charges, COD availability, and GST rates.
10. **Immutable Audit Logs:** Complete security trail of administrative actions with IP addresses and timestamps.

---

## 🛠️ Tech Stack & Architecture

- **Backend:** Python 3.14 / Flask 3.1.3 (Modular Blueprints: `store`, `auth`, `admin`, `api`)
- **Database:** SQLite 3 (Production schema with foreign keys, indexes, and transactions; compatible with PostgreSQL/Supabase)
- **Security:** Salted password hashing (`werkzeug.security`), role-based access decorators (`@admin_required`), session isolation, input sanitization
- **Frontend:** Responsive HTML5, Vanilla JavaScript, CSS3 with custom variables, SVG iconography, and Inter typography

---

## 🚀 Quick Start & Installation

### 1. Prerequisites
Ensure Python 3.10+ is installed on your system.

### 2. Initialize the Database & Seed Inventory
Run the database migration and seeding script:
```powershell
python seed.py
```
This populates:
- Store settings & policies
- Official categories & brands
- 12 authentic flagship smartphones and accessories with complete specifications, images, and variants
- Promo discount coupons (`TECH10`, `FLAT500`, `WELCOME5`)
- Sample order for testing

### 3. Initialize the Administrator (Danish Malik)
Set up the administrator account securely:
```powershell
python setup_admin.py --email "DanishMalikhts@gmail.com" --password "YourStrongPassword123" --name "Danish Malik"
```

### 4. Run the Web Server
Start the application:
```powershell
python app.py
```
Open your browser and navigate to:
- **Storefront:** [http://127.0.0.1:5000/](http://127.0.0.1:5000/)
- **Admin Portal:** [http://127.0.0.1:5000/admin/login](http://127.0.0.1:5000/admin/login)

---

## 🔐 Administrator Access & Security Notes

- **Admin Login Route:** `/admin/login`
- **Default Configured Admin Email:** `DanishMalikhts@gmail.com`
- **Admin Role Enforcement:** All `/admin/*` routes strictly verify session permissions on the server. Customers attempting to access admin endpoints are redirected with access denied warnings.
- **Passwords:** Passwords are never stored or logged in plain text. They are hashed using scrypt with cryptographically random salts.

---

## 💳 Payment Gateway Configuration (Razorpay)

By default, the store operates in **Cash on Delivery (COD) & Doorstep UPI** mode with verified server-side orders. To enable live online card/UPI payments:
1. Create a merchant account at [Razorpay Dashboard](https://dashboard.razorpay.com/).
2. Obtain your `Key ID` and `Key Secret`.
3. Add them to your `.env` file:
   ```env
   RAZORPAY_KEY_ID=rzp_live_xxxxxxxx
   RAZORPAY_KEY_SECRET=xxxxxxxxxxxxxxxx
   ```
4. Enable the Razorpay toggle inside `/admin/settings`.

---

## 📋 Production Deployment Checklist

1. [ ] Generate a secure 64-character random string for `SECRET_KEY` in `.env`.
2. [ ] Point `DATABASE_PATH` to persistent storage or configure PostgreSQL / Supabase connection strings.
3. [ ] Set up an HTTPS reverse proxy (e.g. Nginx, Caddy, or Cloudflare).
4. [ ] Run `python setup_admin.py` to create Danish Malik's secure administrator password.
5. [ ] Configure business email in `/admin/settings`.
