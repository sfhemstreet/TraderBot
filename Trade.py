from colors import c
import base64
import uuid
from config import G_DEFAULT_BITMEX_SYMBOL # if you dont have this declared in config go do that
from Exceptions import InvalidArgError

class Trade:
    '''
    class for making orders to send thru the Bitmex API.

    Attributes:

    `symbol: str`
        symbol for trades

    `orderIdPrefex: str`
        prefex for order IDs

    Methods:

    `market_buy`

    `market_sell`

    `limit_buy`

    `limit_sell`

    `stop_order`

    `close`

    `make_order`

    each method returns an order that can be used in a single or bulk order 
    
    (ie bitmex.place_order(my_order) or bitmex.place_bulk_order([order1, order2]))

    '''
    def __init__(self, symbol, orderIDPrefex="traderbot_"):
        self.symbol = symbol
        self.orderIDPrefex = orderIDPrefex
       

    def market_buy(self,quantity):
        '''
        returns an order to Buy at market price. 

        Parameters:

        `quantity: int`
            number of contracts

        Returns:

        `order: dict`
            market buy order
        '''
        side="Buy"
        order = self.make_order(
            quantity=quantity, 
            side=side, 
        )
        return order


    def market_sell(self,quantity):
        '''
        Make a order for Selling at market price.

        Parameters:

        `quantity: int`
            number of contracts

        Returns:

        `order: dict`
            market sell order
        '''
        side="Sell"
        order = self.make_order(
            quantity=quantity, 
            side=side, 
        )
        return order


    def limit_buy(self,quantity, price):
        '''Make a limit buy order.
        
        Parameters:

        `quantity: int`
            number of contracts

        `price: float`
            price, must be val;id tickSize, ie must be integer or .5 between int 

        Returns:

        `order: dict`
            limit buy order
        
        '''
        self.is_tickSize_valid(price)

        side = "Buy"
        order = self.make_order(
            quantity=quantity, 
            price=price,
            side=side, 
        )
        return order
        

    def limit_sell(self,quantity, price):
        """Make a limit sell / short order.
        
        Parameters:

        `quantity: int`
            number of contracts

        `price: float`
            price, must be val;id tickSize, ie must be integer or .5 between int

        Returns:

        `order: dict`
            limit sell order
        
        """

        self.is_tickSize_valid(price)

        side="Sell"
        order = self.make_order(
            quantity=quantity, 
            price=price,
            side=side, 
        )
        return order


    def stop_order(self,quantity, stopPx, price=None, execInst=None):
        '''
        Creates a stop order.

        Use a price below the current price for stop-sell orders and buy-if-touched orders. 

        Use execInst of 'MarkPrice' or 'LastPrice' to define the current price used for triggering.

        Parameters:

        `quantity: int`
            number of contracts

        `stopPx: float`
            stop price

        `price: float`
            price

        `execInst:str`

        Returns:
        
        `order: dict`
            stop order 
        '''
        if price:
            self.is_tickSize_valid(price)

        order = self.make_order(
            quantity=quantity, 
            stopPx=stopPx,
            price=price,
            execInst=execInst
        )
        return order


    def close(self,quantity=None, side=None, symbol=None, orderIDPrefix=None):
        '''
        Returns a close order ready to send to Bitmex.

        cancel other active limit orders with the same side and symbol if the open quantity exceeds the current position.

        Side or quantity required.
        --------------------------

        Parameters:

        `quantity: int`
            number of contracts to close

        `side: str`
            Buy or Sell

        `symbol: str`
            symbol to apply close to

        `orderIDPrefix: str`
            label prefix of close, if none supplied uses default

        Returns:

        `order: dict`
            close order
        
        '''
        if symbol == None:
            symbol = self.symbol

        if orderIDPrefix == None:
            orderIDPrefix = self.orderIDPrefex

        if quantity == None and side == None:
            raise InvalidArgError([quantity, side],"Side or quantity required to close.")

        clOrdID = orderIDPrefix + base64.b64encode(uuid.uuid4().bytes).decode('utf8').rstrip('=\n')
        order = {
            'symbol': symbol,
            'clOrdID': clOrdID,
            'execInst': 'Close'
        }
        if quantity: order['orderQty'] = quantity,
        if side: order['side'] = side

        return order


    def make_order(
        self,
        quantity=None, 
        symbol=None, 
        price=None, 
        side=None, 
        orderType=None, 
        displayQty=None, 
        stopPx=None, 
        pegOffsetValue=None, 
        pegPriceType=None, 
        timeInForce=None, 
        execInst=None, 
        orderIDPrefix=None):
        """
            Make your own order.

            Parameters:

            `quantity: int`
                number of contracts, each contract is worth 1 USD of Bitcoin. 
             
            `symbol: str`
                symbol of trade

            `price: float`
                price of trade, must be approprate ticksize, either an integer or .5
                If no price supplied, order is market sell or buy.

            `side: str`
                buy or sell

            `orderType: str`
                type of order (Market, Limit, Stop, StopLimit, MarketIfTouched, LimitIfTouched, or Pegged)

            `displayQty: int`
                what quantity yopu want order to display, 0 hides order

            `stopPx: float`
                optional trigger price, use a price below the current price for stop-sell orders and buy-if-touched orders.
            
            `pegOffsetValue: float`
                value of pegOffset

            `pegPriceType:str`
                pegOffset type (LastPeg, MidPricePeg, MarketPeg, PrimaryPeg, or TrailingStopPeg)

            `timeInForce: str`
                (Day, GoodTillCancel, ImmediateOrCancel, or FillOrKill) 

            `execInst: str`
                (ParticipateDoNotInitiate, AllOrNone, MarkPrice, IndexPrice, LastPrice, Close, ReduceOnly, or Fixed)

            `orderIDPrefix:str`
                labels order id with prefix
            
            For more info on orders see Bitmex API explorer.

            Returns:
            
            `order: dict`
                an order ready to be sent in a bulk or single order.
        """
        # Read Me - This creates all the orders below, so dont break it

        if price and price < 0:
            raise InvalidArgError(price,"Order Price must be positive.")

        if price:
            self.is_tickSize_valid(price)

        if not quantity and execInst != 'Close':
            raise InvalidArgError([quantity, execInst],"Must supply order quantity.")

        if side and side != 'Sell' and side != 'Buy':
            raise InvalidArgError(side,"Side must be 'Sell' or 'Buy'.")

        if orderType and (
            orderType != 'Market' or
            orderType != 'Limit' or
            orderType != 'Stop' or 
            orderType != 'StopLimit' or
            orderType != 'MarketIfTouched' or
            orderType != 'LimitIfTouched' or
            orderType != 'Pegged'
        ):
            raise InvalidArgError(orderType,"orderType must be Market, Limit, Stop, StopLimit, MarketIfTouched, LimitIfTouched, or Pegged")

        if displayQty and displayQty < 0:
            raise InvalidArgError(displayQty,"DisplayQty is negative, must be 0 to hide order or positive.")
        
        if pegPriceType and (
            pegPriceType != 'LastPeg' or 
            pegPriceType != 'MidPricePeg' or 
            pegPriceType != 'MarketPeg' or 
            pegPriceType != 'PrimaryPeg' or 
            pegPriceType != 'TrailingStopPeg'
        ):
            raise InvalidArgError(pegPriceType,"pegPriceType must be LastPeg, MidPricePeg, MarketPeg, PrimaryPeg, or TrailingStopPeg.")

        if timeInForce and (
            timeInForce != 'Day' or 
            timeInForce != 'GoodTillCancel' or 
            timeInForce != 'ImmediateOrCancel' or 
            timeInForce != 'FillOrKill'
        ):
            raise InvalidArgError(timeInForce,"timeInForce must be Day, GoodTillCancel, ImmediateOrCancel, or FillOrKill")
        
        if execInst and (
            execInst != 'ParticipateDoNotInitiate' or 
            execInst != 'AllOrNone' or 
            execInst != 'MarkPrice' or 
            execInst != 'IndexPrice' or 
            execInst != 'LastPrice' or 
            execInst != 'Close' or 
            execInst != 'ReduceOnly' or 
            execInst != 'Fixed'
        ):
            raise InvalidArgError(execInst,"execInst must be ParticipateDoNotInitiate, AllOrNone, MarkPrice, IndexPrice, LastPrice, Close, ReduceOnly, or Fixed.")
        
        if execInst and execInst == 'AllOrNone' and displayQty != 0:
            raise InvalidArgError([execInst, displayQty],"execInst is 'AllOrNone', displayQty must be 0" + c[0])

        if symbol == None:
            symbol = self.symbol
            
        if orderIDPrefix == None:
            orderIDPrefix = self.orderIDPrefex

        # Generate a unique clOrdID with our prefix so we can identify it.
        clOrdID = orderIDPrefix + base64.b64encode(uuid.uuid4().bytes).decode('utf8').rstrip('=\n')
        order = {
            'symbol': symbol,
            'clOrdID': clOrdID,
        }
        # add to order if supplied 
        if quantity:        order['orderQty'] = quantity 
        if side:            order['side'] = side
        if price:           order['price'] = price
        if displayQty:      order['displayQty'] = displayQty
        if stopPx:          order['stopPx'] = stopPx
        if pegOffsetValue:  order['pegOffsetValue'] = pegOffsetValue
        if timeInForce:     order['timeInForce'] = timeInForce
        if execInst:        order['execInst'] = execInst
        if orderType:       order['ordType'] = orderType

        return order


    def is_tickSize_valid(self,price):
        """Check for valid tickSize, ie if the price is an integer or .5 away."""

        if not isinstance(price, int):
            if not isinstance(price + 0.5, int):
                raise InvalidArgError(price,"Invalid Tick Size! Prices must be set at integer or .5 between")
        
