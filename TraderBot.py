import asyncio
import logging

logging.basicConfig(filename="test.log", level=logging.DEBUG)

from BitMEX import BitMEX
from TokenAnalyst import TokenAnalyst
from check_config import check_config
from colors import c

           
def main():
    logging.debug(f"---- New Start ----")

    TOKEN_ANALYST_API_KEY, BITMEX_API_KEY, BITMEX_API_SECRET, TRADE_QUANTITY, PORTFOLIO_PERCENTAGE, INFLOW_THRESHOLD = check_config()

    # create asyncio event loop
    loop = asyncio.get_event_loop() 

    # init TokenAnalyst with api-key
    token = TokenAnalyst(TOKEN_ANALYST_API_KEY)

    # init BitMEX with api-key and secret (supply 'base_url' to do real trades, default is testnet url) 
    bitmex = BitMEX(key=BITMEX_API_KEY, secret=BITMEX_API_SECRET)

    # Websocket loop for streaming Token Analyst Inflow data and executing trades
    async def token_analyst_ws_loop():
        """Recv inflow data from Token Analyst websocket."""
        async for data in token.connect():
            if(data == None):
                continue
            else:
                await check_for_inflow(data)
          

    # Websocket Loop for streaming Bitmex data
    async def bitmex_ws_loop():
        """Connect to bitmex websocket to get updates on market and user data."""
        await bitmex.connect()


    async def check_for_inflow(data):
        """Check if data is an Inflow event to our exchange, 
        Collect average inflow, and see if Inflow is above threshold."""

        if(data['flowType'] == 'Inflow' and data['to'][0] == 'Bitmex'):
            # collect running average Inflow 
            await bitmex.calc_inflow_average(data['value'])
            
            print(data)

            # check if Inflow is above threshold
            if(data['value'] > INFLOW_THRESHOLD):
                logging.debug(f"{data['to']} Inflow above threshold - {INFLOW_THRESHOLD}. Value - {data['value']}")
                print(c[3] + f"\n{data['to']} Inflow above threshold - {INFLOW_THRESHOLD}. Value - {data['value']}" + c[0])
                # start trade 
                await init_trade()


    async def init_trade():
        """Starts trade procedure by checking wallet, 
        positions, and trading price."""

        logging.debug('Init Trade')

        # get current positions, wallet amount, and trading price on Bitmex 
        positions = await bitmex.get_position_data()
        wallet_amount = await bitmex.get_wallet_amount()
        trading_price = await bitmex.get_trading_price()
        
        # calc trade amount based on percentage of portfolio available to trade
        trade_amount = PORTFOLIO_PERCENTAGE * wallet_amount

        # if we have positions open we want to sell / open a short position
        # if we dont have any positions open, just open a short position
        if positions['open'] and positions['open'][0]['currentQty'] > 0:
            # sell and short

            logging.debug('Sell positions and open short')

            quantity = positions['open'][0]['currentQty']
            lim = await create_limit_order(quantity, trading_price)
            shor = await create_short(trading_price, trade_amount)
            await bitmex.bulk_order([lim, shor])
        else:
            # short

            logging.debug('No positions, Open short')

            my_short = await create_short(trading_price, trade_amount)
            await bitmex.short(my_short['quantity'], my_short['price'])


    async def create_limit_order(quantity, trading_price):
        """Calculate limit price and return object with 'quantity' 'price' and 'side'."""
        # smaller difference makes trades execute faster
        difference = 0.2
        limit_price = trading_price - difference

        logging.debug(f"Creating limit order. Quanitity - {quantity}, Price - {limit_price}")
        print(c[3] + f"\nCreating limit order.\nQuanitity - {quantity}, Price - {limit_price}\n" + c[0])

        return {'quantity':quantity, 'price':limit_price, 'side': 'Sell'}
        

    async def create_short(trading_price, amount):
        """Calculate short amount and return object with 'quantity' 'price' and 'side'."""
        quantity = TRADE_QUANTITY
        short_price = trading_price - 200

        logging.debug(f"Opening short. Quanitity - {quantity}, Price - {short_price}")
        print(c[3] + f"\nOpening short.\nQuanitity - {quantity}, Price - {short_price}\n" + c[0])

        return {'quantity': quantity, 'price': short_price, 'side': 'Sell'} 
    

    try:
        # Create tasks for both websockets 
        loop.create_task(bitmex_ws_loop())
        loop.create_task(token_analyst_ws_loop())
        # RUN 
        loop.run_forever()
    finally:
        loop.close() 
    '''

async def do_this_after_delay(delay, do_this):
    '''Executes function 'do_this' after non-block sleeping the 'delay' time.'''
    await asyncio.sleep(delay)
    await do_this()


if __name__ == "__main__":
    main()