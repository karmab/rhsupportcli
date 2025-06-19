from base64 import b64decode
import json
import os
import sys
from shutil import move
from time import time
from urllib.request import urlopen, Request
from urllib.parse import urlencode

BASE_URL = 'https://api.access.redhat.com/support/v1/cases'

VALID_STATUSES = ['Waiting on Red Hat', 'Waiting on Customer', 'Closed']
VALID_SEVERITIES = ['1 (Urgent)', '2 (Hight)', '3 (Normal)', '4 (Low)']


def error(text):
    color = "31"
    print(f'\033[0;{color}m{text}\033[0;0m')


def warning(text, quiet=False):
    if quiet:
        return
    color = "33"
    print(f'\033[0;{color}m{text}\033[0;0m')


def info(text):
    color = "36"
    print(f'\033[0;{color}m{text}\033[0;0m')


def success(text):
    color = "32"
    print(f'\033[0;{color}m{text}\033[0;0m')


def get_token(token, offlinetoken=None):
    home = f"{os.environ['HOME']}/.rhsupport"
    url = 'https://sso.redhat.com/auth/realms/redhat-external/protocol/openid-connect/token'
    if token is not None:
        segment = token.split('.')[1]
        padding = len(segment) % 4
        segment += padding * '='
        expires_on = json.loads(b64decode(segment))['exp']
        remaining = expires_on - time()
        if expires_on == 0 or remaining > 600:
            return token
    data = {"client_id": "rhsm-api", "grant_type": "refresh_token", "refresh_token": offlinetoken}
    data = urlencode(data).encode("ascii")
    result = urlopen(url, data=data).read()
    page = result.decode("utf8")
    token = json.loads(page)['access_token']
    with open(f"{home}/token.txt", 'w') as f:
        f.write(token)
    return token


class RHsupportClient(object):
    def __init__(self):
        home = f"{os.environ['HOME']}/.rhsupport"
        offlinetokenpath = f'{home}/offlinetoken.txt'
        tokenpath = f'{home}/token.txt'
        tokenpath = f'{home}/token.txt'
        if not os.path.exists(home):
            os.mkdir(home)
        offlinetoken = os.environ.get('OFFLINETOKEN')
        if os.path.exists(offlinetokenpath):
            offlinetoken = open(offlinetokenpath).read().strip()
        elif offlinetoken is None:
            error("offlinetoken needs to be set. Get it at https://access.redhat.com/management/api")
            sys.exit(1)
        if os.path.exists(tokenpath):
            token = get_token(token=open(tokenpath).read().strip(), offlinetoken=offlinetoken)
        else:
            try:
                token = get_token(token=None, offlinetoken=offlinetoken)
            except Exception as e:
                error(f"Hit issue when trying to set token. Got {e}")
                if os.path.exists(offlinetokenpath):
                    error(f"Moving wrong offlinetoken file to {offlinetokenpath}.old")
                    move(offlinetokenpath, f"{offlinetokenpath}.old")
                sys.exit(1)
        headers = {'Authorization': f'Bearer {token}', 'Accept': 'application/json', 'Content-Type': 'application/json'}
        # binary_headers = {'Authorization': f'Bearer {token}', 'Accept': 'application/octet-stream'}
        self.headers = headers

    def get_case(self, case):
        info(f"Retrieving case {case}")
        request = Request(f"{BASE_URL}/{case}", headers=self.headers)
        return json.loads(urlopen(request).read())

    def get_case_comments(self, case):
        info(f"Retrieving comments for case {case}")
        request = Request(f"{BASE_URL}/{case}/comments", headers=self.headers)
        return json.loads(urlopen(request).read())

    def list_cases(self, parameters={}):
        info("Retrieving cases")
        data = {'offset': 1, 'maxResults': 20}
        data.update(parameters)
        data = json.dumps(data).encode('utf-8')
        request = Request(f"{BASE_URL}/filter", headers=self.headers, method='POST', data=data)
        try:
            return json.loads(urlopen(request).read())['cases']
        except Exception as e:
            error(e)
            return []

    def create_case(self, parameters={}):
        info("Creating new case")
        data = {"product": "Other", "version": "Unknown", "summary": "Example Case",
                "description": "Example Case", "entitlementSla": "PREMIUM"}
        data.update(parameters)
        data = json.dumps(data).encode('utf-8')
        request = Request(BASE_URL, headers=self.headers, method='POST', data=data)
        try:
            return json.loads(urlopen(request).read())
        except Exception as e:
            error(e)

    def create_comment(self, case, comment):
        info(f"Creating new comment on case{case}")
        data = {"commentBody": comment}
        data = json.dumps(data).encode('utf-8')
        request = Request(f"{BASE_URL}/{case}/comments", headers=self.headers, method='POST', data=data)
        try:
            return json.loads(urlopen(request).read())
        except Exception as e:
            error(e)

    def update_case(self, case, parameters={}):
        info(f"Updating case {case}")
        if 'status' in parameters and parameters['status'] not in VALID_STATUSES:
            msg = f"Invalid status. choose betwen {','.join(VALID_STATUSES)}"
            error(msg)
            return {'result': msg}
        if 'severity' in parameters:
            severity = parameters['severity']
            if (isinstance(severity, int) or severity.isdigit()) and 1 < int(severity) < 4:
                parameters['severity'] = VALID_SEVERITIES[severity - 1]
            if parameters['severity'] not in VALID_SEVERITIES:
                msg = f"Invalid severity. choose betwen {','.join(VALID_SEVERITIES)}"
                error(msg)
                return {'result': msg}
        data = json.dumps(parameters).encode('utf-8')
        request = Request(f"{BASE_URL}/{case}", headers=self.headers, method='PUT', data=data)
        urlopen(request).read()
        return {'result': 'success'}
