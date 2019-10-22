import asyncio
import os
import json
import sys
import copy

# ANSI colors
c = (
    "\033[0m",   # End of color
    "\033[36m",  # Cyan
    "\033[91m",  # Red
    "\033[35m",  # Magenta
)

class TraderBot:
    def __init__(self, threshold, trade_amount):
        self._threshold = threshold
        self._trade_amount = trade_amount
        self._token_analyst = None
        self._exchanges = []
        self._exchange_names = []
        self._init_stop = False
        
    def set_threshold(self, threshold):
        self._threshold = threshold

    def set_trade_amount(self, trade_amount):
        self._trade_amount = trade_amount

    def set_token_analyst(self, token_analyst):
        self._token_analyst = token_analyst

    def set_exchanges(self, exchanges):
        self._exchanges = copy.deepcopy(exchanges)
        for e in exchanges:
            self._exchange_names.append(e.name)

    def get_threshold(self):
        return self._threshold


    async def stop(self):
        """Turns off all connections to TraderBot."""
        if self._token_analyst == None:
            return print(c[2] + "\nThere is no stream... must set_token_analyst and run start_stream to use stop_stream." + c[0])
        self._init_stop = True
    
    
    async def start(self):
        """Tells Token Analyst to start streaming websocket, which yields inflow data."""

        if self._token_analyst == None:
            return print(c[2] + "\nMust set token_analyst before call to start" + c[0])

        if len(self._exchanges) < 1:
            return print(c[2] + "\nMust set an exchange before call to start" + c[0])

        ''' Connect to exhange websockets in future - Right now only Bitmex REST API
        asyncio.gather(self.connect_to_token_analyst(), self.connect_to_exchanges())
        '''
        # 
        await self.token_analyst_stream()


    async def token_analyst_stream(self):
        """Inits connection to Token Analyst websocket stream and send inflows to be analyzed."""
        async for data in self._token_analyst.connect():
            if(self._init_stop):
                await self._token_analyst.close()
                return
            if(data == None):
                continue
            # if data sent from token analyst is an Inflow and its in one of our exchanges dive deeper
            elif(data['flowType'] == 'Inflow' and data['to'][0] in self._exchange_names):
                await self.analyze_inflow_data(data)
                continue


    async def analyze_inflow_data(self, data):
        """Analyzes if the inflow value is above threshold. Also sends data to exchange for calculating average inflow."""
        
        await self._exchanges[self._exchange_names.index(str(data['to'][0]))].calc_inflow_average(data['value'])

        if(data['value'] > self._threshold):
            print(c[3] + f"\n{data['to']} Inflow above threshold - {self._threshold}. Value - {data['value']}" + c[0])
            await self.check_orders(data)
            

    async def check_orders(self, data):
        orders = await self._exchanges[self._exchange_names.index(str(data['to'][0]))].get_orders()
        if(orders):
            # You have trades open, sell if long
            orderID = await self._exchanges[self._exchange_names.index(str(data['to'][0]))].sell(1,self._trade_amount)
            print(orderID)
        else:
            # No trades open, open short 
            orderID = await self._exchanges[self._exchange_names.index(str(data['to'][0]))].buy(1,self._trade_amount)
            print(orderID)

    #For now use http but in future this will connect to exchange websockets
    async def connect_to_exchanges(self):
        """Init connections to all exchanges."""
        for e in self._exchanges:
            await e.connect()   
    