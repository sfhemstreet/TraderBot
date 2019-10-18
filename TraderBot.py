import asyncio
import os
import json
import sys

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

    async def start_stream(self):
        if self._token_analyst == None:
            return print("\nMust set token_analyst before call to start_stream.\n")


        async for data in self._token_analyst.connect():
            print(data)

    async def stop_stream(self):
        if self._token_analyst == None:
            return print("\nThere is no stream... must set_token_analyst and run start_stream to use stop_stream.\n")
        await self._token_analyst.close()
       
    async def interpret(self, data):
        print(data)


