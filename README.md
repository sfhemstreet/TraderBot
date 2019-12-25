# TraderBot

Trading Bot that uses real-time bitcoin inflow/outflow data from [Token Analyst's](https://www.tokenanalyst.io/) websocket feed 
to trigger trades on the BitMEX exchange.


## Description

Uses asyncio and websockets to connect to both Token Analyst and BitMEX websockets. 

The TokenAnalyst websocket feed provides real-time bitcoin inflows and outflows to/from exchanges.

The Bitmex websocket feed provides user position, margin, order, wallet, execution and trade data.


**Features**

- Asynchronously connect to Token Analyst's and Bitmex's websockets
- Check for inflows/outflows, filter by exchange and by value
- Make orders for Bitmex
- Interact with Bitmex REST API to place/amend/cancel orders, update leverage, etc
- Avoid hitting rate-limit / being labeled as a spam-account


## Requirements

- TokenAnalyst Pro Api key
- BitMEX API key and secret


## Getting Started

- Clone or download project
- Install requirements: `pip install -r requirements.txt`
- Set up config.py 
    - enter your Token Analyst API key, and BitMEX API key and secret
        - or save your API keys/secrets as environment variables
    - choose symbol and BitMEX endpoints 
        - default symbol is XBTUSD, and default endpoints use the BitMEX testnet
- in TraderBot.py, write your own trade logic in the trader_bot function 
- run TraderBot.py 


## Usage

NOTE : Default config.py settings place all Bitmex orders on the Bitmex testnet.

All inflow/outflow data is sent to trader_bot in TraderBot.py, this should be the starting point for any actions.

4 classes instances are available inside trader_bot,

- `token_analyst` - to check websocket feed data 
- `trade` - to create orders, ie market sell, limit buy, stop order, etc
- `bitmex`  - to get position, margin, order, wallet, execution and trade data, and to place/amend/cancel orders, update leverage, etc on the Bitmex exchange
- `rate_limit` - to keep count of API calls and avoid hitting limit 

*Example* - 

if trader_bot receives an outflow on Bitmex above the threshold, make a limit buy order and place it on Bitmex. 
```
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
```


## License

This project is licensed under the MIT License 


