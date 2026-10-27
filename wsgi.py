"""
HIGH TECH MOBILE - WSGI Entrypoint for Production Hosting
Compatible with Gunicorn, uWSGI, cPanel Passenger, Render, Railway, AWS, and DigitalOcean.
"""
import os
from app import create_app

app = create_app()

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
