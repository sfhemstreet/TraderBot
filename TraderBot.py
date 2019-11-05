import asyncio
import os

from BitMEX import BitMEX
from TokenAnalyst import TokenAnalyst

# export API keys in the environment variables, using $ export KEY_NAME='...'
TOKEN_ANALYST_API_KEY = os.environ['TOKEN_ANALYST_API_KEY']
BITMEX_API_KEY =        os.environ['BITMEX_API_KEY']
BITMEX_API_SECRET =     os.environ['BITMEX_API_SECRET']

# set Inflow threshold to base trades off of (float > 0)
G_THRESHOLD = None

# set percentage of portfolio (bitmex wallet) available to with trade (float > 0 and < 1)
G_PORTFOLIO_PERCENTAGE = None

# color output :P
c = (
    "\033[0m",   # End of color
    "\033[36m",  # Cyan
    "\033[91m",  # Red
    "\033[35m",  # Magenta
)

            
def main():
    # create asyncio event loop
    loop = asyncio.get_event_loop() 

    # init TokenAnalyst with api-key
    token = TokenAnalyst(TOKEN_ANALYST_API_KEY)

    # init BitMEX with api-key and secret (supply 'base_url' to do real trades, default is testnet url) 
    bitmex = BitMEX(key=BITMEX_API_KEY, secret=BITMEX_API_SECRET)

    
    # User Input Only If G_THRESHOLD / G_PORTFOLIO_PERCENTAGE Aren't Filled In 
    #----------------------------------------------------------------------
    # get user input to set THRESHOLD if not declared globally (float > 0)
    if G_THRESHOLD == None:
        THRESHOLD = float(input(c[3] + 
        '''\nEnter Token Analyst INFLOW value threshold.\n~ Must be a number greater than 0 ~
        \n>>> ''' + c[0]))
    else:
        THRESHOLD = G_THRESHOLD
        
    if THRESHOLD <= 0:
        raise Exception(c[2] + "\nTHRESHOLD MUST BE ABOVE 0\n" + c[0])

    # get user input to set percentage of portfolio available 
    # to trade with if not declared globally (float > 0 and < 1)
    if G_PORTFOLIO_PERCENTAGE == None:
        PORTFOLIO_PERCENTAGE = float(input(c[3] + 
        '''\nEnter percentage of portfolio available to trade with.\n~ Must be a number greater than 0 and less than 1 ~
        \n>>> ''' + c[0]))
    else:
        PORTFOLIO_PERCENTAGE = G_PORTFOLIO_PERCENTAGE
        
    if PORTFOLIO_PERCENTAGE <= 0 or PORTFOLIO_PERCENTAGE >= 1:
        raise Exception(c[2] + "\nPORTFOLIO PERCENTAGE MUST BE ABOVE 0 AND BELOW 1\n" + c[0])
    #-----------------------------------------------------------------------


    # WORK ON THIS
    async def stop_limit_order(quantity, trading_price):
        """Calculate limit price and send to bitmex to sell."""
        # if price drops 10 below the current trading price sell
        limit_price = trading_price + 10
        stop_price = trading_price - 10

        print(c[3] + f"\nStop limit order.\nQuanitity - {quantity}, Price - {limit_price}, Stop Price - {stop_price}\n" + c[0])

        await bitmex.sell(quantity=quantity, price=limit_price, stop_price=stop_price)


    # WORK ON THIS
    async def open_short(trading_price, amount):
        """Calculate short amount and send to bitmex to open short."""
        # This is wrong. Fix this. 
        # It is the amount you are willing to lose 
        # if the price goes up when betting that it will go down
        #stop_price = trading_price + amount
        quantity = 1
        # fix this too plz
        short_price = trading_price - 100

        print(c[3] + f"\nOpening short.\nQuanitity - {quantity}, Price - {short_price}\n" + c[0])

        await bitmex.short(quantity=quantity, price=short_price) # , stop_price=stop_price)
    

    # WORK ON THIS
    async def init_trade():
        """Starts trade procedure by checking wallet, 
        positions, and trading price."""
        # get current positions, wallet amount, and trading price on Bitmex 
        positions = await bitmex.get_position_data()
        wallet_amount = await bitmex.get_wallet_amount()
        trading_price = await bitmex.get_trading_price()

        # calc trade amount based on percentage of portfolio available to trade
        trade_amount = PORTFOLIO_PERCENTAGE * wallet_amount

        # if we have positions open we want to sell / open a short position
        # if we dont have any positions open, just open a short position
        if positions['open']:
            # sell and short
            quantity = len(positions['open'])
            await stop_limit_order(quantity, trading_price)
            await open_short(trading_price, trade_amount)
        else:
            # short
            await open_short(trading_price, trade_amount)

        
    async def check_for_inflow(data):
        """Check if data is an Inflow event to our exchange, 
        Collect average inflow, and see if Inflow is above threshold."""

        if(data['flowType'] == 'Inflow' and data['to'][0] == 'Bitmex'):
            # collect running average Inflow 
            await bitmex.calc_inflow_average(data['value'])
            
            # check if Inflow is above threshold
            if(data['value'] > THRESHOLD):
                print(c[3] + f"\n{data['to']} Inflow above threshold - {THRESHOLD}. Value - {data['value']}" + c[0])
                # start trade 
                await init_trade()
                

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