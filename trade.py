from colors import c
import base64
import uuid
from config import G_DEFAULT_BITMEX_SYMBOL # if you dont have this declared in config go do that

'''
    TRADE
    each returns an order that can be used in a single or bulk order (ie bitmex.place_order(my_order) or bitmex.bulk_order([order1, order2])).
    add your own trade functions here or use self.make_order 
'''
class Trade:
    def __init__(self, symbol, orderIDPrefex="traderbot_"):
        self.symbol = symbol
        self.orderIDPrefex = orderIDPrefex
       

    def market_buy(self,quantity):
        '''
        returns an order to Buy at market price. 
        '''
        side="Buy"
        order = self.make_order(
            quantity=quantity, 
            side=side, 
        )
        return order


    def market_sell(self,quantity):
        '''
        Returns a order for Selling at market price.
        '''
        side="Sell"
        order = self.make_order(
            quantity=quantity, 
            side=side, 
        )
        return order


    def limit_buy(self,quantity, price):
        '''Returns a limit buy order.'''
        self.is_tickSize_valid(price)

        side = "Buy"
        order = self.make_order(
            quantity=quantity, 
            price=price,
            side=side, 
        )
        return order
        

    def limit_sell(self,quantity, price):
        """Returns a limit sell / short order."""

        self.is_tickSize_valid(price)

        side="Sell"
        order = self.make_order(
            quantity=quantity, 
            price=price,
            side=side, 
        )
        return order


    def stop_order(self,quantity, stopPx, price=None, execInst=None):
        '''Returns a stop order.
        Use a price below the current price for stop-sell orders and buy-if-touched orders. 
        Use execInst of 'MarkPrice' or 'LastPrice' to define the current price used for triggering.
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
        '''
        if symbol == None:
            symbol = self.symbol

        if orderIDPrefix == None:
            orderIDPrefix = self.orderIDPrefex

        if quantity == None and side == None:
            raise Exception(c[2] + "Side or quantity required to close." + c[0])

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
            Returns an order object ready to use in bulk or single order. 
            Must supply quantity. 
            If no price supplied, order is market sell or buy.
            side is either 'Buy' or 'Sell'
            displayQty of 0 hides order
            stopPx, optional trigger price, use a price below the current price for stop-sell orders and buy-if-touched orders.
            For more info see Bitmex API explorer.
        """
        # Read Me - This creates all the orders below, so dont break it

        if price and price < 0:
            raise Exception(c[2] + "Order Price must be positive." + c[0])

        if price:
            self.is_tickSize_valid(price)

        if not quantity and execInst != 'Close':
            raise Exception(c[2] + "Must supply order quantity." + c[0])

        if side and side != 'Sell' and side != 'Buy':
            raise Exception(c[2] + "Side must be 'Sell' or 'Buy'." + c[0])

        if orderType and (
            orderType != 'Market' or
            orderType != 'Limit' or
            orderType != 'Stop' or 
            orderType != 'StopLimit' or
            orderType != 'MarketIfTouched' or
            orderType != 'LimitIfTouched' or
            orderType != 'Pegged'
        ):
            raise Exception(c[2] + "orderType must be Market, Limit, Stop, StopLimit, MarketIfTouched, LimitIfTouched, or Pegged" + c[0])

        if displayQty and displayQty < 0:
            raise Exception(c[2] + "DisplayQty is negative, must be 0 to hide order or positive." + c[0])
        
        if pegPriceType and (
            pegPriceType != 'LastPeg' or 
            pegPriceType != 'MidPricePeg' or 
            pegPriceType != 'MarketPeg' or 
            pegPriceType != 'PrimaryPeg' or 
            pegPriceType != 'TrailingStopPeg'
        ):
            raise Exception(c[2] + "pegPriceType must be LastPeg, MidPricePeg, MarketPeg, PrimaryPeg, or TrailingStopPeg." + c[0])

        if timeInForce and (
            timeInForce != 'Day' or 
            timeInForce != 'GoodTillCancel' or 
            timeInForce != 'ImmediateOrCancel' or 
            timeInForce != 'FillOrKill'
        ):
            raise Exception(c[2] + "timeInForce must be Day, GoodTillCancel, ImmediateOrCancel, or FillOrKill" + c[0])
        
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
            raise Exception(c[2] + "execInst must be ParticipateDoNotInitiate, AllOrNone, MarkPrice, IndexPrice, LastPrice, Close, ReduceOnly, or Fixed." + c[0])
        
        if execInst and execInst == 'AllOrNone' and displayQty != 0:
            raise Exception(c[2] + "execInst is 'AllOrNone', displayQty must be 0" + c[0])

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
        if not isinstance(price, int) or not isinstance(price + 0.5, int):
            raise Exception(c[2] + "Invalid Tick Size! Prices must be set at integer or .5 between" + c[0])
        