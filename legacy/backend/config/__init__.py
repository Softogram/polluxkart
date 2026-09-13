# Config module
from config.settings import settings
from config.database import Database, get_db, COLLECTIONS

__all__ = ['settings', 'Database', 'get_db', 'COLLECTIONS']
