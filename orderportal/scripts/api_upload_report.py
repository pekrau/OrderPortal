"""API example script: Uploading the order report.

NOTE: The upload operation URL requires the IUID for the order.

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
ORDER_IUID = 'b1abccfbc77048e1941034d7c0101f22'  # The IUID for the order!

url = "{base}/api/v1/order/{iuid}/report".format(base=BASE_URL,
                                                 iuid=ORDER_IUID)
headers = {'X-OrderPortal-API-key': API_KEY,
           'content-type': 'text/plain'}
data = 'Some report text.\nAnd a second line.'

# NOTE: The method PUT must be used here.
response = requests.put(url, headers=headers, data=data)

if response.status_code != 200:
    sys.exit("{} {}".format(response.status_code, response.reason))

print('report updloaded')
