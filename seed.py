"""
HIGH TECH MOBILE - Database Seeding Script
Populates verified smartphone and electronics inventory, categories, brands, store settings, and coupons.
"""
import sqlite3
import json
import os
from werkzeug.security import generate_password_hash
from config import Config

def seed_database():
    db_path = Config.DATABASE_PATH
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    
    # 1. Run schema first
    schema_path = os.path.join(os.path.dirname(__file__), 'schema.sql')
    with open(schema_path, 'r', encoding='utf-8') as f:
        cur.executescript(f.read())
        
    print("[*] Seeding Store Settings...")
    settings = [
        ('store_name', 'HIGH TECH MOBILE', 'Official store brand name'),
        ('store_tagline', 'Showroom Store Pickup & Spot Verification', 'Tagline displayed on header and meta'),
        ('contact_email', 'support@hightechmobile.in', 'Customer support email'),
        ('contact_phone', '+91 98765 43210', 'Customer service phone number'),
        ('store_address', 'Ruheri, Hathras, Uttar Pradesh - 204101, India', 'Physical showroom address'),
        ('store_city', 'Ruheri, Hathras', 'Store city and town'),
        ('store_state', 'Uttar Pradesh', 'Store state'),
        ('store_coordinates', '27.643748, 78.063498', 'GPS Coordinates of showroom'),
        ('store_map_url', 'https://www.google.com/maps?q=27.643748,78.063498', 'Google Maps live navigation link'),
        ('store_live_location', 'https://www.where-am-i.co/@27.643748,78.063498,z14', 'Where Am I live location tracker'),
        ('announcement_text', '📍 Showroom Pickup Only: Reserve Online & Collect at HIGH TECH MOBILE (Ruheri, Hathras, Uttar Pradesh) • 100% Sealed Box & Spot Verification!', 'Top header bar promo text'),
        ('announcement_active', '1', '1 to show announcement bar, 0 to hide'),
        ('free_shipping_threshold', '0', 'Store pickup is always 100% free'),
        ('default_shipping_fee', '0', 'Store pickup has zero delivery fee'),
        ('cod_enabled', '1', '1 if Pay at Store is accepted, 0 otherwise'),
        ('cod_fee', '0', 'Extra fee for Store Pickup in INR (0 for free)'),
        ('tax_rate', '18', 'GST percentage for consumer electronics'),
        ('hero_badge', 'OFFICIAL STORE PICKUP & INSTANT BOOKING', 'Hero upper pill badge'),
        ('hero_title', 'Upgrade Your Mobile Experience.', 'Main homepage hero headline'),
        ('hero_subtitle', 'Reserve online, visit our Ruheri, Hathras showroom (Uttar Pradesh), inspect your brand-sealed smartphone, and pay directly at the counter with 100% trust.', 'Hero supporting text'),
        ('hero_primary_btn_text', 'Browse & Reserve Smartphones', 'Primary hero button text'),
        ('hero_primary_btn_url', '/shop?category=smartphones', 'Primary hero button target URL'),
        ('hero_secondary_btn_text', 'View Showroom Location', 'Secondary hero button text'),
        ('hero_secondary_btn_url', '/contact', 'Secondary hero button target URL'),
        ('razorpay_enabled', '0', '1 to enable Razorpay online payments, 0 for Store Pay mode')
    ]
    
    for key, val, desc in settings:
        cur.execute(
            """INSERT INTO store_settings (setting_key, setting_value, description)
               VALUES (?, ?, ?)
               ON CONFLICT(setting_key) DO UPDATE SET setting_value = excluded.setting_value""",
            (key, val, desc)
        )
        
    print("[*] Seeding Categories...")
    categories = [
        ('Smartphones', 'smartphones', 'Flagship 5G, foldables, and performance smartphones from top tier global brands', 'https://images.unsplash.com/photo-1598327105666-5b89351aff97?w=500&auto=format&fit=crop&q=80', 1),
        ('Tablets', 'tablets', 'Pro performance OLED tablets and iPads for creators and professionals', 'https://images.unsplash.com/photo-1544244015-0df4b3ffc6b0?w=500&auto=format&fit=crop&q=80', 2),
        ('Laptops', 'laptops', 'Ultra-fast laptops, MacBooks, and high-performance notebooks', 'https://images.unsplash.com/photo-1496181133206-80ce9b88a853?w=500&auto=format&fit=crop&q=80', 3),
        ('Smartwatches', 'smartwatches', 'Cellular sports watches, health trackers, and luxury wearable tech', 'https://images.unsplash.com/photo-1523275335684-37898b6baf30?w=500&auto=format&fit=crop&q=80', 4),
        ('Accessories', 'accessories', 'GaN fast chargers, MagSafe cases, braided cables, and adapters', 'https://images.unsplash.com/photo-1583863788434-e58a36330cf0?w=500&auto=format&fit=crop&q=80', 5),
        ('Audio', 'audio', 'Active noise cancelling wireless earbuds, audiophile over-ear headphones, and Hi-Fi soundbars', 'https://images.unsplash.com/photo-1505740420928-5e560c06d30e?w=500&auto=format&fit=crop&q=80', 6),
        ('Gaming', 'gaming', 'Mobile controllers, cooling clips, mechanical wireless keyboards, and headsets', 'https://images.unsplash.com/photo-1600080972464-8e5f35f63d08?w=500&auto=format&fit=crop&q=80', 7)
    ]
    
    cat_ids = {}
    for name, slug, desc, img, order in categories:
        cur.execute(
            """INSERT INTO categories (name, slug, description, image_url, sort_order)
               VALUES (?, ?, ?, ?, ?)
               ON CONFLICT(slug) DO UPDATE SET name=excluded.name, description=excluded.description, image_url=excluded.image_url, sort_order=excluded.sort_order""",
            (name, slug, desc, img, order)
        )
        cur.execute("SELECT id FROM categories WHERE slug = ?", (slug,))
        cat_ids[slug] = cur.fetchone()[0]

    print("[*] Seeding Brands...")
    brands = [
        ('Apple', 'apple', 'https://upload.wikimedia.org/wikipedia/commons/f/fa/Apple_logo_black.svg'),
        ('Samsung', 'samsung', 'https://upload.wikimedia.org/wikipedia/commons/2/24/Samsung_Logo.svg'),
        ('Google', 'google', 'https://upload.wikimedia.org/wikipedia/commons/2/2f/Google_2015_logo.svg'),
        ('OnePlus', 'oneplus', 'https://upload.wikimedia.org/wikipedia/commons/0/02/OnePlus_logo.svg'),
        ('Xiaomi', 'xiaomi', 'https://upload.wikimedia.org/wikipedia/commons/a/ae/Xiaomi_logo_%282021-%29.svg'),
        ('Sony', 'sony', 'https://upload.wikimedia.org/wikipedia/commons/c/ca/Sony_logo.svg'),
        ('Spigen', 'spigen', 'https://images.unsplash.com/photo-1603539947678-cd3954ed515d?w=200&auto=format&fit=crop&q=80'),
        ('Anker', 'anker', 'https://images.unsplash.com/photo-1583863788434-e58a36330cf0?w=200&auto=format&fit=crop&q=80')
    ]
    
    brand_ids = {}
    for name, slug, logo in brands:
        cur.execute(
            """INSERT INTO brands (name, slug, logo_url)
               VALUES (?, ?, ?)
               ON CONFLICT(slug) DO UPDATE SET name=excluded.name, logo_url=excluded.logo_url""",
            (name, slug, logo)
        )
        cur.execute("SELECT id FROM brands WHERE slug = ?", (slug,))
        brand_ids[slug] = cur.fetchone()[0]

    print("[*] Seeding Flagship Products & Tech Catalog...")
    products_data = [
        {
            "name": "Apple iPhone 16 Pro Max",
            "slug": "apple-iphone-16-pro-max",
            "sku": "IPHONE-16PM-TI",
            "brand_slug": "apple",
            "category_slug": "smartphones",
            "price": 144900,
            "original_price": 159900,
            "stock": 28,
            "is_featured": 1,
            "is_bestseller": 1,
            "is_new": 1,
            "short_description": "Forged in Grade 5 Titanium with the breakthrough A18 Pro chip, 48MP Fusion camera system with 5x Telephoto, and Camera Control.",
            "full_description": "The iPhone 16 Pro Max features a stunning Grade 5 Titanium design with thinner borders for our largest 6.9-inch Super Retina XDR display ever. Powered by the industry-leading A18 Pro chip with 6-core GPU, it delivers console-level gaming and superior efficiency. Enjoy all-new Camera Control for instant focal adjustments, 4K 120 fps Dolby Vision recording, and unparalleled battery endurance.",
            "specs": {
                "Display": "6.9-inch Super Retina XDR OLED, 120Hz ProMotion, 2000 nits peak brightness",
                "Processor": "Apple A18 Pro (3nm architecture) with 16-core Neural Engine",
                "Rear Cameras": "48MP Fusion (f/1.78) + 48MP Ultra Wide (f/2.2) + 12MP 5x Telephoto (f/2.8)",
                "Front Camera": "12MP TrueDepth with autofocus",
                "Battery": "Up to 33 hours video playback, MagSafe wireless fast charging",
                "OS": "iOS 18 with Apple Intelligence",
                "Connectivity": "5G (sub-6 GHz and mmWave), Wi-Fi 7, Bluetooth 5.3, USB-C 3.0 (up to 10Gb/s)",
                "Water Resistance": "IP68 rated (maximum depth of 6 metres up to 30 minutes)"
            },
            "images": [
                "https://images.unsplash.com/photo-1695048133142-1a20484d2569?w=800&auto=format&fit=crop&q=80",
                "https://images.unsplash.com/photo-1591337676887-a217a6970a8a?w=800&auto=format&fit=crop&q=80",
                "https://images.unsplash.com/photo-1510557880182-3d4d3cba35a5?w=800&auto=format&fit=crop&q=80"
            ],
            "variants": [
                {"color_name": "Desert Titanium", "color_hex": "#C5B29F", "storage": "256GB", "ram": "8GB", "additional_price": 0, "stock": 10},
                {"color_name": "Natural Titanium", "color_hex": "#9E9A93", "storage": "256GB", "ram": "8GB", "additional_price": 0, "stock": 8},
                {"color_name": "Natural Titanium", "color_hex": "#9E9A93", "storage": "512GB", "ram": "8GB", "additional_price": 20000, "stock": 6},
                {"color_name": "Black Titanium", "color_hex": "#2B2B2B", "storage": "1TB", "ram": "8GB", "additional_price": 40000, "stock": 4}
            ]
        },
        {
            "name": "Samsung Galaxy S24 Ultra 5G",
            "slug": "samsung-galaxy-s24-ultra-5g",
            "sku": "SAMS-S24U-TI",
            "brand_slug": "samsung",
            "category_slug": "smartphones",
            "price": 129999,
            "original_price": 144999,
            "stock": 22,
            "is_featured": 1,
            "is_bestseller": 1,
            "is_new": 1,
            "short_description": "Galaxy AI powerhouse with built-in S Pen, 200MP camera system, titanium frame, and Snapdragon 8 Gen 3 for Galaxy.",
            "full_description": "Welcome to the era of mobile AI with Galaxy S24 Ultra. Unleash whole new levels of creativity, productivity, and possibility starting with the most important device in your life: your smartphone. Encased in a durable shield of titanium and Corning Gorilla Armor, featuring a flat 6.8-inch Dynamic AMOLED 2X 120Hz display with 2600 nits peak outdoor visibility.",
            "specs": {
                "Display": "6.8-inch Dynamic AMOLED 2X, QHD+, 120Hz adaptive, 2600 nits",
                "Processor": "Qualcomm Snapdragon 8 Gen 3 for Galaxy (4nm)",
                "Rear Cameras": "200MP Wide + 50MP Periscope (5x optical / 100x Space Zoom) + 10MP Telephoto + 12MP Ultra Wide",
                "Front Camera": "12MP Dual Pixel AF",
                "Battery": "5000 mAh, 45W super fast charging 2.0, Fast Wireless Charging 2.0",
                "OS": "One UI 6.1 based on Android 14 (7 years of OS & security updates)",
                "S Pen": "Embedded Bluetooth S Pen with Air Actions",
                "Weight": "232g"
            },
            "images": [
                "https://images.unsplash.com/photo-1610945415295-d9bbf067e59c?w=800&auto=format&fit=crop&q=80",
                "https://images.unsplash.com/photo-1580910051074-3eb694886505?w=800&auto=format&fit=crop&q=80"
            ],
            "variants": [
                {"color_name": "Titanium Gray", "color_hex": "#767571", "storage": "256GB", "ram": "12GB", "additional_price": 0, "stock": 10},
                {"color_name": "Titanium Black", "color_hex": "#212121", "storage": "512GB", "ram": "12GB", "additional_price": 10000, "stock": 8},
                {"color_name": "Titanium Violet", "color_hex": "#4D465C", "storage": "256GB", "ram": "12GB", "additional_price": 0, "stock": 4}
            ]
        },
        {
            "name": "Google Pixel 9 Pro",
            "slug": "google-pixel-9-pro",
            "sku": "PIXEL-9PRO-OBS",
            "brand_slug": "google",
            "category_slug": "smartphones",
            "price": 109999,
            "original_price": 119999,
            "stock": 15,
            "is_featured": 1,
            "is_bestseller": 0,
            "is_new": 1,
            "short_description": "Engineered by Google with Tensor G4, Gemini AI integrated natively, and pro-level triple camera system with Super Res Zoom.",
            "full_description": "Pixel 9 Pro is Google's most powerful phone yet. Crafted with polished metal and silky matte glass back, featuring the vivid Super Actua display. Google Tensor G4 brings advanced Gemini AI capabilities to life — from Magic Editor photo transformations to Pixel Studio instant image generation.",
            "specs": {
                "Display": "6.3-inch Super Actua LTPO OLED (1-120Hz), 3000 nits peak brightness",
                "Processor": "Google Tensor G4 with Titan M2 security coprocessor",
                "Cameras": "50MP Octa PD Wide + 48MP Quad PD Ultra Wide with Macro + 48MP Quad PD 5x Telephoto",
                "RAM / Storage": "16GB RAM for high-speed AI tasks",
                "Battery": "4700 mAh, fast charging, Battery Share",
                "OS": "Android 15 with 7 years of Pixel Drops"
            },
            "images": [
                "https://images.unsplash.com/photo-1598327105666-5b89351aff97?w=800&auto=format&fit=crop&q=80",
                "https://images.unsplash.com/photo-1585060544812-6b45742d762f?w=800&auto=format&fit=crop&q=80"
            ],
            "variants": [
                {"color_name": "Obsidian", "color_hex": "#1F2022", "storage": "256GB", "ram": "16GB", "additional_price": 0, "stock": 8},
                {"color_name": "Porcelain", "color_hex": "#F3F1ED", "storage": "256GB", "ram": "16GB", "additional_price": 0, "stock": 5},
                {"color_name": "Hazel", "color_hex": "#63675F", "storage": "512GB", "ram": "16GB", "additional_price": 15000, "stock": 2}
            ]
        },
        {
            "name": "OnePlus 12 5G",
            "slug": "oneplus-12-5g",
            "sku": "OP-12-FLOW",
            "brand_slug": "oneplus",
            "category_slug": "smartphones",
            "price": 64999,
            "original_price": 69999,
            "stock": 35,
            "is_featured": 1,
            "is_bestseller": 1,
            "is_new": 0,
            "short_description": "Smooth Beyond Belief. Snapdragon 8 Gen 3, 4th Gen Hasselblad Camera for Mobile, and 100W SUPERVOOC charging.",
            "full_description": "The OnePlus 12 redefines the flagship benchmark. It seamlessly combines ultra-flagship hardware with state-of-the-art software optimizations. Features a dazzling 2K 120Hz ProXDR display, 5400 mAh massive dual-cell battery, and dual vapor chamber cryogenic cooling.",
            "specs": {
                "Display": "6.82-inch 2K 120Hz ProXDR Display with LTPO 3.0, 4500 nits peak",
                "Processor": "Qualcomm Snapdragon 8 Gen 3 (4nm)",
                "Cameras": "50MP Sony LYT-808 (f/1.6, OIS) + 64MP 3x Periscope (f/2.6, OIS) + 48MP Ultra Wide",
                "Battery": "5400 mAh with 100W Wired SUPERVOOC + 50W Wireless AIRVOOC",
                "Audio": "Dual stereo speakers with Dolby Atmos and spatial audio"
            },
            "images": [
                "https://images.unsplash.com/photo-1565849904461-04a58ad377e0?w=800&auto=format&fit=crop&q=80",
                "https://images.unsplash.com/photo-1511707171634-5f897ff02aa9?w=800&auto=format&fit=crop&q=80"
            ],
            "variants": [
                {"color_name": "Flowy Emerald", "color_hex": "#2E534D", "storage": "256GB", "ram": "12GB", "additional_price": 0, "stock": 20},
                {"color_name": "Silky Black", "color_hex": "#1A1A1A", "storage": "512GB", "ram": "16GB", "additional_price": 5000, "stock": 15}
            ]
        },
        {
            "name": "Apple Watch Ultra 2 (Cellular)",
            "slug": "apple-watch-ultra-2-cellular",
            "sku": "AW-ULTRA2-49",
            "brand_slug": "apple",
            "category_slug": "smartwatches",
            "price": 89900,
            "original_price": 94900,
            "stock": 12,
            "is_featured": 1,
            "is_bestseller": 0,
            "is_new": 1,
            "short_description": "The ultimate sports and adventure smartwatch. 49mm rugged aerospace-grade titanium case, S9 SiP, and 3000 nits display.",
            "full_description": "Engineered for endurance athletes, outdoor adventurers, and ocean explorers. The Apple Watch Ultra 2 features precision dual-frequency GPS, a customizable Action button, Depth gauge with water temperature sensor, and up to 72 hours of battery in Low Power Mode.",
            "specs": {
                "Case": "49mm Aerospace-grade Titanium with sapphire crystal front",
                "Display": "Always-On Retina display, 3000 nits peak brightness",
                "Chip": "S9 SiP with 4-core Neural Engine and Double Tap gesture",
                "Sensors": "ECG, Blood Oxygen, Temperature sensing, Compass, Dual-frequency GPS",
                "Water Resistance": "100m water resistant, certified EN13319 for diving up to 40m"
            },
            "images": [
                "https://images.unsplash.com/photo-1523275335684-37898b6baf30?w=800&auto=format&fit=crop&q=80",
                "https://images.unsplash.com/photo-1508685096489-7aacd43bd3b1?w=800&auto=format&fit=crop&q=80"
            ],
            "variants": [
                {"color_name": "Titanium with Orange Ocean Band", "color_hex": "#E05A2B", "storage": "64GB", "ram": "Default", "additional_price": 0, "stock": 6},
                {"color_name": "Titanium with Blue Alpine Loop", "color_hex": "#29465B", "storage": "64GB", "ram": "Default", "additional_price": 0, "stock": 6}
            ]
        },
        {
            "name": "Samsung Galaxy Watch 7 (Bluetooth + LTE)",
            "slug": "samsung-galaxy-watch-7-lte",
            "sku": "SAMS-GW7-44",
            "brand_slug": "samsung",
            "category_slug": "smartwatches",
            "price": 32999,
            "original_price": 36999,
            "stock": 18,
            "is_featured": 0,
            "is_bestseller": 1,
            "is_new": 1,
            "short_description": "Advanced health tracking with BioActive Sensor, Energy Score, and Dual GPS navigation powered by Wear OS 5.",
            "full_description": "Meet your everyday wellness companion. Powered by a high-efficiency 3nm processor, Galaxy Watch 7 offers precise sleep apnea detection, personalized workout insights, and seamless connection with Samsung Galaxy ecosystem.",
            "specs": {
                "Display": "1.5-inch Super AMOLED (480x480), Sapphire Crystal",
                "Processor": "Exynos W1000 (3nm, 5-Core)",
                "Health": "Heart Rate, ECG, BIA body composition, Blood Pressure, Sleep coaching",
                "Battery": "425 mAh, WPC-based wireless fast charging"
            },
            "images": [
                "https://images.unsplash.com/photo-1579586337278-3befd40fd17a?w=800&auto=format&fit=crop&q=80"
            ],
            "variants": [
                {"color_name": "Green", "color_hex": "#4C6B58", "storage": "32GB", "ram": "2GB", "additional_price": 0, "stock": 10},
                {"color_name": "Silver", "color_hex": "#CFCFCF", "storage": "32GB", "ram": "2GB", "additional_price": 0, "stock": 8}
            ]
        },
        {
            "name": "Apple AirPods Pro (2nd Gen with USB-C)",
            "slug": "apple-airpods-pro-2nd-gen-usbc",
            "sku": "AIRPODS-PRO2-USBC",
            "brand_slug": "apple",
            "category_slug": "audio",
            "price": 24900,
            "original_price": 27900,
            "stock": 40,
            "is_featured": 1,
            "is_bestseller": 1,
            "is_new": 0,
            "short_description": "Up to 2x more Active Noise Cancellation, Adaptive Audio, Transparency mode, and MagSafe Charging Case (USB-C).",
            "full_description": "AirPods Pro (2nd generation) with USB-C deliver unparalleled audio fidelity with H2 chip processing. Features Adaptive Audio that blends Active Noise Cancellation with Transparency mode depending on your surroundings, along with personalized Spatial Audio and dynamic head tracking.",
            "specs": {
                "Audio Tech": "Apple H2 headphone chip, Apple U1/U2 chip in MagSafe case",
                "Noise Control": "Active Noise Cancellation, Adaptive Audio, Conversation Awareness",
                "Battery": "Up to 6 hours listening time with ANC on (up to 30 hours with case)",
                "Charging": "USB-C, MagSafe, Apple Watch charger, Qi-certified chargers",
                "Sweat/Water Resistance": "IP54 dust, sweat, and water resistant"
            },
            "images": [
                "https://images.unsplash.com/photo-1600294037681-c80b4cb5b434?w=800&auto=format&fit=crop&q=80",
                "https://images.unsplash.com/photo-1588423771073-b8903fbb85b5?w=800&auto=format&fit=crop&q=80"
            ],
            "variants": [
                {"color_name": "White", "color_hex": "#FFFFFF", "storage": "N/A", "ram": "N/A", "additional_price": 0, "stock": 40}
            ]
        },
        {
            "name": "Sony WH-1000XM5 Wireless Noise Cancelling Headphones",
            "slug": "sony-wh-1000xm5-wireless-headphones",
            "sku": "SONY-XM5-SLV",
            "brand_slug": "sony",
            "category_slug": "audio",
            "price": 29990,
            "original_price": 34990,
            "stock": 25,
            "is_featured": 1,
            "is_bestseller": 1,
            "is_new": 0,
            "short_description": "Industry-leading noise cancellation with 8 microphones, Auto NC Optimizer, and up to 30 hours of continuous playback.",
            "full_description": "The WH-1000XM5 headphones rewrite the rules for distraction-free listening. Two processors control 8 microphones for unprecedented noise cancellation and exceptional call quality. With a specially designed 30mm driver unit, you enjoy pure, natural audio reproduction and LDAC high-res audio streaming.",
            "specs": {
                "Driver Unit": "30mm precision-engineered carbon fiber composite dome",
                "Noise Cancellation": "Dual Processors (Integrated Processor V1 + HD Noise Cancelling Processor QN1)",
                "Battery Life": "Up to 30 hours (ANC ON), 40 hours (ANC OFF), 3 min quick charge gives 3 hours",
                "Bluetooth": "Version 5.2 with LDAC, AAC, SBC and Multipoint connection (connect 2 devices)"
            },
            "images": [
                "https://images.unsplash.com/photo-1505740420928-5e560c06d30e?w=800&auto=format&fit=crop&q=80",
                "https://images.unsplash.com/photo-1546435770-a3e426bf472b?w=800&auto=format&fit=crop&q=80"
            ],
            "variants": [
                {"color_name": "Silver", "color_hex": "#D1D0CE", "storage": "N/A", "ram": "N/A", "additional_price": 0, "stock": 13},
                {"color_name": "Black", "color_hex": "#1E1E1E", "storage": "N/A", "ram": "N/A", "additional_price": 0, "stock": 12}
            ]
        },
        {
            "name": "Apple iPad Pro 11-inch (M4 Chip)",
            "slug": "apple-ipad-pro-11-inch-m4",
            "sku": "IPAD-M4-11",
            "brand_slug": "apple",
            "category_slug": "tablets",
            "price": 99900,
            "original_price": 109900,
            "stock": 14,
            "is_featured": 1,
            "is_bestseller": 0,
            "is_new": 1,
            "short_description": "Outrageously thin design with game-changing Ultra Retina XDR tandem OLED display and the hyper-fast Apple M4 processor.",
            "full_description": "The all-new iPad Pro packs outrageous power into an impossibly thin, light, and portable design. Powered by Apple M4 chip with an advanced display engine to drive the precision, color, and brightness of the Ultra Retina XDR display. Supports Apple Pencil Pro and redesigned Magic Keyboard.",
            "specs": {
                "Display": "11-inch Ultra Retina XDR Tandem OLED, 1000 nits full-screen, 1600 nits peak HDR",
                "Chip": "Apple M4 (9-core CPU, 10-core GPU, Hardware-accelerated ray tracing)",
                "Cameras": "12MP Wide rear camera + LiDAR Scanner, Landscape 12MP Ultra Wide front camera",
                "Speakers": "Four-speaker sound system with studio-quality mics",
                "Thickness": "Impossibly thin 5.3 mm"
            },
            "images": [
                "https://images.unsplash.com/photo-1544244015-0df4b3ffc6b0?w=800&auto=format&fit=crop&q=80"
            ],
            "variants": [
                {"color_name": "Space Black", "color_hex": "#1E1E1E", "storage": "256GB", "ram": "8GB", "additional_price": 0, "stock": 8},
                {"color_name": "Silver", "color_hex": "#E0E0E0", "storage": "512GB", "ram": "8GB", "additional_price": 20000, "stock": 6}
            ]
        },
        {
            "name": "Anker Prime 67W GaN Fast Wall Charger (3 Ports)",
            "slug": "anker-prime-67w-gan-fast-charger",
            "sku": "ANKER-67W-GAN",
            "brand_slug": "anker",
            "category_slug": "accessories",
            "price": 3499,
            "original_price": 4499,
            "stock": 60,
            "is_featured": 0,
            "is_bestseller": 1,
            "is_new": 0,
            "short_description": "Ultra-compact 3-port fast wall charger with GaN technology. Charges your MacBook, iPhone, and Galaxy simultaneously.",
            "full_description": "Equipped with two USB-C ports and one USB-A port, effortlessly charge your smartphone, tablet, and notebook with a single pocket-sized adapter. Delivers maximum 67W single-port charging power with intelligent PowerIQ 4.0 dynamic power distribution.",
            "specs": {
                "Total Wattage": "67W Max",
                "Ports": "2x USB-C + 1x USB-A",
                "Technology": "GaNPrime, ActiveShield 2.0 temperature monitoring",
                "Dimensions": "50% smaller than an original 67W single-port charger"
            },
            "images": [
                "https://images.unsplash.com/photo-1583863788434-e58a36330cf0?w=800&auto=format&fit=crop&q=80"
            ],
            "variants": [
                {"color_name": "Space Gray", "color_hex": "#4A4D52", "storage": "N/A", "ram": "N/A", "additional_price": 0, "stock": 60}
            ]
        },
        {
            "name": "Spigen Ultra Hybrid MagSafe Case for iPhone 16 Pro",
            "slug": "spigen-ultra-hybrid-magsafe-iphone-16-pro",
            "sku": "SPG-UH-16P-MAG",
            "brand_slug": "spigen",
            "category_slug": "accessories",
            "price": 1999,
            "original_price": 2499,
            "stock": 75,
            "is_featured": 0,
            "is_bestseller": 1,
            "is_new": 1,
            "short_description": "Crystal-clear hybrid shock absorption case with integrated strong magnetic ring for seamless MagSafe charging.",
            "full_description": "Showcase your new iPhone 16 Pro in pure clarity. The Ultra Hybrid combines a shock-absorbing flexible bumper with a rigid scratch-resistant back. Built-in neodymium magnets guarantee high-speed MagSafe wireless alignment and secure magnetic accessories grip.",
            "specs": {
                "Material": "Polycarbonate back + TPU bumper",
                "Protection": "Air Cushion Technology at all 4 corners (Military Grade Drop Certified)",
                "MagSafe Compatibility": "Strong built-in magnetic ring for wireless chargers and wallets"
            },
            "images": [
                "https://images.unsplash.com/photo-1603539947678-cd3954ed515d?w=800&auto=format&fit=crop&q=80"
            ],
            "variants": [
                {"color_name": "White Clear", "color_hex": "#ECECEC", "storage": "N/A", "ram": "N/A", "additional_price": 0, "stock": 45},
                {"color_name": "Zero One Edition", "color_hex": "#252525", "storage": "N/A", "ram": "N/A", "additional_price": 300, "stock": 30}
            ]
        },
        {
            "name": "Razer Kishi V2 Mobile Gaming Controller",
            "slug": "razer-kishi-v2-mobile-controller",
            "sku": "RZR-KISHI-V2",
            "brand_slug": "oneplus",
            "category_slug": "gaming",
            "price": 9999,
            "original_price": 11999,
            "stock": 16,
            "is_featured": 1,
            "is_bestseller": 0,
            "is_new": 0,
            "short_description": "Console-quality mobile gaming controls with microswitch buttons, analog triggers, programmable macros, and pass-through USB-C.",
            "full_description": "Rethink everything you knew about mobile gaming. The Razer Kishi V2 is a universal mobile gaming controller that brings a console-class gameplay experience to your smartphone. Play the biggest AAA mobile games and stream console/PC titles via Xbox Cloud Gaming and GeForce NOW.",
            "specs": {
                "Connectivity": "Direct low-latency USB-C connection",
                "Buttons": "Microswitch tactile face buttons and D-pad, analog triggers",
                "Compatibility": "Universal expandable bridge fits most Android and iPhone 15/16 series",
                "Charging": "Pass-through charging while playing"
            },
            "images": [
                "https://images.unsplash.com/photo-1600080972464-8e5f35f63d08?w=800&auto=format&fit=crop&q=80"
            ],
            "variants": [
                {"color_name": "Matte Black", "color_hex": "#111111", "storage": "N/A", "ram": "N/A", "additional_price": 0, "stock": 16}
            ]
        }
    ]

    for p in products_data:
        brand_id = brand_ids.get(p["brand_slug"])
        cat_id = cat_ids.get(p["category_slug"])
        specs_json = json.dumps(p["specs"])
        
        cur.execute(
            """INSERT INTO products (
                name, slug, sku, brand_id, category_id, price, original_price, cost_price,
                stock_quantity, short_description, full_description, specifications_json,
                is_featured, is_bestseller, is_new, is_published, seo_title, seo_description
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 1, ?, ?)
            ON CONFLICT(slug) DO UPDATE SET
                price=excluded.price, original_price=excluded.original_price,
                stock_quantity=excluded.stock_quantity, short_description=excluded.short_description,
                full_description=excluded.full_description, specifications_json=excluded.specifications_json,
                is_featured=excluded.is_featured, is_bestseller=excluded.is_bestseller, is_new=excluded.is_new""",
            (
                p["name"], p["slug"], p["sku"], brand_id, cat_id, p["price"], p["original_price"],
                p["price"] * 0.8, p["stock"], p["short_description"], p["full_description"], specs_json,
                p["is_featured"], p["is_bestseller"], p["is_new"],
                f"{p['name']} - Buy Online in India at Best Price | High Tech Mobile",
                p["short_description"][:155]
            )
        )
        cur.execute("SELECT id FROM products WHERE slug = ?", (p["slug"],))
        product_id = cur.fetchone()[0]
        
        # Product Images
        cur.execute("DELETE FROM product_images WHERE product_id = ?", (product_id,))
        for idx, img_url in enumerate(p["images"]):
            cur.execute(
                """INSERT INTO product_images (product_id, image_url, alt_text, sort_order, is_primary)
                   VALUES (?, ?, ?, ?, ?)""",
                (product_id, img_url, f"{p['name']} photo {idx+1}", idx, 1 if idx == 0 else 0)
            )
            
        # Variants
        cur.execute("DELETE FROM product_variants WHERE product_id = ?", (product_id,))
        for v in p["variants"]:
            v_sku = f"{p['sku']}-{v['color_name'][:3].upper()}-{v['storage']}".replace(' ', '')
            cur.execute(
                """INSERT INTO product_variants (product_id, color_name, color_hex, storage, ram, additional_price, stock_quantity, sku)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                (product_id, v["color_name"], v["color_hex"], v["storage"], v["ram"], v["additional_price"], v["stock"], v_sku)
            )

    print("[*] Seeding Discount Coupons...")
    coupons = [
        ('TECH10', 'percentage', 10, 1999, 2000, 500, '2027-12-31 23:59:59'),
        ('FLAT500', 'fixed', 500, 4999, 500, 300, '2027-12-31 23:59:59'),
        ('WELCOME5', 'percentage', 5, 999, 1000, 1000, '2027-12-31 23:59:59')
    ]
    for code, dtype, val, min_amt, max_disc, limit, expires in coupons:
        cur.execute(
            """INSERT INTO coupons (code, discount_type, discount_value, min_order_amount, max_discount_amount, usage_limit, expires_at, is_active)
               VALUES (?, ?, ?, ?, ?, ?, ?, 1)
               ON CONFLICT(code) DO UPDATE SET discount_value=excluded.discount_value, min_order_amount=excluded.min_order_amount""",
            (code, dtype, val, min_amt, max_disc, limit, expires)
        )

    print("[*] Seeding Verified Indian Customer Reviews...")
    reviews_seed = [
        ('apple-iphone-16-pro-max', 'Aarav Sharma', 'Uttar Pradesh', 5, 'Best Mobile Store Experience!', 'Dukan par jakar iPhone 16 Pro Max kharida. Avid bhai aur Danish bhai ne samne seal pack box open karke diya aur official Apple warranty live verify karwayi. 100% genuine and best deal!'),
        ('samsung-galaxy-s24-ultra-5g', 'Rohan Verma', 'Noida', 5, 'Smooth Store Pickup & Instant Handover', 'Maine online booking kari aur sham ko Ruheri, Hathras dukan par jakar S24 Ultra collect kiya. Bill, warranty aur free case sab kuch 10 minute mein complete. Highly recommended!'),
        ('oneplus-12-5g', 'Pooja Patel', 'Hathras', 5, 'Transparent Pricing & Polite Owners', 'Avid Malik aur Danish Malik bhai and their team are extremely polite and helpful. No advance payment pressure. Verified the phone at the counter and paid through UPI.'),
        ('google-pixel-9-pro', 'Mohammad Faizan', 'Aligarh / Hathras', 5, '100% Original Sealed Box', 'Dukan par aakar kharidne ka maza hi alag hai! Samne phone dekha, inspect kiya aur satisfy hone ke baad pay kiya. Superb experience at High Tech Mobile.'),
        ('apple-watch-ultra-2-cellular', 'Vikram Malhotra', 'Mathura', 5, 'Genuine Brand Warranty & Instant Invoice', 'Bought Apple Watch Ultra 2 directly from the showroom. Genuine Indian unit with valid invoice for GST input credit.')
    ]
    
    for p_slug, author, city, rating, title, comment in reviews_seed:
        cur.execute("SELECT id FROM products WHERE slug = ?", (p_slug,))
        p_row = cur.fetchone()
        if p_row:
            cur.execute(
                """INSERT INTO reviews (product_id, customer_name, rating, title, comment, is_verified_purchase, is_approved)
                   VALUES (?, ?, ?, ?, ?, 1, 1)""",
                (p_row[0], f"{author} ({city})", rating, title, comment)
            )

    conn.commit()
    conn.close()
    print("[SUCCESS] High Tech Mobile database seeded successfully!")

if __name__ == '__main__':
    seed_database()
