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
    def __init__(self, threshold):
        self._threshold = threshold
        #self._sell_amount = sell_price
        #self._buy_price
        self._token_analyst = None
        self._bitmex = None
        self._exchange_names = []
        self._init_stop = False
        
    def set_threshold(self, threshold):
        self._threshold = threshold

    def set_trade_amount(self, trade_amount):
        self._trade_amount = trade_amount

    def set_token_analyst(self, token_analyst):
        self._token_analyst = token_analyst

    def set_bitmex(self, bitmex):
        self._bitmex = bitmex

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

        if self._bitmex == None:
            return print(c[2] + "\nMust set an exchange before call to start" + c[0])

        ''' Connect to exhange websockets in future - Right now only Bitmex REST API
        asyncio.gather(self.connect_to_token_analyst(), self.connect_to_exchanges())
        '''
        await self._main_loop()


    async def _main_loop(self):
        """Inits connection to Token Analyst websocket stream, sends inflows to be analyzed, trades basiced off analysis and current positions."""
        async for data in self._token_analyst.connect():
            if(self._init_stop):
                await self._token_analyst.close()
                return
            if(data == None):
                continue
            # if data sent from token analyst is an Inflow and its in one of our exchanges dive deeper
            elif(data['flowType'] == 'Inflow' and data['to'][0] == 'Bitmex'):
                result = await self.analyze_inflow_data(data)
                
                if not result:
                    continue
                
                hasPosition = await self.check_positions()

                if hasPosition:
                    # sell
                    self._bitmex.sell(1)
                else:
                    #short
                    self._bitmex.buy(1)
                


    async def analyze_inflow_data(self, data):
        """Analyzes if the inflow value is above threshold. Also sends data to exchange for calculating average inflow."""
        
        await self._bitmex.calc_inflow_average(data['value'])

        if(data['value'] > self._threshold):
            print(c[3] + f"\n{data['to']} Inflow above threshold - {self._threshold}. Value - {data['value']}" + c[0])
            return True
        else:
            return False  


    async def check_positions(self):
        positions = await self._bitmex.get_positions()
        if(positions[0]['isOpen']):
            return True
        else:
            return False
        


    #For now use http but in future this will connect to exchange websockets
    async def connect_to_exchanges(self):
        """Init connections to all exchanges."""
        for e in self._exchanges:
            await e.connect()   
    