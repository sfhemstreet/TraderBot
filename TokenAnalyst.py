import websockets
import os
import json
import asyncio
import sys
from Exceptions import WebSocketError


# ANSI colors
c = (
    "\033[0m",   # End of color
    "\033[36m",  # Cyan
    "\033[91m",  # Red
    "\033[35m",  # Magenta
)

class TokenAnalyst:
    """Connects to Token Analyst websocket and yields Inflow data thru the connect method."""
    def __init__(self, key):
        self._key = key
        self._ws = None


    async def connect(self, channel="btc_confirmed_exchange_flows"):
        """Connects to websocket and yields blockchain data. Default channel is 'btc_confirmed_exchange_flows'"""
        uri = "wss://ws.tokenanalyst.io"
        id = "token_analyst_stream"
        payload = {"event":"subscribe","channel":channel,"id":id,"key":self._key}

        async with websockets.connect(uri, ping_timeout=None) as websocket:
            self._ws = websocket
            await websocket.send(json.dumps(payload))
            async for msg in websocket: 
                data = await self.interpret(json.loads(msg), id)
                yield data 


    async def close(self):
        """ Close Token Anaylst websocket"""
        await self._ws.close()
        print(c[3] + '\nTokenAnalyst connection closed' + c[0])


    async def interpret(self, response, id):
        """Interpret data to check for heartbeat, connection success / errors, and Inflow."""
        if(response['id'] == id and response['event'] == "data"):
            return await self.on_data(response['data'])
        if(response['id'] == None and response['event'] == "heartbeat"):
            return await self.on_heartbeat(response['data'])
        if(response['id'] == id and response['event'] == "subscribed" and response['data']['success'] == True):
            return await self.on_subscribed(response['data'])
        if(response['event'] == 'error' and response['data']['success'] == False):
            return await self.on_error(response['data'])
        return None
            

    async def on_data(self, data): 
        return data


    async def on_heartbeat(self, heartbeat):
        print(c[1] + "\nToken Analyst heartbeat - server time: " + str(heartbeat['serverTime']) + c[0]) 
        return None


    async def on_subscribed(self, details):
        print(c[1] + "\nToken Analyst connection successful. " + str(details['message']) + c[0])
        return None


    async def on_error(self, error):
        raise WebSocketError(error, error['message'])
        print(c[2] + "\nTokenAnalyst error - " + error['message'] + c[0])
        await self.close()
        sys.exit(1)


    def check_for_inflow(self, data, threshold=None, exchange='Bitmex'):
        """
        Checks Token Analyst data for Inflow.
        Returns -1 or the inflow value.
        Supply 'threshold' value to filter results to those above threshold.
        Supply 'exchange' value to filter by exchange, default is Bitmex. 
        (Valid exchange values are All, Binance, Bitmex, Bitfinex, Bittrex, Kraken, Poloniex, and Huobi)
        """
        value = self._inflow_outflow_check(data=data, threshold=threshold, exchange=exchange, check_flowtype='Inflow')
        return value

    
    def check_for_outflow(self, data, threshold=None, exchange='Bitmex'):
        """
        Checks Token Analyst data for Outflow.
        Returns 0 or the outflow value.
        Supply 'threshold' value to filter results to those above threshold.
        Supply 'exchange' value to filter by exchange, default is Bitmex. 
        (Valid exchange values are All, Binance, Bitmex, Bitfinex, Bittrex, Kraken, Poloniex, and Huobi)
        """
        value = self._inflow_outflow_check(data=data, threshold=threshold, exchange=exchange, check_flowtype='Outflow')
        return value


    def _inflow_outflow_check(self, data, check_flowtype, threshold, exchange):
        '''used for check_for_outflow_value() and check_for_inflow_value()'''
        flowType = data['flowType']
        value = data['value']
        to = data['to']

        if flowType != check_flowtype:
            return 0

        if threshold and value < threshold:
            return 0

        if exchange != 'All' and exchange != to:
            return 0

        return value



    def get_transactionId(self, data):
        """Returns transaction ID from given Token Analyst websocket data."""
        transactionId = data['transactionId']
        return transactionId


    def get_blockHash(self, data):
        """Returns block hash from given Token Analyst websocket data."""
        blockHash = data['blockHash']
        return blockHash


    def get_blockNumber(self, data):
        """Returns block number from given Token Analyst websocket data."""
        blockNumber = data['blockNumber']
        return blockNumber


    def get_timestamp(self, data):
        """Returns timestamp from given Token Analyst websocket data."""
        timestamp = data['timestamp']
        return timestamp


    def get_from(self, data):
        """Returns 'from' from given Token Analyst websocket data."""
        from_data = data['from'][0]
        return from_data


    def get_to(self, data):
        """Returns exchange the Token Analyst websocket data is to."""
        to = data['to'][0]
        return to


    def get_value(self, data):
        """Returns value from given Token Analyst websocket data."""
        value = data['value']
        return value


    def get_flowtype(self, data):
        """Returns the flowtype of the given Token Analyst websocket data, either 'Inflow' or 'Outflow'."""
        flowType = data['flowType']
        return flowType