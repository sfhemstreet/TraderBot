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
    Optional - if not filled out here you will have to input 
    them manually every time.
'''
# default symbol for trades 
G_DEFAULT_BITMEX_SYMBOL = "XBTUSD"

# default bitmex websocket is set to testnet, change to make real trades 
G_DEFAULT_BITMEX_WS_URL = "wss://testnet.bitmex.com" # for real trades use "wss://www.bitmex.com"

# default bitmex REST API url is set to testnet, change to make real trades
G_DEFAULT_BITMEX_BASE_URL = "https://testnet.bitmex.com/api/v1/" # for real trades use "https://www.bitmex.com/api/v1"

