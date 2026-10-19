"""
WSGI Entry Point for BBAT104 TQM Library Management System (Review 2).
Provides application callable for Gunicorn, Render, Railway, Docker, and other WSGI servers.
"""

from database import init_db
from web_app import app

init_db()

# Expose 'application' as alias for compatibility with AWS Elastic Beanstalk / standard WSGI
application = app

if __name__ == "__main__":
    app.run()
