"""API example script: Get order data.

NOTE: You need to change several variables to make this work. See below.

NOTE: This uses the third-party 'requests' module, which is much nicer than
the standard 'urllib' module.
"""

from __future__ import print_function
import json
import sys
import requests # http://docs.python-requests.org/en/master/

# Change the following:
API_KEY = '7f075a4c5b324e3ca63f22d8dc0929c4'  # API key for the user account.
BASE_URL = 'http://localhost:8886'  # Base URL for your OrderPortal instance.
ORDER_ID = 'NMI00603'  # The ID or IUID for the order.


url = "{base}/api/v1/order/{id}".format(base=BASE_URL,
                                        id=ORDER_ID)
headers = {'X-OrderPortal-API-key': API_KEY}

response = requests.get(url, headers=headers)

if response.status_code != 200:
    sys.exit("{} {}".format(response.status_code, response.reason))

print(json.dumps(response.json(), indent=2))
