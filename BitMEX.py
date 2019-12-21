import websockets
import json
import asyncio
import hashlib
import hmac
import time
import requests
import datetime
import base64
import uuid
import logging
import urllib
from colors import c
from collections import deque
from Exceptions import WebSocketError, InvalidArgError


class BitMEX:
    """
    Class for interactions with Bitmex.
    
    Connect to Bitmex websocket for position, margin, order, wallet, and trade data.

    Place, amend, and cancel orders on Bitmex exchange.

    Attributes:

    `key: str`
        Bitmex API key
    
    `secret: str`
        Bitmex API secret 
    
    `symbol: str`
        trade symbol
    
    `base_url: str` 
        base url for Bitmex REST API
    
    `ws_url: str`
        Bitmex websocket url
    
    `orderIDPrefex: str`
        prefex attached to order IDs
    
    `timeout: int`
        timeout time, default is 8

    Methods:

    `connect`
        connect to Bitmex websocket, subscribes to get position, margin, order, wallet, and trade data.

    `place_order`
        place an order on the Bitmex exchange

    `place_bulk_order`
        place a bulk order on the Bitmex exchange

    `cancel_order`
        cancel order

    `cancel_all_orders`
        cancels all orders, or of filtered orders

    `amend_order`
        amend an order 

    `amend_bulk_order`
        amend bulk order

    `update_leverage`
        update your leverage

    `isolated_margin`
        Enable isolated margin per-position.

    `cross_margin`
        Enable cross margin per-position.

    `transfer_margin`
        Transfer equity in or out of a position. 

    `risk_limit`
        Update your risk limit. 

    `get_positions`
        get your position data

    `get_last_position`
        get last position data

    `get_wallet_amount`
        get amount in wallet

    `get_last_margin_data`
        get last margin data

    `get_last_order_data`
        get last order data

    `get_last_trade_data`
        get last trade data

    `get_last_trade_price`
        get last trade price

    """
    def __init__(self, key, secret, symbol, base_url, ws_url, orderIDPrefex="traderbot_", timeout=8):
        self.name = "Bitmex"
        self._key = key
        self._secret = secret
        self.base_url = base_url
        self.symbol = symbol
        self._ws = None
        self._ws_url = ws_url
        self._inflow_average = 0
        self._inflow_total = 0
        self._inflow_count = 0
        self._session = requests.Session()
        #self._session.headers.update({'user-agent': 'trader-bot9000b'})
        self._session.headers.update({'content-type': 'application/json'})
        self._session.headers.update({'accept': 'application/json'})
        self.timeout = timeout
        self._orderIDPrefix = orderIDPrefex # cannot be longer than 13 chars long
        self._order_IDs = []
        self.retries = 0 
        # user / trade data
        self.wallet_data = None
        self.position_data = deque(maxlen=100)
        self.margin_data = deque(maxlen=100)
        self.order_data = deque(maxlen=100)
        self.trade_data = deque(maxlen=100)
        self.execution_data = deque(maxlen=100)


    # getters for Bitmex Data stored from websocket stream
    def get_position_data(self):
        """Returns all position data."""
        return self.position_data

    
    def get_last_position(self):
        """Returns latest position data or None."""
        if self.position_data:
            return self.position_data[-1]
        return None


    def get_wallet_data(self):
        """Returns all Bitmex wallet data."""
        return self.wallet_data


    def get_margin_data(self):
        """Returns margin data."""
        return self.margin_data


    def get_order_data(self):
        """Returns all order data."""
        return self.order_data
        

    def get_trade_data(self):
        """Returns all trade data."""
        return self.trade_data


    def get_last_trade_price(self):
        """Returns price from last trade on Bitmex or None."""
        if self.trade_data:
            return self.trade_data[-1]['price']
        return None

    
    def get_execution_data(self):
        """Returns all execution data."""
        return self.execution_data


    # REST API 
    async def place_order(self, order):
        '''
            Place an order on the bitmex exchange.

            async func - use await

            Parameters:
            
            `order: dict`
                order ( use Trade class to make orders )

            Returns:
            
            `orderInfo: json data`
                bitmex response
        '''
        endpoint = "order"
        return await self._http_request(path=endpoint, postdict=order, verb="POST")


    async def place_bulk_order(self, orders):
        """Place a bulk order on Bitmex exchange.

        async func - use await
        
        Parameters:

        `orders: array<dict>`
            array of orders ( use Trade class to make orders )

        Returns:
            
        `orderInfo: json data`
            bitmex response

        """
        if len(orders) < 1:
            raise InvalidArgError(orders, "Invalid bulk order number.")

        endpoint = "order/bulk"
        allOrders = {'orders': orders}
        return await self._http_request(path=endpoint, postdict=allOrders, verb="POST")
        

    async def cancel_order(self, orderID=None, clOrdID=None, text=None):
        """Cancel an existing order(s) by submitting orderID(s) or clOrdID(s). 
        
        Supply optional text to annotate cancellation.

        async func - use await
        
        Parameters:

        `orderID: str`
            orderID of order to cancel

        `clOrdID: str`
            clOrdID of order to cancel

        `text: str`
            annnotaion text

        Returns:

        `orderInfo: json data`
            bitmex response
        """
        if orderID == None and clOrdID == None:
            raise InvalidArgError([orderID, clOrdID], "Must submit either orderID or clOrdID to cancel order(s).")

        path = "order"
        postdict = {}
        if orderID:   postdict['orderID'] = orderID
        elif clOrdID: postdict['clOrdID'] = clOrdID
        if text:      postdict['text'] = text

        return await self._http_request(path=path, postdict=postdict, verb="DELETE")


    async def cancel_all_orders(self, symbol=None, cancel_filter=None, text=None):
        """
        Cancel all orders. 

        async func - use await

        Parameters:

        `symbol: str` 
            optional, if supplied only cancels order of that symbol.

        `cancel_filter: str`
             optional, optional filter for cancellation, use to only cancel some orders, e.g. {"side": "Buy"}

        `text`
            supply optional text to annotate cancellation.

        Returns:

        `orderInfo: json data`
            bitmex response

        """
        path = "order/all"
        postdict = {}
        if symbol:          postdict['symbol'] = symbol
        if cancel_filter:   postdict['filter'] = cancel_filter
        if text:            postdict['text']   = text

        if postdict: 
            return await self._http_request(path=path, postdict=postdict, verb="DELETE")
        else: 
            return await self._http_request(path=path, verb="DELETE")



    async def amend_order(
        self, 
        orderID=None, 
        origClOrdID=None, 
        clOrdID=None, 
        orderQty=None, 
        leavesQty=None, 
        price=None, 
        stopPx=None, 
        pegOffsetValue=None, 
        text=None
    ):
        """
        Amend the quantity or price of an open order.

        Send an orderID or origClOrdID to identify the order you wish to amend.

        Both order quantity and price can be amended. Only one qty field can be used to amend.

        Use the leavesQty field to specify how much of the order you wish to remain open. 
        This can be useful if you want to adjust your position's delta by a certain amount, regardless of how much of the order has already filled.
        A leavesQty can be used to make a "Filled" order live again, if it is received within 60 seconds of the fill.

        async func - use await

        Parameters:

        `orderID: str`
            order ID

        `origClOrdID: str`
            the orginal clOrdID

        `clOrdID: str`
            clOrdID for amend

        `orderQty: int`
            order quantity

        `leavesQty: int`
            how much of the order you wish to remain open
        
        `price: float`
            price to amend to, use valid tickSize, ie integer or .5

        `stopPx: float`
            stop to amend

        `pegOffsetValue: float`
            pegOffset Value

        `text: str`
            annotate amend for records

        Returns:

        `orderInfo: json data`
            bitmex response

        """
        if orderID == None and origClOrdID == None:
            raise InvalidArgError([orderID, origClOrdID], "Must submit either orderID or origClOrdID to amend order(s).")
        
        path = "order"
        postdict = {}

        if orderID:         postdict['orderID']         = orderID
        if origClOrdID:     postdict['origClOrdID']     = origClOrdID
        if clOrdID:         postdict['clOrdID']         = clOrdID
        if orderQty:        postdict['orderQty']        = orderQty
        if leavesQty:       postdict['leavesQty']       = leavesQty
        if price:           postdict['price']           = price
        if stopPx:          postdict['stopPx']          = stopPx
        if pegOffsetValue:  postdict['pegOffsetValue']  = pegOffsetValue
        if text:            postdict['text']            = text

        return await self._http_request(path=path, postdict=postdict, verb='PUT')


    async def amend_bulk_order(self, orders):
        """Amend multiple orders for the same symbol. 

        async func - use await
        
        Parameters:

        `orders: array<dict>`
            array of orders to amend

        Returns:

        `orderInfo: json data`
            bitmex response
        """

        path = "order/bulk"
        postdict = {
            'orders': orders
        }
        return await self._http_request(path=path, postdict=postdict, verb='PUT')


    async def update_leverage(self, leverage, symbol=None):
        """
        Choose leverage for a position. 

        async func - use await

        Parameters:

        `leverage: float` 
            a number between 0.01 and 100 to enable isolated margin with a fixed leverage. 
            0 to enable cross margin.

        `symbol: str` 
            default symbol used if not supplied.

        Returns:

        `orderInfo: json data`
            bitmex response
        """
        if symbol == None:
            symbol = self.symbol

        path = "position/leverage"
        postdict = {
            'symbol': symbol,
            'leverage': leverage
        }
        return await self._http_request(path=path, postdict=postdict, verb='POST')


    async def isolated_margin(self, symbol=None):
        """Enable isolated margin per-position. 

        async func - use await
        
        Parameters:

        `symbol: str`
            symbol, if not supplied, uses default.

        Returns:
        
        `orderInfo: json data`
            bitmex response
        
        """
        if symbol == None:
            symbol = self.symbol

        path = "position/isolate"
        postdict = {
            'symbol': symbol,
            'enabled': True
        }
        return await self._http_request(path=path, postdict=postdict, verb='POST')


    async def cross_margin(self, symbol=None):
        """Enable cross margin per-position. 

        async func - use await
        
        Parameters:

        `symbol: str`
            symbol, if not supplied, uses default.

        Returns:
        
        `orderInfo: json data`
            bitmex response
        
        """

        if symbol == None:
            symbol = self.symbol

        path = "position/isolate"
        postdict = {
            'symbol': symbol,
            'enabled': False
        }
        return await self._http_request(path=path, postdict=postdict, verb='POST')


    async def transfer_margin(self, amount, symbol=None):
        """
        Transfer equity in or out of a position. 

        async func - use await

        Parameters:

        `amount: float` 
            Amount to transfer, in Satoshis, May be negative.

        `symbol: str`  
            Symbol of position to isolate, if no symbol supplied, uses default.

        Returns:
        
        `orderInfo: json data`
            bitmex response
        
        """
        if symbol == None:
            symbol = self.symbol
        
        path = "position/transferMargin"
        postdict = {
            'symbol': symbol,
            'amount': amount
        }
        return await self._http_request(path=path, postdict=postdict, verb='POST')


    async def risk_limit(self, riskLimit, symbol=None):
        """
        Update your risk limit. 

        async func - use await

        Parameters:

        `riskLimit: float` 
            New Risk Limit, in Satoshis

        `symbol: str`
            symbol, if not supplied, uses default.

        Returns:
        
        `orderInfo: json data`
            bitmex response
        
        """
        if symbol == None:
            symbol = self.symbol

        path = "position/riskLimit"
        postdict = {
            'symbol': symbol,
            'riskLimit': riskLimit
        }
        return await self._http_request(path=path, postdict=postdict, verb='POST')

    
    # ------------------ WEBSOCKETS -------------------
    async def connect(self):
        """
        Connect to Bitmex websocket to recieve and store position, margin, order, wallet, and trade data. 
        
        async func - use await
        """

        WS_VERB = "GET"
        WS_ENDPOINT = "/realtime"
        EXPIRES = int(round(time.time()) + 100)
        uri = str(self._ws_url + WS_ENDPOINT)
        # we need to generate a signiture to connect, see bitmex docs for more info on this
        signature = generate_signature(self._secret, WS_VERB, WS_ENDPOINT, EXPIRES)
        id = "bitMEX_stream"

        payload = {
            "op": "authKeyExpires",
            "args": [
                self._key, 
                EXPIRES, 
                signature
            ]
        }

        # connect to websocket with no timeout time
        async with websockets.connect(uri, ping_timeout=None) as websocket:
            self._ws = websocket
            await websocket.send(json.dumps(payload))

            # check data in the init response from websocket
            async for raw_msg in websocket: 
                msg_type = await self._interpret_msg_type(json.loads(raw_msg),id)
                if msg_type == 'INFO':
                    pass
                elif msg_type == 'SUCCESS':
                    # we are connected, subscribe to channels we want
                    args = await self._get_all_info() 
                    await self._ws_subscribe(args)
                elif msg_type == 'ERROR':
                    raise WebSocketError(json.loads(raw_msg),"ERROR CONNECTING TO BITMEX WEBSOCKET")
                    return
         

    async def _get_all_info(self):
        """Returns websocket args to subscribe to position, margin, order, wallet, and trade."""
        trade = "trade:" + self.symbol

        # to filter results 

        args = [
            "position",
            "margin",
            "wallet",
            "order",
            str(trade),
            "execution"]

        return args 
       

    async def _ws_subscribe(self, args):
        """Subscribes to data on bitmex websocket. Takes in array of args for what to subscribe to."""
        
        id = "bitMEX_stream"
        payload = {
            "op": "subscribe",
            "args": args
        }

        # send our subscribe args 
        await self._ws.send(json.dumps(payload))
        # look at responses back, and store table data 
        async for raw_msg in self._ws:
            msg_type = await self._interpret_msg_type(json.loads(raw_msg),id)
            if msg_type == 'INFO':
                pass
            elif msg_type == 'SUCCESS':
                pass
            elif msg_type == 'ERROR':
                raise WebSocketError(json.loads(raw_msg),"ERROR SUBSCRIBING TO BITMEX WEBSOCKET")
            elif msg_type == 'TABLE':
                await self._store_table_info(json.loads(raw_msg))
            
    
    async def _interpret_msg_type(self, response, id):
        """Gets response from websocket and returns type of response, ie table, info, success, error."""
        if 'info' in response:
            print(c[1] + f"\n{response['info']} Limit : {response['limit']}" + c[0]) 
            return 'INFO'
        elif 'success' in response:
            if 'subscribe' in response:
                print(c[1] + f"\nBitMEX websocket successfully subscribed to {response['subscribe']}" + c[0])
                return 'SUCCESS'
            return 'SUCCESS'
        elif 'error' in response:
            print(c[2] + f"\n{response}" + c[0])
            return 'ERROR'
        elif 'table' in response:
            return 'TABLE'
        

    async def _store_table_info(self, data):
        """Stores bitmex table data on Position, Wallet, Margin, Order, execution, and Trade."""
        
        if(data['table'] == 'position'):
            if(data['data']):
                self.position_data.append(data['data'][0])

        elif(data['table'] == 'wallet'):
            self.wallet_data = data['data'][0]

        elif(data['table'] == 'margin'):
            if(data['data']):
                self.margin_data.append(data['data'][0])

        elif(data['table'] == 'order'):
            if(data['data']):
                self.order_data.append(data['data'][0])

        elif(data['table'] == 'trade'):
            if(data['data']):
                self.trade_data.append(data['data'][0])

        elif(data['table'] == 'execution'):
            if(data['data']):
                self.execution_data.append(data['data'][0])
   

    async def _http_request(self, path, query=None, postdict=None, timeout=None, verb=None, rethrow_errors=False, max_retries=None):
        """Send a request to BitMEX Servers. Returns json response."""
        # Handle URL
        url = self.base_url + path

        if timeout is None:
            timeout = self.timeout

        # Default to POST if data is attached, GET otherwise
        if not verb:
            verb = 'POST' if postdict else 'GET'

        # don't retry POST or PUT. 
        if max_retries is None:
            max_retries = 0 if verb in ['POST', 'PUT'] else 3

        # Create auth header for request
        auth = BitmexHeaders(self._key, self._secret)

        def exit_or_throw(e):
            if rethrow_errors:
                raise e
            else:
                exit(1)

        async def retry():
            self.retries += 1
            if self.retries > max_retries:
                raise Exception("Max retries on %s (%s) hit, raising." % (path, json.dumps(postdict or '')))
            return await self._http_request(path, query, postdict, timeout, verb, rethrow_errors, max_retries)

        # Make the request
        response = None
        try:
            logging.info("sending req to %s: %s" % (url, json.dumps(postdict or query or '')))
            req = requests.Request(method=verb, url=url, json=postdict, auth=auth, params=query)
            prepped = self._session.prepare_request(req)
            # send
            response = self._session.send(prepped, timeout=timeout)
            # Make non-200s throw
            response.raise_for_status()

        except requests.exceptions.HTTPError as e:
            if response is None:
                raise e

            # 401 - Auth error. This is fatal.
            if response.status_code == 401:
                logging.error("API Key or Secret incorrect, please check and restart.")
                logging.error("Error: " + response.text)
                if postdict:
                    logging.error(postdict)
                # Always exit, even if rethrow_errors, because this is fatal
                exit(1)

            # 404, can be thrown if order canceled or does not exist.
            elif response.status_code == 404:
                if verb == 'DELETE':
                    logging.error("Order not found: %s" % postdict['orderID'])
                    return
                logging.error("Unable to contact the BitMEX API (404). " +
                                  "Request: %s \n %s" % (url, json.dumps(postdict)))
                exit_or_throw(e)

            # 429, ratelimit; cancel orders & wait until X-RateLimit-Reset
            elif response.status_code == 429:
                logging.error("Ratelimited on current request. Sleeping, then trying again. Try fewer " +
                                  "order pairs or contact support@bitmex.com to raise your limits. " +
                                  "Request: %s \n %s" % (url, json.dumps(postdict)))

                # Figure out how long we need to wait.
                ratelimit_reset = response.headers['X-RateLimit-Reset']
                to_sleep = int(ratelimit_reset) - int(time.time())
                reset_str = datetime.datetime.fromtimestamp(int(ratelimit_reset)).strftime('%X')

                # We're ratelimited, and we may be waiting for a long time. Cancel orders.
                logging.warning("Canceling all known orders in the meantime.")
                self.cancel_all_orders(text="RateLimited Cancel")

                logging.error("Your ratelimit will reset at %s. Sleeping for %d seconds." % (reset_str, to_sleep))
                await asyncio.sleep(to_sleep)

                # Retry the request.
                return await retry()

            # 503 - BitMEX temporary downtime, likely due to a deploy. Try again
            elif response.status_code == 503:
                logging.warning("Unable to contact the BitMEX API (503), retrying. " +
                                    "Request: %s \n %s" % (url, json.dumps(postdict)))
                asyncio.sleep(3)
                return await retry()

            elif response.status_code == 400:
                error = response.json()['error']
                message = error['message'].lower() if error else ''

                # Duplicate clOrdID: that's fine, probably a deploy, go get the order(s) and return it
                if 'duplicate clordid' in message:
                    orders = postdict['orders'] if 'orders' in postdict else postdict

                    IDs = json.dumps({'clOrdID': [order['clOrdID'] for order in orders]})
                    orderResults = await self._http_request('/order', query={'filter': IDs}, verb='GET')

                    for i, order in enumerate(orderResults):
                        if (
                                order['orderQty'] != abs(postdict['orderQty']) or
                                order['side'] != ('Buy' if postdict['orderQty'] > 0 else 'Sell') or
                                order['price'] != postdict['price'] or
                                order['symbol'] != postdict['symbol']):
                            raise Exception('Attempted to recover from duplicate clOrdID, but order returned from API ' +
                                            'did not match POST.\nPOST data: %s\nReturned order: %s' % (
                                                json.dumps(orders[i]), json.dumps(order)))
                    # All good
                    return orderResults

                elif 'insufficient available balance' in message:
                    logging.error('Account out of funds. The message: %s' % error['message'])
                    exit_or_throw(Exception('Insufficient Funds'))


            # If we haven't returned or re-raised yet, we get here.
            logging.error("Unhandled Error: %s: %s" % (e, response.text))
            logging.error("Endpoint was: %s %s: %s" % (verb, path, json.dumps(postdict)))
            exit_or_throw(e)

        except requests.exceptions.Timeout as e:
            # Timeout, re-run this request
            logging.warning("Timed out on request: %s (%s), retrying..." % (path, json.dumps(postdict or '')))
            return await retry()

        except requests.exceptions.ConnectionError as e:
            logging.warning("Unable to contact the BitMEX API (%s). Please check the URL. Retrying. " +
                                "Request: %s %s \n %s" % (e, url, json.dumps(postdict)))
            asyncio.sleep(1)
            return await retry()

        # Reset retry counter on success
        self.retries = 0

        return response.json()


"""Taken from BitMEX market maker."""
# Generates an API signature.
# A signature is HMAC_SHA256(secret, verb + path + expires + data), hex encoded.
# Verb must be uppercased, url is relative, expires must be an increasing 64-bit integer
# and the data, if present, must be JSON without whitespace between keys.
def generate_signature(secret, verb, url, nonce, data=''):
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