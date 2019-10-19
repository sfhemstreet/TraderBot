import asyncio
import os
import json
import sys

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
        
    def set_threshold(self, threshold):
        self._threshold = threshold

    def set_trade_amount(self, trade_amount):
        self._trade_amount = trade_amount

    def set_token_analyst(self, token_analyst):
        self._token_analyst = token_analyst

    def get_threshold(self):
        return self._threshold

    async def start_stream(self):
        if self._token_analyst == None:
            return print(c[2] + "\nMust set token_analyst before call to start_stream.\n" + c[0])

        async for data in self._token_analyst.connect():
            if(data == None):
                continue
            elif(data['flowType'] == 'Inflow' and data['value'] > self.get_threshold()):
                print(c[3] + "\nInflow above threshold.\n" + str(data['value']) + c[0])

    async def stop_stream(self):
        if self._token_analyst == None:
            return print(c[2] + "\nThere is no stream... must set_token_analyst and run start_stream to use stop_stream.\n" + c[0])
        await self._token_analyst.close()
       
    async def interpret(self, data):
        print(data)


