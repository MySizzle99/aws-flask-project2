import sys

APP_DIR = "/var/www/flaskapp"
if APP_DIR not in sys.path:
    sys.path.insert(0, APP_DIR)

from app import app as application
