from base64 import b64decode
import json
import mimetypes
import os
import sys
from time import time
from urllib.request import urlopen, Request
from urllib.parse import urlencode
import uuid

BASE_URL = 'https://api.access.redhat.com/support'
CASES_URL = f'{BASE_URL}/v1/cases'

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
    return token


class RHsupportClient(object):
    def __init__(self, offlinetoken=None):
        offlinetoken = offlinetoken or os.environ.get('OFFLINETOKEN')
        if offlinetoken is None:
            error('OFFLINETOKEN is not set')
            sys.exit(1)
        token = get_token(token=None, offlinetoken=offlinetoken)
        headers = {'Authorization': f'Bearer {token}', 'Accept': 'application/json', 'Content-Type': 'application/json'}
        self.headers = headers

    def get_case(self, case):
        info(f"Retrieving case {case}")
        request = Request(f"{CASES_URL}/{case}", headers=self.headers)
        return json.loads(urlopen(request).read())

    def get_comments(self, case):
        info(f"Retrieving comments for case {case}")
        request = Request(f"{CASES_URL}/{case}/comments", headers=self.headers)
        return json.loads(urlopen(request).read())

    def get_attachments(self, case, path='.'):
        info(f"Retrieving attachments for case {case}")
        request = Request(f"{CASES_URL}/{case}/attachments", headers=self.headers)
        binary_headers = self.headers.copy()
        binary_headers['Accept'] = 'application/octet-stream'
        for index, attachment in enumerate(json.loads(urlopen(request).read())):
            name = attachment.get('fileName') or f'attachment_{index}'
            url = attachment.get('link')
            info(f"Downloading attachment {name} in {path}")
            with urlopen(Request(url, headers=binary_headers)) as response:
                with open(f"{path}/{name}", 'wb') as out:
                    out.write(response.read())
        return {'result': 'success'}

    def list_cases(self, parameters={}):
        info("Retrieving cases")
        data = {'offset': 1, 'maxResults': 20}
        data.update(parameters)
        data = json.dumps(data).encode('utf-8')
        request = Request(f"{CASES_URL}/filter", headers=self.headers, method='POST', data=data)
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
        request = Request(CASES_URL, headers=self.headers, method='POST', data=data)
        try:
            return json.loads(urlopen(request).read())
        except Exception as e:
            error(e)

    def create_comment(self, case, comment):
        info(f"Creating new comment on case{case}")
        data = {"commentBody": comment}
        data = json.dumps(data).encode('utf-8')
        request = Request(f"{CASES_URL}/{case}/comments", headers=self.headers, method='POST', data=data)
        try:
            return json.loads(urlopen(request).read())
        except Exception as e:
            error(e)

    def create_attachment(self, case, path):
        path = os.path.expanduser(path)
        info(f"Creating new attachment from {path} on case {case}")
        filename = os.path.basename(path)
        content_type = mimetypes.guess_type(path)[0] or 'application/octet-stream'
        boundary = uuid.uuid4().hex
        if not os.path.exists(path):
            msg = f"file {path} not found"
            error(msg)
            return {'result': 'failure'}
        with open(path, 'rb') as f:
            file_data = f.read()
        body = (
            f'--{boundary}\r\n'
            f'Content-Disposition: form-data; name="file"; filename="{filename}"\r\n'
            f'Content-Type: {content_type}\r\n'
            f'\r\n'
        ).encode('utf-8') + file_data + f'\r\n--{boundary}--\r\n'.encode('utf-8')
        url = f'{CASES_URL}/{case}/attachments'
        headers = self.headers.copy()
        headers['Content-Type'] = f'multipart/form-data; boundary={boundary}'
        headers['Content-Length'] = str(len(body))
        request = Request(url, data=body, method='POST', headers=headers)
        try:
            return json.loads(urlopen(request).read())
        except Exception as e:
            error(e)
            return {'result': e}

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
        request = Request(f"{CASES_URL}/{case}", headers=self.headers, method='PUT', data=data)
        urlopen(request).read()
        return {'result': 'success'}

    def get_business_hours(self, timezone):
        info(f"Retrieving business hours for timezone {timezone}")
        data = {"timezone": timezone}
        data = urlencode(data)
        request = Request(f"{BASE_URL}/v1/businesshours?{data}", headers=self.headers)
        return json.loads(urlopen(request).read())

    def get_account(self):
        info("Retrieving current account")
        request = Request(f"{BASE_URL}/v1/accounts/current", headers=self.headers)
        return json.loads(urlopen(request).read())

    def list_customers(self, account):
        if account is None:
            account = self.get_account()['accountNumber']
        info(f"Retrieving customer accounts for partner {account}")
        request = Request(f"{BASE_URL}/v1/accounts/customer/{account}", headers=self.headers)
        return json.loads(urlopen(request).read())

    def list_partners(self, account):
        if account is None:
            account = self.get_account()['accountNumber']
        info(f"Retrieving partner accounts for customer {account}")
        request = Request(f"{BASE_URL}/v1/accounts/partner/{account}", headers=self.headers)
        return json.loads(urlopen(request).read())

    def list_contacts(self, account):
        if account is None:
            account = self.get_account()['accountNumber']
        info(f"Retrieving contacts for account {account}")
        request = Request(f"{BASE_URL}/v1/accounts/{account}/contacts", headers=self.headers)
        return json.loads(urlopen(request).read())

    def search_kcs(self, parameters):
        info("Searching kcs")
        if 'q' not in parameters:
            error('Missing q in parameters')
            return []
        data = json.dumps(parameters).encode('utf-8')
        request = Request(f"{BASE_URL}/search/v2/kcs", headers=self.headers, method='POST', data=data)
        try:
            return json.loads(urlopen(request).read())
        except Exception as e:
            error(e)

    def search_cases(self, parameters):
        info("Searching cases")
        if 'q' not in parameters:
            error('Missing q in parameters')
            return []
        data = json.dumps(parameters).encode('utf-8')
        request = Request(f"{BASE_URL}/search/v2/cases", headers=self.headers, method='POST', data=data)
        try:
            return json.loads(urlopen(request).read())
        except Exception as e:
            error(e)
