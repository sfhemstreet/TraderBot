import websockets
import json
import asyncio
import hashlib
import hmac
import time
import urllib.parse

# used to create signature for auth connection 
BITMEX_URL = "wss://testnet.bitmex.com"
VERB = "GET"
ENDPOINT = "/realtime"
EXPIRES = int(round(time.time()) + 100)

async def interpret(response, id):
    if 'info' in response:
        print(response['info'], 'Limit :',response['limit'])
        return False
    elif 'success' in response:
        return True
    elif 'error' in response:
        print(response['error'])
        return False


async def live_feed(websocket):
    payload = {"op": "subscribe", "args": ["affiliate","execution","order","margin","position","privateNotifications","transact","wallet","trade"]}
    
    await websocket.send(json.dumps(payload))
    
    async for msg in websocket: 
        print(msg)


async def subscribe(key, secret):
    # default is testnet, change for real trades
    uri = "wss://testnet.bitmex.com/realtime"
    signature = generate_signature(secret, VERB, ENDPOINT, EXPIRES)
    id = "bm_0"
    payload = {"op": "authKeyExpires", "args": [key, EXPIRES, signature]}

    async with websockets.connect(uri) as websocket:
        await websocket.send(json.dumps(payload))
        async for msg in websocket: 
            result = await interpret(json.loads(msg), id)
            if result:
                await live_feed(websocket)
                


# Generates an API signature.
# A signature is HMAC_SHA256(secret, verb + path + nonce + data), hex encoded.
# Verb must be uppercased, url is relative, nonce must be an increasing 64-bit integer
# and the data, if present, must be JSON without whitespace between keys.
def generate_signature(apiSecret, verb, url, nonce, postdict=None):
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
    
    message = (verb + path + str(nonce) + data).encode('utf-8')

    signature = hmac.new(apiSecret.encode('utf-8'), message, digestmod=hashlib.sha256).hexdigest()
    
    return signature


