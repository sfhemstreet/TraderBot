import os
from colors import c
import logging
from Exceptions import APIKeyError
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

# bitmex websocket URL - default is testnet, change to make real trades 
G_BITMEX_WS_URL = "wss://testnet.bitmex.com" # REAL TRADES -> "wss://www.bitmex.com"

# bitmex REST API URL - default is testnet, change to make real trades
G_BITMEX_BASE_URL = "https://testnet.bitmex.com/api/v1/" # REAL TRADES -> "https://www.bitmex.com/api/v1/"




def check_config():
    '''
        Checks config.py for API keys and default settings and gets user input for variables not declared.

        If you don't want to input these variables every time, put them in config.py 
    '''

    # check for Token Analyst API KEY
    if len(G_TOKEN_ANALYST_API_KEY) < 8:
        TOKEN_ANALYST_API_KEY = input(c[3] + 
        '''\nEnter Token Analyst API key\n>>> ''' + c[0])
    else:
        TOKEN_ANALYST_API_KEY = G_TOKEN_ANALYST_API_KEY
        
    if len(TOKEN_ANALYST_API_KEY) < 8:
        raise APIKeyError(TOKEN_ANALYST_API_KEY,"INVALID TOKEN ANALYST API KEY")

    
    # check fro Bitmex API Key
    if len(G_BITMEX_API_KEY) < 8:
        BITMEX_API_KEY = input(c[3] + 
        '''\nEnter BitMEX API key\n>>> ''' + c[0])
    else:
        BITMEX_API_KEY = G_BITMEX_API_KEY

    if len(BITMEX_API_KEY) < 8:
        raise APIKeyError(BITMEX_API_KEY,"INVALID BITMEX API KEY.")


    # check for Bitmex API Secret
    if len(G_BITMEX_API_SECRET) < 8:
        BITMEX_API_SECRET = input(c[3] + 
        '''\nEnter BitMEX API Secret\n>>> ''' + c[0])
    else:
        BITMEX_API_SECRET = G_BITMEX_API_SECRET

    if len(BITMEX_API_SECRET) < 8:
        raise APIKeyError(BITMEX_API_SECRET,"INVALID BITMEX API SECRET.")


    # check for bitmex symbol
    if not G_DEFAULT_BITMEX_SYMBOL:
        DEFAULT_BITMEX_SYMBOL = input(c[3] + 
        '''\nEnter BitMEX default symbol \n>>> ''' + c[0])
    else:
        DEFAULT_BITMEX_SYMBOL = G_DEFAULT_BITMEX_SYMBOL

    if  not DEFAULT_BITMEX_SYMBOL:
        raise APIKeyError(DEFAULT_BITMEX_SYMBOL,"INVALID DEFAULT_BITMEX_SYMBOL.")


    # check for bitmex base url
    if not G_BITMEX_BASE_URL:
        BITMEX_BASE_URL = input(c[3] + 
        '''\nEnter BitMEX default base url \n>>> ''' + c[0])
    else:
        BITMEX_BASE_URL = G_BITMEX_BASE_URL

    if not BITMEX_BASE_URL:
        raise APIKeyError(BITMEX_BASE_URL,"INVALID BITMEX_BASE_URL.")

    
    # check for bitmex ws url
    if not G_BITMEX_WS_URL:
        BITMEX_WS_URL = input(c[3] + 
        '''\nEnter BitMEX default websocket url \n>>> ''' + c[0])
    else:
        BITMEX_WS_URL = G_BITMEX_WS_URL

    if not BITMEX_WS_URL:
        raise APIKeyError(BITMEX_WS_URL,"INVALID BITMEX_WS_URL.")


    return (
        TOKEN_ANALYST_API_KEY, 
        BITMEX_API_KEY, 
        BITMEX_API_SECRET, 
        DEFAULT_BITMEX_SYMBOL, 
        BITMEX_BASE_URL, 
        BITMEX_WS_URL
    )