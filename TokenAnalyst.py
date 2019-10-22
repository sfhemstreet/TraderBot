import websockets
import os
import json
import asyncio
import sys


# ANSI colors
c = (
    "\033[0m",   # End of color
    "\033[36m",  # Cyan
    "\033[91m",  # Red
    "\033[35m",  # Magenta
)

class TokenAnalyst:
    def __init__(self, key):
        self._key = key
        self._ws = None

    async def connect(self):
        uri = "wss://ws.tokenanalyst.io"
        id = "token_analyst_stream"
        channel = "btc_unconfirmed_exchange_flows"
        payload = {"event":"subscribe","channel":channel,"id":id,"key":self._key}

        async with websockets.connect(uri) as websocket:
            self._ws = websocket
            await websocket.send(json.dumps(payload))
            async for msg in websocket: 
                data = await self.interpret(json.loads(msg), id)
                yield data 


    async def close(self):
        await self._ws.close()
        print(c[3] + '\nTokenAnalyst connection closed' + c[0])



    async def interpret(self, response, id):
        if(response['id'] == id and response['event'] == "data"):
            return await self.on_data(response['data'])
        if(response['id'] == None and response['event'] == "heartbeat"):
            return await self.on_heartbeat(response['data'])
        if(response['id'] == id and response['event'] == "subscribed" and response['data']['success'] == True):
            return await self.on_subscribed(response['data'])
        if(response['event'] == 'error' and response['data']['success'] == False):
            return await self.on_error(response['data'])
            

    async def on_data(self, data): 
        if(data['flowType'] == 'Inflow'):
            return data


    async def on_heartbeat(self, heartbeat):
        print(c[1] + "\nToken Analyst heartbeat - server time: " + str(heartbeat['serverTime']) + c[0]) 


    async def on_subscribed(self, details):
        print(c[1] + "\nToken Analyst connection successful. " + str(details['message']) + c[0])


    async def on_error(self, error):
        print(c[2] + "\nTokenAnalyst error - " + error['message'] + c[0])
        await self.close()
        sys.exit(1)

