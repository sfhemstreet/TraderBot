# TraderBot

Project to test reading BitMEX inflow data from
Token Analyst's websocket to trigger trades on the
BitMEX exchange.

- Connects to Token Analyst websocket for on-chain data
- Connects to BitMEX websocket for realtime user/trade data
- Uses Bitmex REST API to buy/sell XBTUSD

By default all trades are on the Bitmex TestNet

Required API keys
- Must have TokenAnalyst Pro Api key
- Must have BitMEX API key and secret

To Run
- Install requirements: pip install -r requirements.txt
- open config.py 
    - enter API keys 
        - you can optionally save your API keys as enviroment variables
    - enter trading variables
- in TraderBot.py edit the traderBot function with your own trade logic
- run TraderBot.py


