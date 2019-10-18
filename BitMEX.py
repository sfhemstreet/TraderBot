import websockets
import json
import asyncio
import hashlib
import hmac
import time
import urllib.parse


# used to create signature for auth connection 
# default URL is testnet, change URL for real trading
URL = "wss://testnet.bitmex.com"
VERB = "GET"
ENDPOINT = "/realtime"
EXPIRES = int(round(time.time()) + 100)


class BitMEX:
    def __init__(self, key, secret):
        self._key = key
        self._secret = secret

    async def connect(self):
        uri = URL + ENDPOINT
        signature = generate_signature(self._secret, VERB, ENDPOINT, EXPIRES)
        id = "bitMEX_stream"
        payload = {"op": "authKeyExpires", "args": [self._key, EXPIRES, signature]}
        async with websockets.connect(uri) as websocket:
            await websocket.send(json.dumps(payload))
            async for msg in websocket: 
                result = await interpret(json.loads(msg), id)
                if result:
                    await live_feed(websocket)
       
    async def live_feed(self, websocket):
        payload = {"op": "subscribe", "args": ["affiliate","execution","order","margin","position","privateNotifications","transact","wallet","trade"]}
    
        await websocket.send(json.dumps(payload))
        async for msg in websocket: 
            return msg





# Generates an API signature.
# A signature is HMAC_SHA256(secret, verb + path + expires + data), hex encoded.
# Verb must be uppercased, url is relative, nonce must be an increasing 64-bit integer
# and the data, if present, must be JSON without whitespace between keys.
def generate_signature(apiSecret, verb, url, expires, postdict=None):
    """Given an API Secret key and data, create a BitMEX-compatible signature."""
    data = ''
    if postdict:
        # separators remove spaces from json
        # BitMEX expects signatures from JSON built without spaces
        data = json.dumps(postdict, separators=(',', ':'))
    parsedURL = urllib.parse.urlparse(url)
    path = parsedURL.path
    if parsedURL.query:
        path = path + '?' + parsedURL.query
    
    message = (verb + path + str(expires) + data).encode('utf-8')

    signature = hmac.new(apiSecret.encode('utf-8'), message, digestmod=hashlib.sha256).hexdigest()
    
    return signature