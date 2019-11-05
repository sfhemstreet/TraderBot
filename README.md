# TraderBot

Project to test reading BitMEX inflow data from
Token Analyst's websocket to trigger trades on the
BitMEX exchange.

- Connects to Token Analyst websocket for on-chain inflow data
- Connects to BitMEX websocket for realtime user/trade data
- Uses Bitmex REST API to buy/sell XBTUSD

By default all trades are on the Bitmex TestNet

Required API keys
- Must have TokenAnalyst Pro Api key
- Must have BitMEX API key and secret

To Test
- install the requirements in requirements.txt
- run TraderBot.py 
