import time
import requests
from requests_html import HTMLSession
import re
import json
import hashlib
import os
from slugify import slugify
from .session_manager import CookieSessionManager
from .exception.instagram_auth_exception import InstagramAuthException
from .exception.instagram_exception import InstagramException
from .exception.instagram_not_found_exception import InstagramNotFoundException
from .model.account import Account
from . import endpoints
import http.cookiejar

class Instagram:
    HTTP_NOT_FOUND = 404
    HTTP_OK = 200
    HTTP_FORBIDDEN = 403
    HTTP_BAD_REQUEST = 400

    MAX_COMMENTS_PER_REQUEST = 300
    MAX_LIKES_PER_REQUEST = 50
    # 30 mins time limit on operations that require multiple self.__req
    PAGING_TIME_LIMIT_SEC = 1800
    PAGING_DELAY_MINIMUM_MICROSEC = 1000000  # 1 sec min delay to simulate browser
    PAGING_DELAY_MAXIMUM_MICROSEC = 3000000  # 3 sec max delay to simulate browser

    instance_cache = None

    def __init__(self, sleep_between_requests=0):
        self.__req = HTMLSession()
        self.paging_time_limit_sec = Instagram.PAGING_TIME_LIMIT_SEC
        self.paging_delay_minimum_microsec = Instagram.PAGING_DELAY_MINIMUM_MICROSEC
        self.paging_delay_maximum_microsec = Instagram.PAGING_DELAY_MAXIMUM_MICROSEC

        self.session_username = None
        self.session_password = None
        self.cookie=None
        self.user_session = None
        self.rhx_gis = None
        self.sleep_between_requests = sleep_between_requests
        self.user_agent = 'Instagram 126.0.0.25.121 Android (23/6.0.1; 320dpi; 720x1280; samsung; SM-A310F; a3xelte; samsungexynos7580; en_GB; 110937453)'

    def set_cookies(self,cookie):
        cj = http.cookiejar.MozillaCookieJar(cookie)
        cj.load()
        cookie = requests.utils.dict_from_cookiejar(cj)
        self.cookie=cookie
        self.user_session = cookie

    def with_credentials(self, username, password, session_folder=None):
        """
        param string username
        param string password
        param null sessionFolder

        return Instagram
        """
        Instagram.instance_cache = None

        if not session_folder:
            cwd = os.getcwd()
            session_folder = cwd + os.path.sep + 'sessions' + os.path.sep

        if isinstance(session_folder, str):

            Instagram.instance_cache = CookieSessionManager(
                session_folder, slugify(username) + '.txt')

        else:
            Instagram.instance_cache = session_folder

        Instagram.instance_cache.empty_saved_cookies()


        self.session_username = username
        self.session_password = password

    def generate_headers(self, session, gis_token=None):
        """
        :param session: user session dict
        :param gis_token: a token used to be verified by instagram in header
        :return: header dict
        """
        headers = {}
        if session is not None:
            cookies = ''

            for key in session.keys():
                cookies += f"{key}={session[key]}; "

            csrf = session['x-csrftoken'] if session['csrftoken'] is None else \
                session['csrftoken']

            headers = {
                'cookie': cookies,
                'referer': endpoints.BASE_URL + '/',
                'x-csrftoken': csrf
            }

        if self.user_agent is not None:
            headers['user-agent'] = self.user_agent

            if gis_token is not None:
                headers['x-instagram-gis'] = gis_token

        return headers

    def __generate_gis_token(self, variables):
        """
        :param variables: a dict used to  generate_gis_token
        :return: a token used to be verified by instagram
        """
        rhx_gis = self.__get_rhx_gis() if self.__get_rhx_gis() is not None else 'NULL'
        string_to_hash = ':'.join([rhx_gis, json.dumps(variables, separators=(',', ':')) if isinstance(variables, dict) else variables])
        return hashlib.md5(string_to_hash.encode('utf-8')).hexdigest()

    def __get_rhx_gis(self):
        """
        :return: a string to generate gis_token
        """
        if self.rhx_gis is None:
            try:
                shared_data = self.__get_shared_data_from_page()
            except Exception as _:
                raise InstagramException('Could not extract gis from page')

            if 'rhx_gis' in shared_data.keys():
                self.rhx_gis = shared_data['rhx_gis']
            else:
                self.rhx_gis = None

        return self.rhx_gis

    def __get_mid(self):
        """manually fetches the machine id from graphQL"""
        time.sleep(self.sleep_between_requests)
        response = self.__req.get('https://www.instagram.com/web/__mid/')

        if response.status_code != Instagram.HTTP_OK:
            raise InstagramException.default(response.text,
                                             response.status_code)

        return response.text

    def __get_shared_data_from_page(self, url=endpoints.BASE_URL):
        """
        :param url: the requested url
        :return: a dict extract from page
        """
        url = url.rstrip('/') + '/'
        time.sleep(self.sleep_between_requests)
        response = self.__req.get(url, headers=self.generate_headers(
            self.user_session))

        if Instagram.HTTP_NOT_FOUND == response.status_code:
            raise InstagramNotFoundException(f"Page {url} not found")

        if not Instagram.HTTP_OK == response.status_code:
            raise InstagramException.default(response.text,
                                             response.status_code)

        return Instagram.extract_shared_data_from_body(response.text)

    @staticmethod
    def extract_shared_data_from_body(body):
        """
        :param body: html string from a page
        :return: a dict extract from page
        """
        array = re.findall(r'_sharedData = .*?;</script>', body)
        if len(array) > 0:
            raw_json = array[0][len("_sharedData ="):-len(";</script>")]

            return json.loads(raw_json)

        return None

  
    def get_account(self, username):
        """
        :param username: username
        :return: Account
        """
        time.sleep(self.sleep_between_requests)
        response = self.__req.get(endpoints.get_account_page_link(
            username), headers=self.generate_headers(self.user_session))

        if Instagram.HTTP_NOT_FOUND == response.status_code:
            raise InstagramNotFoundException(
                'Account with given username does not exist.')

        if Instagram.HTTP_OK != response.status_code:
            raise InstagramException.default(response.text,
                                             response.status_code)

        user_array = Instagram.extract_shared_data_from_body(response.text)

        if user_array['entry_data']['ProfilePage'][0]['graphql']['user'] is None:
            raise InstagramNotFoundException(
                'Account with this username does not exist')

        return Account(
            user_array['entry_data']['ProfilePage'][0]['graphql']['user'])

    def is_logged_in(self, session):
        """
        :param session: session dict
        :return: bool
        """
        if self.cookie!=None:
            return True

        if session is None or 'sessionid' not in session.keys():
            return False


        session_id = session['sessionid']
        csrf_token = session['csrftoken']

        headers = {
            'cookie': f"ig_cb=1; csrftoken={csrf_token}; sessionid={session_id};",
            'referer': endpoints.BASE_URL + '/',
            'x-csrftoken': csrf_token,
            'X-CSRFToken': csrf_token,
            'user-agent': self.user_agent,
        }

        time.sleep(self.sleep_between_requests)
        response = self.__req.get(endpoints.BASE_URL, headers=headers)
        test=response.status_code
        test2=Instagram.HTTP_OK

        if not response.status_code == Instagram.HTTP_OK:
            return False

        cookies = response.cookies.get_dict()


        if cookies is None or not 'ds_user_id' in cookies.keys():
            return False

        return True

    def login(self, force=False, two_step_verificator=None):
        """support_two_step_verification true works only in cli mode - just run login in cli mode - save cookie to file and use in any mode
        :param force: true will refresh the session
        :param two_step_verificator: true will need to do verification when an account goes wrong
        :return: headers dict
        """
        if self.session_username is None or self.session_password is None:
            raise InstagramAuthException("User credentials not provided")

        session = json.loads(
            Instagram.instance_cache.get_saved_cookies()) if Instagram.instance_cache.get_saved_cookies() != None else None

        if force or not self.is_logged_in(session):
            time.sleep(self.sleep_between_requests)
            response = self.__req.get(endpoints.BASE_URL)
            if not response.status_code == Instagram.HTTP_OK:
                raise InstagramException.default(response.text,
                                                 response.status_code)

            match = re.findall(r'"csrf_token":"(.*?)"', response.text)

            if len(match) > 0:
                csrfToken = match[0]

            cookies = response.cookies.get_dict()

            # cookies['mid'] doesnt work at the moment so fetch it with function
            mid = self.__get_mid()

            headers = {
                'cookie': f"ig_cb=1; csrftoken={csrfToken}; mid={mid};",
                'referer': endpoints.BASE_URL + '/',
                'x-csrftoken': csrfToken,
                'X-CSRFToken': csrfToken,
                'user-agent': self.user_agent,
            }
            payload = {'username': self.session_username,
                       'enc_password': f"#PWD_INSTAGRAM_BROWSER:0:{int(time.time())}:{self.session_password}"}
            response = self.__req.post(endpoints.LOGIN_URL, data=payload,
                                       headers=headers)

            if not response.status_code == Instagram.HTTP_OK:
                if (
                        response.status_code == Instagram.HTTP_BAD_REQUEST
                        and response.text is not None
                        and response.json()['message'] == 'checkpoint_required'
                        and two_step_verificator is not None):
                    response = self.__verify_two_step(response, cookies,
                                                      two_step_verificator)
                    print('checkpoint required')

                elif response.status_code is not None and response.text is not None:
                    raise InstagramAuthException(
                        f'Response code is {response.status_code}. Body: {response.text} Something went wrong. Please report issue.',
                        response.status_code)
                else:
                    raise InstagramAuthException(
                        'Something went wrong. Please report issue.',
                        response.status_code)
            elif not response.json()['authenticated']:
                raise InstagramAuthException('User credentials are wrong.')

            cookies = response.cookies.get_dict()

            cookies['mid'] = mid
            Instagram.instance_cache.set_saved_cookies(json.dumps(cookies, separators=(',', ':')))

            self.user_session = cookies

        else:
            self.user_session = session

        return self.generate_headers(self.user_session)
