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

# ws_url is set to testnet, change to make real trades 
WS_URL = "wss://testnet.bitmex.com"
WS_VERB = "GET"
WS_ENDPOINT = "/realtime"


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
        self._order_IDs = []
        self.retries = 0 
        # user / trade data
        self.wallet_data = None
        self.position_data = None
        self.margin_data = None
        self.order_data = None
        self.trade_data = None
        self.execution_data = None


    async def calc_inflow_average(self, new_value):
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
    async def get_position_data(self):
        """Get position data and return it as an object organized into closed and open positions."""
        pos_data = {
            'closed': [],
            'open': []
        }
        for p in self.position_data:
            if p['isOpen'] == False:
                pos_data['closed'].append(p)
            else:
                pos_data['open'].append(p)
        
        return pos_data
        

    async def get_wallet_amount(self):
        """Returns amount available in wallet."""
        return self.wallet_data[0]['amount']


    async def get_margin_data(self):
        """Returns last stroed margin data."""
        return self.margin_data[0]


    async def get_order_data(self):
        # NOT IN USE YET
        print("ORD")
        print(self.order_data)


    async def get_trading_price(self):
        """Return price from last trade stored from websocket."""
        return self.trade_data[0]['price']


    # WEBSOCKETS
    # Following code is for websocket connection - 
    async def connect(self):
        """Connects to Bitmex websocket."""
        EXPIRES = int(round(time.time()) + 100)
        uri = WS_URL + WS_ENDPOINT
        signature = bitmex_helpers.generate_signature(self._secret, WS_VERB, WS_ENDPOINT, EXPIRES)
        id = "bitMEX_stream"
        payload = {"op": "authKeyExpires", "args": [self._key, EXPIRES, signature]}
        async with websockets.connect(uri) as websocket:
            self._ws = websocket
            await websocket.send(json.dumps(payload))
            async for msg in websocket: 
                msg_type = await self.interpret_msg_type(json.loads(msg),id)
                if msg_type == 'INFO':
                    pass
                elif msg_type == 'SUCCESS':
                    await self.get_all_info() 
                elif msg_type == 'ERROR':
                    raise Exception(c[2] + "\nERROR CONNECTING TO BITMEX WEBSOCKET" + c[0])
                    return


    async def get_all_info(self):
        """Gets position, margin, order, wallet, and trade data via websocket."""
        args = ["position","margin","wallet","order","trade:XBTUSD","execution"]
        await self.ws_subscribe(args)
       

    async def ws_subscribe(self, args):
        """Subscribes to data on bitmex websocket. Takes in array of args for what to subscribe to."""
        payload = {"op": "subscribe", "args": args}
        id = "bitMEX_stream"
        await self._ws.send(json.dumps(payload))
        async for msg in self._ws:
            msg_type = await self.interpret_msg_type(json.loads(msg),id)
            if msg_type == 'INFO':
                pass
            elif msg_type == 'SUCCESS':
                pass
            elif msg_type == 'ERROR':
                raise Exception(c[2] + "\nERROR SUBSCRIBING TO BITMEX WEBSOCKET" + c[0])
            elif msg_type == 'TABLE':
                await self.store_table_info(msg)

    
    async def interpret_msg_type(self, response, id):
        """Gets response from websocket and returns type of response, ie table, info, success, error."""
        if 'info' in response:
            print(c[1] + f"\n{response['info']} Limit : {response['limit']}" + c[0]) 
            return 'INFO'
        elif 'success' in response:
            if 'subscribe' in response:
                print(c[1] + f"\nBitMEX websocket successfully subscribed to {response['subscribe']}" + c[0])
            return 'SUCCESS'
        elif 'error' in response:
            print(c[2] + f"\n{response}" + c[0])
            return 'ERROR'
        elif 'table' in response:
            return 'TABLE'
        

    async def store_table_info(self, raw_data):
        """Stores bitmex table data on Position, Wallet, Margin, Order, and Trade."""
        data = json.loads(raw_data)
        if(data['table'] == 'position'):
            if(data['data']):
                self.position_data = data['data']

        elif(data['table'] == 'wallet'):
            self.wallet_data = data['data']

        elif(data['table'] == 'margin'):
            if(data['data']):
                self.margin_data = data['data']

        elif(data['table'] == 'order'):
            if(data['data']):
                self.order_data = data['data']

        elif(data['table'] == 'trade'):
            if(data['data']):
                self.trade_data = data['data']

        elif(data['table'] == 'execution'):
            if(data['data']):
                self.execution_data = data['data']



    # REST API 
    async def make_order(self, quantity, price=None, side=None, orderType=None, displayQty=None, stopPx=None, pegOffsetValue=None, pegPriceType=None, timeInForce=None, execInst=None):
        """
            Returns an order object ready to use in bulk or single order. 
            Must supply quantity. 
            If no price supplied, order is market sell or buy.
            side is either 'Buy' or 'Sell'
            displayQty of 0 hides order
            stopPx, optional trigger price, use a price below the current price for stop-sell orders and buy-if-touched orders
        """
        if price and price < 0:
            raise Exception(c[2] + "Order Price must be positive." + c[0])

        if not quantity:
            raise Exception(c[2] + "Must supply order quantity." + c[0])

        if side and side != 'Sell' and side != 'Buy':
            raise Exception(c[2] + "Side must be 'Sell' or 'Buy'." + c[0])

        if orderType and (
            orderType != 'Market' or
            orderType != 'Limit' or
            orderType != 'Stop' or 
            orderType != 'StopLimit' or
            orderType != 'MarketIfTouched' or
            orderType != 'LimitIfTouched' or
            orderType != 'Pegged'
        ):
            raise Exception(c[2] + "orderType must be Market, Limit, Stop, StopLimit, MarketIfTouched, LimitIfTouched, or Pegged" + c[0])

        if displayQty and displayQty < 0:
            raise Exception(c[2] + "DisplayQty is negative, must be 0 to hide order or positive." + c[0])
        
        if pegPriceType and (
            pegPriceType != 'LastPeg' or 
            pegPriceType != 'MidPricePeg' or 
            pegPriceType != 'MarketPeg' or 
            pegPriceType != 'PrimaryPeg' or 
            pegPriceType != 'TrailingStopPeg'
        ):
            raise Exception(c[2] + "pegPriceType must be LastPeg, MidPricePeg, MarketPeg, PrimaryPeg, or TrailingStopPeg." + c[0])

        if timeInForce and (
            timeInForce != 'Day' or 
            timeInForce != 'GoodTillCancel' or 
            timeInForce != 'ImmediateOrCancel' or 
            timeInForce != 'FillOrKill'
        ):
            raise Exception(c[2] + "timeInForce must be Day, GoodTillCancel, ImmediateOrCancel, or FillOrKill" + c[0])
        
        if execInst and (
            execInst != 'ParticipateDoNotInitiate' or 
            execInst != 'AllOrNone' or 
            execInst != 'MarkPrice' or 
            execInst != 'IndexPrice' or 
            execInst != 'LastPrice' or 
            execInst != 'Close' or 
            execInst != 'ReduceOnly' or 
            execInst != 'Fixed'
        ):
            raise Exception(c[2] + "execInst must be ParticipateDoNotInitiate, AllOrNone, MarkPrice, IndexPrice, LastPrice, Close, ReduceOnly, or Fixed." + c[0])
        
        if execInst and execInst == 'AllOrNone' and displayQty != 0:
            raise Exception(c[2] + "execInst is 'AllOrNone', displayQty must be 0" + c[0])

        # Generate a unique clOrdID with our prefix so we can identify it.
        clOrdID = self._orderIDPrefix + base64.b64encode(uuid.uuid4().bytes).decode('utf8').rstrip('=\n')
        order = {
            'symbol': self.symbol,
            'orderQty': quantity,
            'clOrdID': clOrdID,
            'side': side
        }
        # add to order if supplied 
        if price:           order['price'] = price
        if displayQty:      order['displayQty'] = displayQty
        if stopPx:          order['stopPx'] = stopPx
        if pegOffsetValue:  order['pegOffsetValue'] = pegOffsetValue
        if timeInForce:     order['timeInForce'] = timeInForce
        if execInst:        order['execInst'] = execInst
        if orderType:       order['ordType'] = orderType

        return order


    async def market_buy(self, quantity):
        '''
        Buy at market price. 
        Returns order object. ID: orderID
        '''
        side="Buy"
        order = await self.make_order(
            quantity=quantity, 
            side=side, 
        )
        return await self.place_order(order)


    async def market_sell(self, quantity):
        '''
        Sell at market price.
        Returns order object. ID: orderID
        '''
        side="Sell"
        order = await self.make_order(
            quantity=quantity, 
            side=side, 
        )
        return await self.place_order(order)
    

    async def limit_buy(self, quantity, price):
        '''Place a limit buy order.
        Returns order object ID: orderID
        '''
        side = "Buy"
        order = await self.make_order(
            quantity=quantity, 
            price=price,
            side=side, 
        )
        return await self.place_order(order)

    
    async def short(self, quantity, price):
        """Place a short order.
        Returns order object. ID: orderID
        """
        side="Sell"
        order = await self.make_order(
            quantity=quantity, 
            price=price,
            side=side, 
        )
        return await self.place_order(order)


    async def stop_order(self, quantity, stopPx, price=None, execInst=None):
        '''Place stop order.
        Use a price below the current price for stop-sell orders and buy-if-touched orders. 
        Use execInst of 'MarkPrice' or 'LastPrice' to define the current price used for triggering.
        '''
        order = await self.make_order(
            quantity=quantity, 
            stopPx=stopPx,
            price=price,
            execInst=execInst
        )
        return await self.place_order(order)

    
    async def close(self, quantity=None, side=None):
        '''
        cancel other active limit orders with the same side and symbol if the open quantity exceeds the current position.
        Side or quantity required.

        '''
        if quantity == None and side == None:
            raise Exception(c[2] + "Side or quantity required to close." + c[0])

        clOrdID = self._orderIDPrefix + base64.b64encode(uuid.uuid4().bytes).decode('utf8').rstrip('=\n')
        order = {
            'symbol': self.symbol,
            'clOrdID': clOrdID,
            'execInst': 'Close'
        }
        if quantity: order['orderQty'] = quantity,
        if side: order['side'] = side

        return await self.place_order(order)


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

    
    
