import asyncio
import os
import ta_connect
import bitmex_connect

# export API keys in the environment variables, using $ export API_KEY='...'
TOKEN_ANALYST_API_KEY = os.environ['TOKEN_ANALYST_API_KEY']
BITMEX_API_KEY = os.environ['BITMEX_API_KEY']
BITMEX_API_SECRET = os.environ['BITMEX_API_SECRET']


async def ta_bitmex_connect_both():
    """ Connect to TokenAnalyst WebSocket and BitMEX WebSocket. """
    ta = ta_connect.subscribe(TOKEN_ANALYST_API_KEY)
    bm = bitmex_connect.subscribe(BITMEX_API_KEY, BITMEX_API_SECRET)
    
    await asyncio.gather(ta,bm)

asyncio.run(ta_bitmex_connect_both())

