import asyncio
import os

from BitMEX import BitMEX

BITMEX_API_KEY =    os.environ['BITMEX_API_KEY']
BITMEX_API_SECRET = os.environ['BITMEX_API_SECRET']


# color output :P
c = (
    "\033[0m",   # End of color
    "\033[36m",  # Cyan
    "\033[91m",  # Red
    "\033[35m",  # Magenta
)


def main():

    loop = asyncio.get_event_loop()
    bitmex = BitMEX(key=BITMEX_API_KEY, secret=BITMEX_API_SECRET)
    
    # Websocket Loop for streaming Bitmex data
    async def bitmex_ws_loop():
        """Connect to bitmex websocket to get updates on market and user data."""
        await bitmex.connect()


    async def init_trade():
        """Starts trade procedure by checking wallet, 
        positions, and trading price."""
        # get current positions, wallet amount, and trading price on Bitmex 
        positions = await bitmex.get_position_data()
        print('\nPositions -\n', positions, '\n\n');
        wallet_amount = await bitmex.get_wallet_amount()
        print('\nWallet -\n', wallet_amount, '\n\n');
        trading_price = await bitmex.get_trading_price()
        print('\nTrading Price -\n', trading_price, '\n\n');
        

        # calc trade amount based on percentage of portfolio available to trade
        trade_amount = 0.1 * wallet_amount
       
        # if we have positions open we want to sell / open a short position
        # if we dont have any positions open, just open a short position
        if positions['open']:
            # sell and short
            quantity = len(positions['open'])
            lim = await create_limit_order(quantity, trading_price)
            shor = await create_short(trading_price, trade_amount)
            await bitmex.bulk_order([lim, shor])
        else:
            # short
            my_short = await create_short(trading_price, trade_amount)
            await bitmex.short(my_short['quantity'], my_short['price'])


        asyncio.sleep(10)

        positions = await bitmex.get_position_data()
        print('\nPositions -\n', positions, '\n\n');
        wallet_amount = await bitmex.get_wallet_amount()
        print('\nWallet -\n', wallet_amount, '\n\n');
        trading_price = await bitmex.get_trading_price()
        print('\nTrading Price -\n', trading_price, '\n\n');
        await bitmex.get_order_data()
        

    async def create_limit_order(quantity, trading_price):
        """Calculate limit price and return object with 'quantity' 'price' and 'side'."""
        # smaller difference makes trades execute faster
        difference = 0.5
        limit_price = trading_price - difference

        print(c[3] + f"\nCreating limit order.\nQuanitity - {quantity}, Price - {limit_price}\n" + c[0])

        return {'quantity':quantity, 'price':limit_price, 'side': 'Sell'}
        

    async def create_short(trading_price, amount):
        """Calculate short amount and return object with 'quantity' 'price' and 'side'."""
        quantity = 100
        short_price = trading_price - 200

        print(c[3] + f"\nOpening short.\nQuanitity - {quantity}, Price - {short_price}\n" + c[0])

        return {'quantity': quantity, 'price': short_price, 'side': 'Sell'} 





    try:
        # Create tasks for both websockets 
        loop.create_task(bitmex_ws_loop())
        loop.create_task(do_this_after_delay(5,init_trade))
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