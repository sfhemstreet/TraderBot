import websockets
import os
import json
import asyncio



async def interpret(response, id):
    if(response['id'] == id and response['event'] == "data"):
        await on_data(response['data'])
    if(response['id'] == None and response['event'] == "heartbeat"):
        await on_heartbeat(response['data'])
    if(response['id'] == id and response['event'] == "subscribed" and response['data']['success'] == True):
        await on_subscribed(response['data'])

async def subscribe(key):
    uri = "wss://ws.tokenanalyst.io"
    id = "ta_0"
    channel = "exchange_flows"
    payload = {"event":"subscribe","channel":channel,"id":id,"key":key}
    async with websockets.connect(uri) as websocket:
        await websocket.send(json.dumps(payload))
        async for msg in websocket: 
            await interpret(json.loads(msg), id)

async def on_data(data): 
    if(data['flowType'] == 'Inflow'):
        print("Received data: " + str(data))

async def on_heartbeat(heartbeat):
    print("Received heartbeat: " + str(heartbeat)) 

async def on_subscribed(details):
    print("Successfully subscribed: " + str(details))

