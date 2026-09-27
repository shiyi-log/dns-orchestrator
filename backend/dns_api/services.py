from backend.app.config import get_settings
from backend.app.service import DNSService
from .account_service import AccountService


service = DNSService(get_settings())
account_service = AccountService(get_settings())


def configure_account_service(settings):
    global account_service
    account_service = AccountService(settings)
    return account_service
