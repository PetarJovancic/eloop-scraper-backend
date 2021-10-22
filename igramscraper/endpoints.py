import urllib.parse


BASE_URL = 'https://www.instagram.com'
LOGIN_URL = 'https://www.instagram.com/accounts/login/ajax/'
ACCOUNT_PAGE = 'https://www.instagram.com/%s'


def get_account_page_link(username):
    return ACCOUNT_PAGE % urllib.parse.quote_plus(username)
