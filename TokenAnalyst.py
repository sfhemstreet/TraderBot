import websockets
import os
import json
import asyncio
import sys
from Exceptions import WebSocketError
from colors import c


class TokenAnalyst:
    """
    Handler for Token Analyst websocket connection and data yeilded from connection.
    
    Attributes:
    
    `key: str`
        Token Analyst API key

    Methods:

    `connect`
        connect to Token Ananlyst websocket

    `close`
        close websocket connection

    `check_for_inflow`
        check websocket data for inflow value

    `check_for_outflow`
        check websocket data for outflow value

    `get_value`
        get value from websocket data

    `get_to`
        get 'to' from websocket data

    `get_from`
        get 'from' from websocket data

    `get_flowtype`
        get flowtype from websocket data

    `get_blockhash`
        get blockhash from websocket data

    `get_blockNumber`
        get blocknumber from websocket data

    `get_transactionId`
        get transactionId from websocket data

    `get_timestamp`
        get timestamp from websocket data
    
    """
    def __init__(self, key):
        self._key = key
        self._ws = None


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


    def check_for_inflow(self, data, threshold=None, exchange='Bitmex'):
        """
        Checks Token Analyst data for Inflow.

        Parameters:

        `data: Token Analyst data`
            data from Token Analyst websocket
        
        `threshold: float` 
            value to filter results to those above threshold.

        `exchange: str` 
            value to filter by exchange, default is Bitmex. 
            (Valid exchange values are All, Binance, Bitmex, Bitfinex, Bittrex, Kraken, Poloniex, and Huobi)

        Returns:

        `value: float` 
            Value of inflow. 0 if not an inflow or below threshold
        """

        value = self._inflow_outflow_check(data=data, threshold=threshold, exchange=exchange, check_flowtype='Inflow')
        return value

    
    def check_for_outflow(self, data, threshold=None, exchange='Bitmex'):
        """
        Checks Token Analyst data for Outflow.

        Parameters:

        `data: Token Analyst data`
            data from Token Analyst websocket
        
        `threshold: float` 
            value to filter results to those above threshold.

        `exchange: str` 
            value to filter by exchange, default is Bitmex. 
            (Valid exchange values are All, Binance, Bitmex, Bitfinex, Bittrex, Kraken, Poloniex, and Huobi)

        Returns:

        `value: float` 
            Value of outflow. 0 if not an outflow or below threshold
        """
        value = self._inflow_outflow_check(data=data, threshold=threshold, exchange=exchange, check_flowtype='Outflow')
        return value


    async def connect(self, channel="btc_confirmed_exchange_flows"):
        """
        Connects to Token Analyst websocket, and yields on-chain data.

        async func - use await

        Parameters:

        `channel: str`
            websocket channel to subscribe to

        Yields:

        `data: json object` 
            see Token Analyst API docs for details 

        """

        uri = "wss://ws.tokenanalyst.io"
        id = "token_analyst_stream"
        payload = {
            "event":"subscribe",
            "channel":channel,
            "id":id,
            "key":self._key
        }

        # connect to websocket with no ping timeout - longer connection
        async with websockets.connect(uri, ping_timeout=None) as websocket:
            self._ws = websocket
            await websocket.send(json.dumps(payload))
            async for msg in websocket: 
                # check msg for data, returns None or on-chain data
                data = await self._interpret(json.loads(msg), id)
                yield data 


    async def close(self):
        """Close Token Anaylst websocket. 
        
        async func - use await."""
        
        await self._ws.close()
        print(c[3] + '\nTokenAnalyst connection closed' + c[0])


    async def _interpret(self, response, id):
        """check for heartbeat, connection success / errors, and Data."""

        if(response['id'] == id and response['event'] == "data"):
            return await self._on_data(response['data'])
        if(response['id'] == None and response['event'] == "heartbeat"):
            return await self._on_heartbeat(response['data'])
        if(response['id'] == id and response['event'] == "subscribed" and response['data']['success'] == True):
            return await self._on_subscribed(response['data'])
        if(response['event'] == 'error' and response['data']['success'] == False):
            return await self._on_error(response['data'])
        return None
            

    async def _on_data(self, data): 
        """Returns on-chain data."""

        return data


    async def _on_heartbeat(self, heartbeat):
        """Prints that we got a heartbeat from Token Analyst along with servertime."""

        print(c[1] + "\nToken Analyst heartbeat - server time: " + str(heartbeat['serverTime']) + c[0]) 
        return None


    async def _on_subscribed(self, details):
        """Prints that we have successfully subscribed to a given channel."""

        print(c[1] + "\nToken Analyst connection successful. " + str(details['message']) + c[0])
        return None


    async def _on_error(self, error):
        """Raises error, prints that websocket has had an error, and aborts."""

        raise WebSocketError(error, error['message'])
        print(c[2] + "\nTokenAnalyst error - " + error['message'] + c[0])
        await self.close()
        sys.exit(1)


    def _inflow_outflow_check(self, data, check_flowtype, threshold, exchange):
        '''used for check_for_outflow_value() and check_for_inflow_value()'''
        
        flowType = data['flowType']
        value = data['value']
        to = data['to']

        if flowType != check_flowtype:
            return 0

        if threshold and value < threshold:
            return 0

        if exchange != 'All' and exchange not in to:
            return 0

        return value

