from backend.app.config import get_settings
from backend.app.service import DNSService


service = DNSService(get_settings())
