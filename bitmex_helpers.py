import urllib
import time
import hashlib
import hmac
import requests


"""Taken from BitMEX market maker."""
# Generates an API signature.
# A signature is HMAC_SHA256(secret, verb + path + expires + data), hex encoded.
# Verb must be uppercased, url is relative, expires must be an increasing 64-bit integer
# and the data, if present, must be JSON without whitespace between keys.
def generate_signature(secret, verb, url, nonce, data):
    """Generate a request signature compatible with BitMEX."""
    # Parse the url so we can remove the base and extract just the path.
    parsedURL = urllib.parse.urlparse(url)
    path = parsedURL.path
    if parsedURL.query:
        path = path + '?' + parsedURL.query

    if isinstance(data, (bytes, bytearray)):
        data = data.decode('utf8')

    # print "Computing HMAC: %s" % verb + path + str(nonce) + data
    message = verb + path + str(nonce) + data

    signature = hmac.new(bytes(secret, 'utf8'), bytes(message, 'utf8'), digestmod=hashlib.sha256).hexdigest()
    return signature


"""Taken from BitMEX market maker."""
class BitmexHeaders(requests.auth.AuthBase):
    """Attaches API Key Headers to requests."""

    def __init__(self, key, secret):
        self._key = key
        self._secret = secret

    def __call__(self, req):
        """Generate API key headers."""
        # modify and return the request
        expires = int(round(time.time()) + 5)  # 5s grace period in case of clock skew
        req.headers['api-expires'] = str(expires)
        req.headers['api-key'] = self._key
        req.headers['api-signature'] = generate_signature(self._secret, req.method, req.url, expires, req.body or '')

        return req