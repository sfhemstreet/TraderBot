import os
'''
    API keys can be held in your enviroment or copy and pasted below.
    Comment out / delete which ever you are not using.
    Keep em secret, keep em safe. 
'''
G_TOKEN_ANALYST_API_KEY = os.environ['TOKEN_ANALYST_API_KEY']
G_BITMEX_API_KEY =        os.environ['BITMEX_API_KEY']
G_BITMEX_API_SECRET =     os.environ['BITMEX_API_SECRET']
'''
G_TOKEN_ANALYST_API_KEY = 'API_KEY'
G_BITMEX_API_KEY =        'API_KEY'
G_BITMEX_API_SECRET =     'SECRET'
'''

''' 
    Global Trading Variables
'''
# default symbol for trades - see Bitmex API docs for other valid symbols
G_DEFAULT_BITMEX_SYMBOL = "XBTUSD"

# default is testnet, change to make real trades 
G_DEFAULT_BITMEX_WS_URL = "wss://testnet.bitmex.com" # REAL TRADES -> "wss://www.bitmex.com"

# default is testnet, change to make real trades
G_DEFAULT_BITMEX_BASE_URL = "https://testnet.bitmex.com/api/v1/" # REAL TRADES -> "https://www.bitmex.com/api/v1/"

