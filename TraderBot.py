import asyncio
import logging

logging.basicConfig(filename="test.log", level=logging.DEBUG)

from BitMEX import BitMEX
from TokenAnalyst import TokenAnalyst
import trade
from check_config import check_config
from colors import c

def main():

    # ---------- Your code here ---------- #
    async def trader_bot(data):
        """
        Recieves blockchain data from Token Analyst websocket 
        """
        
        # Example Code -
        #   in this example we will trigger a trade based on Inflows over a certain value.
        #   when we get data that is an Inflow and above our threshold, 
        #   we will check our positions on Bitmex and either sell our positions if we have any open
        #   or open a short position if we do not
        #---------------------------------------

        inflow_threshold = 100

        # using token_analyst method 'check_for_inflow_value'
        # check if data is an inflow
        # here we will supply a threshold to filter results to only those above our inflow_threshold 
        result = token_analyst.check_for_inflow_value(data=data, threshold=inflow_threshold)

        if result:
            # the data is an Inflow and is above our threshold 
            # lets see if we have any positions open that we might want to sell
            open_positions_qty = bitmex.get_open_positions_qty()

            # lets also get the last trade price
            last_price = bitmex.get_last_trading_price()

            # check if we have any open positions
            # if we do lets use limit sell to sell when the price goes a little below current market 
            # if we dont have any positions open lets open a short position with the same function
            if open_positions_qty > 0:

                # lets sell a little below the last trading price 
                price = last_price - 1

                # make an order
                sell_order = trade.limit_sell(quantity=open_positions_qty, price=price)

                # send to bitmex, 
                # we get back the order details that we can use to ammend/cancel/keep tarck of the order
                order_details = bitmex.place_order(sell_order)

            else:
                short_price = last_price - 100
                short_order = trade.limit_sell(quantity=10, price=short_price)
                short_order_details = bitmex.place_order(short_order)

        
        # right now getting some funky results from bitmex websocket
        # probably has to do with changes on their end, (ie symbol / index changes, websocket response changes)
        # gonna wait a little a see if they fix there stuff 


    # End trader_bot 
    # ------------------------------------ #


    logging.debug(f"---- New Start ----")

    # check config gets API keys 
    TOKEN_ANALYST_API_KEY, BITMEX_API_KEY, BITMEX_API_SECRET = check_config()

    # init TokenAnalyst with api-key
    token_analyst = TokenAnalyst(TOKEN_ANALYST_API_KEY)

    # init BitMEX with api-key and secret (supply 'base_url' to do real trades, default is testnet url) 
    bitmex = BitMEX(key=BITMEX_API_KEY, secret=BITMEX_API_SECRET)

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
        loop.close() 
    

async def do_this_after_delay(delay, do_this):
    '''Executes function 'do_this' after non-block sleeping the 'delay' time.'''
    await asyncio.sleep(delay)
    await do_this()


if __name__ == "__main__":
    main()

