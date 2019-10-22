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


# ANSI colors
c = (
    "\033[0m",   # End of color
    "\033[36m",  # Cyan
    "\033[91m",  # Red
    "\033[35m",  # Magenta
)


class BitMEX:
    def __init__(self, key, secret, symbol="XBTUSD", orderIDPrefex="mm_bitmex_", base_url="https://testnet.bitmex.com/api/v1/", timeout=8):
        self.name = "Bitmex"
        self._key = key
        self._secret = secret
        self.base_url = base_url
        self.symbol = symbol
        self._ws = None
        self._inflow_average = 0
        self._inflow_total = 0
        self._inflow_count = 0
        self._session = requests.Session()
        #self._session.headers.update({'user-agent': 'trader-bot9000b'})
        self._session.headers.update({'content-type': 'application/json'})
        self._session.headers.update({'accept': 'application/json'})
        self.timeout = timeout
        self._orderIDPrefix = orderIDPrefex # cannot be longer than 13 chars long
        self.retries = 0 

    async def calc_inflow_average(self, new_value):
        """Calculates running average from token analys inflow data and prints the running average for every x inflows."""
        # set x to how many data points you want to average before it is printed
        x = 20
        self._inflow_count = self._inflow_count + 1
        self._inflow_total = self._inflow_total + new_value
        self._inflow_average = self._inflow_total / self._inflow_count
        
        if(self._inflow_count % x == 0):
            print(c[1] + f"\nCurrent inflow average is {round(self._inflow_average,4)}" + c[0])

        return


    # Code below is taken from BitMEX Market Maker and modified to fit this project
    async def place_order(self, quantity, price):
        """Place an order."""
        if price < 0:
            raise Exception("Price must be positive.")

        endpoint = "order"
        # Generate a unique clOrdID with our prefix so we can identify it.
        clOrdID = self._orderIDPrefix + base64.b64encode(uuid.uuid4().bytes).decode('utf8').rstrip('=\n')
        postdict = {
            'symbol': self.symbol,
            'orderQty': quantity,
            'price': price,
            'clOrdID': clOrdID
        }
        return await self._http_request(path=endpoint, postdict=postdict, verb="POST")


    async def buy(self, quantity, price):
        """Place a buy order.
        Returns order object. ID: orderID
        """
        return await self.place_order(quantity, price)

    
    async def sell(self, quantity, price):
        """Place a sell order.
        Returns order object. ID: orderID
        """
        return await self.place_order(-quantity, price)


    async def get_orders(self):
        """Get open orders via HTTP."""
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


    async def cancel(self, orderID):
        """Cancel an existing order."""
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
            print("req --------- ", req)
            prepped = self._session.prepare_request(req)
            print("prepped-----------",prepped)
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
                return retry()

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

    '''
    # Following code is for websocket connection - 
    async def connect(self):
        # used to create signature for auth connection 
        # default URL is testnet, change URL for real trading
        WS_URL = "wss://testnet.bitmex.com"
        WS_VERB = "GET"
        WS_ENDPOINT = "/realtime"
        EXPIRES = int(round(time.time()) + 100)
        uri = URL + ENDPOINT
        signature = bitmex_helpers.generate_signature(self._secret, VERB, ENDPOINT, EXPIRES)
        id = "bitMEX_stream"
        payload = {"op": "authKeyExpires", "args": [self._key, EXPIRES, signature]}
        async with websockets.connect(uri) as websocket:
            self._ws = websocket
            await websocket.send(json.dumps(payload))
            async for msg in websocket: 
                await self.interpret(json.loads(msg), id)
            return
       
    async def exchange_user_data(self):
        payload = {"op": "subscribe", "args": ["order","margin","position","wallet"]}
        id = "bitMEX_stream"
        await self._ws.send(json.dumps(payload))
        async for msg in self._ws:
            await self.interpret(json.loads(msg),id)
        return

    async def interpret(self, response, id):
        if 'info' in response:
            print(c[1] + f"\n{response['info']} Limit : {response['limit']}" + c[0])
            return 
        elif 'success' in response:
            print()
            return 
        elif 'error' in response:
            print(response['error'])
            return 
        elif 'table' in response:
            await self.get_table_info(response)
            return
        else:
            return


    async def get_table_info(self, data):
        """Prints bitrmex user table data on Position, Wallet, Margin, and Order."""
        if(data['table'] == 'position'):
            if(data['data']):
                print(c[3] + "\nBitMEX positions - " + c[0])
                for d in data['data']:
                    print(d)
                print(c[3] + "- - - - - - - - - - - - - " + c[0])
            else:
                print(c[3] + "\nBitMEX positions - No open positions." + c[0])
            return
        elif(data['table'] == 'wallet'):
            print(c[3] + f"\nBitMEX wallet amount - {data['data'][0]['amount']}" + c[0])
            return
        elif(data['table'] == 'margin'):
            print(c[3] + f"\nBitMEX session margin - {data['data'][0]['sessionMargin']}" + c[0])
            return
        elif(data['table'] == 'order'):
            if(data['data']):
                print(c[3] + "\nBitMEX orders - " + c[0])
                for d in data['data']:
                    print(d)
                print(c[3] + "- - - - - - - - - - - - - " + c[0])
            else:
                print(c[3] + "\nBitMEX orders - No orders." + c[0])
            return
        else:
            return
    '''


