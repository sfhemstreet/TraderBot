import asyncio
import logging
import time
from threading import Thread

logging.basicConfig(filename="test.log", level=logging.DEBUG)

from BitMEX import BitMEX
from TokenAnalyst import TokenAnalyst
from Trade import Trade
from RateLimitTracker import RateLimitTracker
from config import *
from check_config import check_config
from colors import c


def main():

    # ---------- Your code here ---------- #
    async def trader_bot(data):
        """
        User trade function, fill in with trade logic.
        Recieves blockchain data from Token Analyst websocket.  
        """
        # use trade to make order objects 
            # ie -  my_order = trade.limit_buy(quantity, price)
        # use bitmex to submit orders - note that you must use await keyword 
            # ie -  order_info = await bitmex.place_order(my_order)
        # use token_analyst to check for inflow / outflow 
            # ie -  result = token_analyst.chech_for_inflow(data, threshold?, exchange?)

        
        # Example Code -
        #   in this example we will trigger a trade based on Inflows over a certain value.
        #   when we get data that is an Inflow and above our threshold, 
        #   we will check our positions on Bitmex and either sell our positions if we have any open
        #   or open a short position if we do not
        #---------------------------------------

        print(data)

        # set a threshold to watch for
        inflow_threshold = 0.0000001

        # check if data is an inflow
        # here we will supply a threshold to filter results to only those above our inflow_threshold 
        result = token_analyst.check_for_inflow(data=data, threshold=inflow_threshold, exchange='All')

        if result:
            # check if you are going to above the ratelimit before doing any trades
            # check method must be awaited because we might async sleep
            rate_limit.check(will_increment=False)

            # lets see if we have any positions open that we might want to sell
            position = bitmex.get_last_position()

            if position:
                position_qty = position['currentQty']

                if position_qty > 0:

                    # lets sell a little below the market price, 
                    # note that price must be integer or .5, otherwise you will get a tickSize error 
                    price = int(position['markPrice'] - 1)

                    # make an order
                    sell_order = trade.limit_sell(quantity=position_qty, price=price)

                    # send to bitmex, 
                    # we get back the order details that we can use to ammend/cancel/track the order
                    order_details = await bitmex.place_order(sell_order)

                    # keep track of rate limit
                    rate_limit.increment()
                    return
                
            last_price = bitmex.get_last_trade_price()

            if last_price:
                # important! make sure price is integer or .5, otherwise you will get a tickSize error  
                short_price = int(last_price - 100)
                short_order = trade.limit_sell(quantity=10, price=short_price)
                short_order_details = await bitmex.place_order(short_order)
                # keep track of rate limit
                rate_limit.increment()

        


    # End trader_bot 
    # ------------------------------------ #


    logging.debug(f"---- New Start ----")

    # check config gets API keys 
    TOKEN_ANALYST_API_KEY, BITMEX_API_KEY, BITMEX_API_SECRET = check_config()

    # init TokenAnalyst with api-key
    token_analyst = TokenAnalyst(TOKEN_ANALYST_API_KEY)

    # init BitMEX with api-key and secret (supply 'base_url' to do real trades, default is testnet url) 
    bitmex = BitMEX(key=BITMEX_API_KEY, secret=BITMEX_API_SECRET, symbol=G_DEFAULT_BITMEX_SYMBOL, base_url=G_DEFAULT_BITMEX_BASE_URL, ws_url=G_DEFAULT_BITMEX_WS_URL )

    # init Trade with symbol
    trade = Trade(symbol=G_DEFAULT_BITMEX_SYMBOL)

    # keep track of trades per minute to avoid rate limit
    rate_limit = RateLimitTracker()

    # create asyncio event loop
    loop = asyncio.get_event_loop() 

    # Websocket loop for streaming Token Analyst data 
    # sends data to trader_bot 
    async def token_analyst_ws_loop():
        """Recieves websocket data from Token Analyst and sends data to traderBot."""
        async for data in token_analyst.connect():
            if(data == None):
                continue
            else:
                await trader_bot(data)
          
    # Websocket Loop for streaming Bitmex data
    async def bitmex_ws_loop():
        """Connect to bitmex websocket to get updates on market and user data."""
        await bitmex.connect()

    try:
        # Create tasks for both websockets 
        loop.create_task(bitmex_ws_loop())
        loop.create_task(token_analyst_ws_loop())
        # RUN 
        loop.run_forever()
    finally:
        loop.stop() 
    

async def do_this_after_delay(delay, do_this):
    '''Executes function 'do_this' after non-block sleeping the 'delay' time.'''
    await asyncio.sleep(delay)
    await do_this()


if __name__ == "__main__":
    main()

