import asyncio
import os
import TraderBot
import BitMEX
import TokenAnalyst

# export API keys in the environment variables, using $ export API_KEY='...'
TOKEN_ANALYST_API_KEY = os.environ['TOKEN_ANALYST_API_KEY']
BITMEX_API_KEY = os.environ['BITMEX_API_KEY']
BITMEX_API_SECRET = os.environ['BITMEX_API_SECRET']

# set Inflow threshold and amount for each trade 
THRESHOLD = 666 
AMOUNT = 0.000000001 

async def main():

    # create a TraderBot with threshold, amount
    bot = TraderBot.TraderBot(THRESHOLD, AMOUNT)

    # create TokenAnalyst with api key
    ta = TokenAnalyst.TokenAnalyst(TOKEN_ANALYST_API_KEY)

    # create BitMEX with key and secret
    bm = BitMEX.BitMEX(BITMEX_API_KEY, BITMEX_API_SECRET)

    # set token_analyst in bot 
    bot.set_token_analyst(ta)

    # set bitmex in bot
    #bot.set_bitmex(bm)

    # start stream 
    await bot.start_stream()
    
    await bot.stop_stream()



asyncio.run(main())


