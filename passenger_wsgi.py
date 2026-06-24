import os
import sys

# ============================================================
# 1. Force Passenger to use your virtualenv's Python 3.9
# ============================================================
INTERP = "/home/servolltechco/virtualenv/wifi_manager/3.9/bin/python"
if sys.executable != INTERP:
    os.execl(INTERP, INTERP, *sys.argv)

# ============================================================
# 2. Add project paths
# ============================================================
PROJECT_ROOT = "/home/servolltechco/wifi-backend.servolltech.co.ke/wifi_manager"
sys.path.insert(0, PROJECT_ROOT)
sys.path.insert(0, os.path.join(PROJECT_ROOT, 'wifi_manager'))

# ============================================================
# 3. Django settings
# ============================================================
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'wifi_manager.settings')

# ============================================================
# 4. WSGI application
# ============================================================
from django.core.wsgi import get_wsgi_application
application = get_wsgi_application()