import websockets
import json
import asyncio
import hashlib
import hmac
import time
import urllib.parse
import requests
import datetime
import base64
import uuid
import logging
import bitmex_helpers
from collections import deque


# ANSI colors
c = (
    "\033[0m",   # End of color
    "\033[36m",  # Cyan
    "\033[91m",  # Red
    "\033[35m",  # Magenta
)

class BitMEX:
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


    def calc_inflow_average(self, new_value):
        """Calculates running average from token analys inflow 
        data and prints the running average for every x inflows."""
        # set x to how many data points you want to average before it is printed
        x = 20
        self._inflow_count = self._inflow_count + 1
        self._inflow_total = self._inflow_total + new_value
        self._inflow_average = self._inflow_total / self._inflow_count
        
        if(self._inflow_count % x == 0):
            print(c[1] + f"\nCurrent inflow average is {round(self._inflow_average,4)}" + c[0])


    # getters for Bitmex Data stored from websocket stream
    def get_positions(self):
        """Returns all position data."""
        return self.position_data

    
    def get_latest_position(self):
        """Returns latest position data or None."""
        if self.position_data:
            return self.position_data[-1]
        return None


    def get_wallet_amount(self):
        """Returns amount available in Bitmex wallet or None."""
        if self.wallet_data:
            return self.wallet_data['amount']
        return None


    def get_latest_margin_data(self):
        """Returns latest margin data or None."""
        if self.margin_data:
            return self.margin_data[-1]
        return None


    def get_latest_order_data(self):
        """Returns latest order data or None."""
        if self.order_data:
            return self.order_data[-1]
        return None


    def get_last_trade_price(self):
        """Returns price from last trade on Bitmex or None."""
        if self.trade_data:
            return self.trade_data[-1]['price']
        return None

    
    # WEBSOCKETS
    # Following code is for websocket connection - 
    async def connect(self):
        """Connects to Bitmex websocket."""
       
        WS_VERB = "GET"
        WS_ENDPOINT = "/realtime"
        EXPIRES = int(round(time.time()) + 100)
        uri = str(self._ws_url + WS_ENDPOINT)
        signature = bitmex_helpers.generate_signature(self._secret, WS_VERB, WS_ENDPOINT, EXPIRES)
        id = "bitMEX_stream"
        payload = {"op": "authKeyExpires", "args": [self._key, EXPIRES, signature]}

        async with websockets.connect(uri, ping_timeout=None) as websocket:
            self._ws = websocket
            await websocket.send(json.dumps(payload))
            async for raw_msg in websocket: 
                msg_type = await self.interpret_msg_type(json.loads(raw_msg),id)
                if msg_type == 'INFO':
                    pass
                elif msg_type == 'SUCCESS':
                    args = await self.get_all_info() 
                    await self.ws_subscribe(args)
                elif msg_type == 'ERROR':
                    raise Exception(c[2] + "\nERROR CONNECTING TO BITMEX WEBSOCKET" + c[0])
                    return
         

    async def get_all_info(self):
        """Returns websocket args to subscribe to position, margin, order, wallet, and trade."""
        trade = "trade:" + self.symbol
        args = ["position","margin","wallet","order",str(trade), "execution"]
        return args 
       

    async def ws_subscribe(self, args):
        """Subscribes to data on bitmex websocket. Takes in array of args for what to subscribe to."""
        payload = {"op": "subscribe", "args": args}
        id = "bitMEX_stream"
        await self._ws.send(json.dumps(payload))
        async for raw_msg in self._ws:
            msg_type = await self.interpret_msg_type(json.loads(raw_msg),id)
            if msg_type == 'INFO':
                pass
            elif msg_type == 'SUCCESS':
                pass
            elif msg_type == 'ERROR':
                raise Exception(c[2] + "\nERROR SUBSCRIBING TO BITMEX WEBSOCKET" + c[0])
            elif msg_type == 'TABLE':
                await self.store_table_info(json.loads(raw_msg))
            
    
    async def interpret_msg_type(self, response, id):
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
        

    async def store_table_info(self, data):
        """Stores bitmex table data on Position, Wallet, Margin, Order, execution, and Trade."""
        #print('storing-', data)
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
   
    
    # REST API 
    async def place_order(self, order):
        '''
            Send single order. 
            return order ID
        '''
        endpoint = "order"
        return await self._http_request(path=endpoint, postdict=order, verb="POST")


    async def place_bulk_order(self, orders):
        """Place a bulk order via REST API."""
        if len(orders) < 1:
            raise Exception(c[2] + "Orders must be more than 1 order." + c[0])

        endpoint = "order/bulk"
        allOrders = {'orders': orders}
        return await self._http_request(path=endpoint, postdict=allOrders, verb="POST")
        

    async def cancel_order(self, orderID):
        """Cancel an existing order by submitting order ID."""
        path = "order"
        postdict = {
            'orderID': orderID,
        }
        return await self._http_request(path=path, postdict=postdict, verb="DELETE")


    async def _http_request(self, path, query=None, postdict=None, timeout=None, verb=None, rethrow_errors=False, max_retries=None):
        """Send a request to BitMEX Servers."""
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
        auth = bitmex_helpers.BitmexHeaders(self._key, self._secret)

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
                self.cancel([o['orderID'] for o in self.get_orders()])

                logging.error("Your ratelimit will reset at %s. Sleeping for %d seconds." % (reset_str, to_sleep))
                asyncio.sleep(to_sleep)

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


    ''' REST API requests. Not needed with use of websockets 
     async def get_orders_rest(self):
        """Get open orders via REST API http."""
        path = "order"
        orders = await self._http_request(
            path=path,
            query={
                'filter': json.dumps({'ordStatus.isTerminated': False, 'symbol': self.symbol}),
                'count': 500
            },
            verb="GET"
        )
        # Only return orders that start with our clOrdID prefix.
        return [o for o in orders if str(o['clOrdID']).startswith(self._orderIDPrefix)]


    async def get_orders(self):
        """Get orders via websocket."""
        arg = ["order"]
        self.ws_subscribe(arg)

    
    async def get_positions_rest(self):
        """Get current positions via REST API http."""
        path = "position"
        columns = ['lastPrice']
        positions = await self._http_request(
            path=path,
            verb="GET",
            query={
                'columns': ['unrealisedRoePcnt','timestamp',
                            'currentTimestamp','breakEvenPrice',
                            'markPrice','markValue','currentQty',
                            'avgEntryPrice','isOpen']
            }
        )
        return positions



    async def get_positions(self):
        """Get current positions via Websocket."""
        arg = ["position"]
        self.ws_subscribe(arg)



    async def get_stats_rest(self):
        "Get exchange statistics via REST API http."
        path = "stats"
        stats = await self._http_request(
            path=path,
            verb="GET"
        )
        return stats


    async def get_quote_rest(self):
        """Get best bid/offer snapshot via REST API http."""
        path = "quote"
        quote = await self._http_request(
            path=path,
            verb="GET",
            query={
                'symbol': 'XBT:nearest',
                'count': 1
            }
        )
        return quote


    async def get_quote(self):
        """Get top level of the book via websocket."""
        arg = ["quote"]
        self.ws_subscribe(arg)


    async def get_last_xbt_trade_rest(self):
        "Get last trade price of XBT via REST API http."
        path = "trade"
        trade = await self._http_request(
            path=path,
            query={
                'symbol':'XBT',
                'count': 1,
                'reverse': True
            }
        )
        return trade[0]
    '''

    
    
