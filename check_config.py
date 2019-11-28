from config import *
from colors import c
import logging

def check_config():
    '''
        Checks config.py for API keys and gets user input for API keys not declared.
        If you don't want to input these variables every time, put them in config.py 
    '''
    # check for Token Analyst API KEY
    if len(G_TOKEN_ANALYST_API_KEY) < 8:
        TOKEN_ANALYST_API_KEY = input(c[3] + 
        '''\nEnter Token Analyst API key\n>>> ''' + c[0])
    else:
        TOKEN_ANALYST_API_KEY = G_TOKEN_ANALYST_API_KEY
        
    if len(TOKEN_ANALYST_API_KEY) < 8:
        raise Exception(c[2] + "\nINVALID TOKEN ANALYST API KEY\n" + c[0])

    
    # check fro Bitmex API Key
    if len(G_BITMEX_API_KEY) < 8:
        BITMEX_API_KEY = input(c[3] + 
        '''\nEnter BitMEX API key\n>>> ''' + c[0])
    else:
        BITMEX_API_KEY = G_BITMEX_API_KEY

    if len(BITMEX_API_KEY) < 8:
        raise Exception(c[2] + "\nINVALID BITMEX API KEY\n" + c[0])


    # check for Bitmex API Secret
    if len(G_BITMEX_API_SECRET) < 8:
        BITMEX_API_SECRET = input(c[3] + 
        '''\nEnter BitMEX API Secret\n>>> ''' + c[0])
    else:
        BITMEX_API_SECRET = G_BITMEX_API_SECRET

    if len(BITMEX_API_SECRET) < 8:
        raise Exception(c[2] + "\nINVALID BITMEX API SECRET\n" + c[0])


    return (TOKEN_ANALYST_API_KEY, BITMEX_API_KEY, BITMEX_API_SECRET)