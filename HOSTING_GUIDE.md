# HIGH TECH MOBILE — Production Hosting & Deployment Guide
(Website Ko Internet Par Live Host Karne Ka Asaan Tareeqa)

Is package me **HIGH TECH MOBILE** ki complete working website, clean production database (0 fake orders), aur real admin panel ready hai.

---

## 📦 Package Summary
- **ZIP File:** `high_tech_mobile_production.zip`
- **WSGI Entrypoint:** `wsgi.py` (`wsgi:app`)
- **Store Owners:** Avid Malik & Danish Malik
- **Admin Email:** `avidmalikhts@gmail.com`
- **Admin Password:** `nayra@99667`
- **Showroom Address:** Ruheri, Hathras, Uttar Pradesh - 204101, India
- **Live GPS Map:** https://www.google.com/maps?q=27.643748,78.063498
- **Live Location Tracker:** https://www.where-am-i.co/@27.643748,78.063498,z14
- **Business Model:** Showroom Store Pickup Only (Dukan Par Aakar Kharidein — ₹0 Advance Booking)

---

## 🚀 Option 1: Render.com Par Host Karein (Sabse Asaan & 100% Free)

Render.com par bina credit card ke 2 minute me free hosting ho jati hai jisme Free SSL (HTTPS) certificate bhi milta hai.

### Step-by-Step:
1. **GitHub Par Upload Karein:**
   - [github.com](https://github.com) par free account banayein aur **New Repository** banayein (e.g. `high-tech-mobile`).
   - Project files ko GitHub repository me upload karein.

2. **Render Account Banayein:**
   - [render.com](https://render.com) par jakar **Sign Up with GitHub** karein.

3. **New Web Service Create Karein:**
   - Dashboard me **New +** button par click karke **Web Service** chunein.
   - Apni GitHub repository (`high-tech-mobile`) select karein.
   - Yeh settings bharein:
     - **Name:** `high-tech-mobile`
     - **Region:** Singapore / Frankfurt (Asia ke paas)
     - **Branch:** `main`
     - **Runtime:** `Python 3`
     - **Build Command:** `pip install -r requirements.txt`
     - **Start Command:** `gunicorn wsgi:app`
     - **Instance Type:** `Free`

4. **Environment Variables (Optional):**
   - **Environment Variables** tab me add karein:
     - `SECRET_KEY`: `high-tech-mobile-prod-secret-2026`
     - `ADMIN_EMAIL`: `avidmalikhts@gmail.com`
     - `ADMIN_DEFAULT_PASSWORD`: `nayra@99667`

5. **Deploy Karein:**
   - **Deploy Web Service** par click karein.
   - 2 minute me aapki website live ho jayegi (e.g. `https://high-tech-mobile.onrender.com`).

---

## 🐍 Option 2: PythonAnywhere.com Par Host Karein (Free & Popular)

Agar aapko direct files upload karke chalana hai:

1. [pythonanywhere.com](https://www.pythonanywhere.com) par free Beginner account banayein.
2. **Files** tab me jakar `high_tech_mobile_production.zip` upload karein aur extract karein:
   ```bash
   unzip high_tech_mobile_production.zip -d hightech
   ```
3. **Web** tab me jayein &rarr; **Add a new web app** &rarr; **Manual configuration** &rarr; **Python 3.10 / 3.11** select karein.
4. **Virtualenv** section me:
   ```bash
   pip install -r requirements.txt
   ```
5. **WSGI configuration file** link par click karein aur usme yeh likhein:
   ```python
   import sys
   import os

   path = '/home/yourusername/hightech'
   if path not in sys.path:
       sys.path.append(path)

   from wsgi import app as application
   ```
6. **Reload** button dabayein. Website aapke username ke URL par live ho jayegi!

---

## 🌐 Option 3: cPanel / Shared Hosting (Hostinger, GoDaddy, Namecheap)

Agar aapke paas domain aur cPanel hosting hai:

1. cPanel me login karein aur **"Setup Python App"** search karein.
2. **Create Application** par click karein:
   - **Python version:** `3.10` ya `3.11`
   - **Application root:** `hightech`
   - **Application URL:** apna domain name select karein (e.g. `hightechmobile.in`)
   - **Application startup file:** `wsgi.py`
   - **Application Entry point:** `app`
3. **File Manager** me jakar `hightech` folder me `high_tech_mobile_production.zip` upload karein aur Extract karein.
4. cPanel me terminal khol kar ya virtual environment me run karein:
   ```bash
   pip install -r requirements.txt
   ```
5. **Restart** button click karein. Website domain par live ho jayegi!

---

## 🖥️ Option 4: VPS Server (Ubuntu / DigitalOcean / AWS / Linode)

Agar aapke paas Ubuntu VPS hai:

```bash
# 1. System packages install karein
sudo apt update && sudo apt install -y python3-pip python3-venv nginx

# 2. Directory banayein & zip extract karein
mkdir /var/www/hightechmobile && cd /var/www/hightechmobile
# (Upload files here)

# 3. Virtualenv banayein & packages install karein
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# 4. Systemd service banayein (/etc/systemd/system/hightech.service)
sudo nano /etc/systemd/system/hightech.service
```

Paste service configuration:
```ini
[Unit]
Description=HIGH TECH MOBILE Gunicorn Service
After=network.target

[Service]
User=www-data
Group=www-data
WorkingDirectory=/var/www/hightechmobile
Environment="PATH=/var/www/hightechmobile/venv/bin"
ExecStart=/var/www/hightechmobile/venv/bin/gunicorn --workers 3 --bind unix:hightech.sock wsgi:app

[Install]
WantedBy=multi-user.target
```

Start service and enable Nginx:
```bash
sudo systemctl start hightech
sudo systemctl enable hightech
```

---

## 🔑 Admin Login Information (Production)
- **Admin Dashboard Route:** `/admin/login`
- **Email:** `avidmalikhts@gmail.com`
- **Password:** `nayra@99667`
