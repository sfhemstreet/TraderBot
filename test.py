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
THRESHOLD = 100


def main():

    # create a TraderBot with threshold
    bot = TraderBot.TraderBot(THRESHOLD)

    # create TokenAnalyst with api key / create BitMEX with key and secret
    ta = TokenAnalyst.TokenAnalyst(TOKEN_ANALYST_API_KEY)
    bm = BitMEX.BitMEX(BITMEX_API_KEY, BITMEX_API_SECRET)

    # set token_analyst  
    bot.set_token_analyst(ta)

    # set bitmex exhange
    bot.set_bitmex(bm)
    
    # create event loop
    loop = asyncio.get_event_loop() 
    
    '''
    # Error Handling - work on this to cancel all trades, shutdown bot 
    # May want to catch other signals too
    signals = (signal.SIGHUP, signal.SIGTERM, signal.SIGINT)
    for s in signals:
        loop.add_signal_handler(s, lambda s=s: asyncio.create_task(shutdown(s, loop, bot)))
    '''

    try:
        loop.create_task(bot.start())
        # to stop bot after running for set time uncomment following 2 lines 
        #stop_time = 200000
        #loop.create_task(do_this_after_delay(stop_time, bot.stop))
        loop.run_forever()
    finally:
        loop.close() 


async def do_this_after_delay(delay, do_this):
    '''Executes function 'do_this' after non-block sleeping the 'delay' time.'''
    await asyncio.sleep(delay)
    await do_this()


if __name__ == "__main__":
    main()


