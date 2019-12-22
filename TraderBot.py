import asyncio
import logging
import time
from threading import Thread

logging.basicConfig(filename="debug.log", level=logging.DEBUG)

from BitMEX import BitMEX
from TokenAnalyst import TokenAnalyst
from Trade import Trade
from RateLimitTracker import RateLimitTracker
from config import check_config
from colors import c
from order_logger import order_logger


def main():

    # ---------- Your code here ---------- #
    async def trader_bot(data):
        """
        User trade function, fill in with trade logic.

        Recieves blockchain data from Token Analyst websocket.  

        
        """
        
        last_trade_price = bitmex.get_last_trade_price()

        outflow_threshold = 1000
        outflow_result = token_analyst.check_for_outflow(data=data, threshold=outflow_threshold)

        if outflow_result:
            rate_limit.check()
            
            price = int(last_trade_price - 100)
            my_order = trade.limit_buy(quantity=10, price=price)
            order_reponse = await bitmex.place_order(order=my_order)
            
            my_orders.append(order_reponse)
            order_logger.info("outflow trade - %s - response - %s" % (my_order, order_reponse))


    # ----------------- end trader_bot ------------------- #


    logging.debug("---------------- New Start -------------------")
    order_logger.info("---------------- New Start -------------------")

    (
        TOKEN_ANALYST_API_KEY, 
        BITMEX_API_KEY, 
        BITMEX_API_SECRET, 
        DEFAULT_BITMEX_SYMBOL, 
        BITMEX_BASE_URL, 
        BITMEX_WS_URL
    ) = check_config()

    token_analyst = TokenAnalyst(key=TOKEN_ANALYST_API_KEY)

    bitmex = BitMEX(
        key=BITMEX_API_KEY, 
        secret=BITMEX_API_SECRET, 
        symbol=DEFAULT_BITMEX_SYMBOL, 
        base_url=BITMEX_BASE_URL, 
        ws_url=BITMEX_WS_URL 
    )

    trade = Trade(
        symbol=DEFAULT_BITMEX_SYMBOL,
        orderIDPrefex="traderbot_"
    )

    rate_limit = RateLimitTracker(
        limit=30, 
        timeframe=60
    )

    my_orders = []


    # Below creates an event loop and 2 main tasks, 
    # reading the Bitmex and Token Analyst websockets.
    #
    # Connecting to Bitmex gets us updates on
    # position, margin, order, wallet, execution and trade data.
    #
    # Connecting to the Token Analyst websocket 
    # yields us on-chain data we can use to make trades.
    # When that data is recieved it is sent to the 
    # trader_bot function above for us to act on. 

    loop = asyncio.get_event_loop() 

    async def token_analyst_ws_loop():
        """
        Connects to Token Analyst websocket, 
        recieves on-chain data and sends data to trader_bot.
        
        """
        async for data in token_analyst.connect(channel="btc_confirmed_exchange_flows"):
            if(data == None):
                continue
            else:
                await trader_bot(data)

        
    async def bitmex_ws_loop():
        """
        Connects to bitmex websocket to get updates on 
        position, margin, order, wallet, and trade data.
        
        """
        await bitmex.connect()
        

    try: 
        loop.create_task(bitmex_ws_loop())
        loop.create_task(token_analyst_ws_loop())
        
        loop.run_forever()
    finally:
        loop.stop() 


if __name__ == "__main__":
    main()
