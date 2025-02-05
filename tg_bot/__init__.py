from .user_handlers import register_user_handlers
from .admin_handlers import register_admin_handlers

def register_all_handlers(dp):
    register_admin_handlers(dp)
    register_user_handlers(dp)
