# TraderBot

Project to test reading BitMEX inflow data from
Token Analyst's websocket to trigger trades on the
BitMEX exchange.

- Connects to Token Analyst websocket for on-chain data
- Connects to BitMEX websocket for realtime user/trade data
- Uses Bitmex REST API to buy/sell XBTUSD


## Requirements

- TokenAnalyst Pro Api key
- BitMEX API key and secret


## Getting Started

- Clone or download project
- Install requirements: pip install -r requirements.txt
- Set up config.py 
    - enter your Token Analyst API key, and BitMEX API key and secret
        - you can optionally save your API keys as environment variables
    - choose symbol and BitMEX endpoints 
        - (default symbol is XBTUSD, and default endpoints use the BitMEX testnet)
- in TraderBot.py, write your own trade logic in the trader_bot function 
- run TraderBot.py 


## License

This project is licensed under the MIT License - see the [LICENSE.md](LICENSE.md) file for details

