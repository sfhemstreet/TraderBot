import asyncio
import os
import signal

import TraderBot
import BitMEX
import TokenAnalyst
import shutdown


# export API keys in the environment variables, using $ export API_KEY='...'
TOKEN_ANALYST_API_KEY = os.environ['TOKEN_ANALYST_API_KEY']
BITMEX_API_KEY = os.environ['BITMEX_API_KEY']
BITMEX_API_SECRET = os.environ['BITMEX_API_SECRET']

# set Inflow threshold and amount for each trade 
THRESHOLD = 50 
AMOUNT = 0.000000001 

def main():

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

    # create event loop
    loop = asyncio.get_event_loop() 

    # May want to catch other signals too
    signals = (signal.SIGHUP, signal.SIGTERM, signal.SIGINT)
    for s in signals:
        loop.add_signal_handler(s, lambda s=s: asyncio.create_task(shutdown(s, loop, bot)))
   


    # The keyboard interupt no longer works because of code above
    # Work on gracefully stopping websocket connections 
    try:
        #start stream
        loop.create_task(bot.start_stream())
        loop.run_forever()
    finally:
        # again, work on graceful exit
        loop.close() 



if __name__ == "__main__":
    main()


