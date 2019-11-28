from config import *
from colors import c
import logging

def check_config():
    '''
        Checks config.py for variables and gets user input for variables not declared.
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


    # get user input to set DEFAULT_SYMBOL if not declared globally (ie XBTUSD)
    if G_DEFAULT_SYMBOL == None:
        raise Exception(c[2] + "\nSET G_DEFAULT_SYMBOL IN CONFIG ie 'XBTUSD'")


    # get user input to set THRESHOLD if not declared globally (float > 0)
    if G_INFLOW_THRESHOLD == None:
        INFLOW_THRESHOLD = float(input(c[3] + 
        '''\nEnter Token Analyst INFLOW value threshold.\n~ Must be a number greater than 0 ~
        \n>>> ''' + c[0]))
    else:
        INFLOW_THRESHOLD = G_INFLOW_THRESHOLD
        
    if INFLOW_THRESHOLD <= 0:
        raise Exception(c[2] + "\nTHRESHOLD MUST BE ABOVE 0\n" + c[0])

    # get user input to set percentage of portfolio available 
    # to trade with if not declared globally (float > 0 and < 1)
    if G_PORTFOLIO_PERCENTAGE == None:
        PORTFOLIO_PERCENTAGE = float(input(c[3] + 
        '''\nEnter percentage of portfolio available to trade with.\n~ Must be a number greater than 0 and less than 1 ~
        \n>>> ''' + c[0]))
    else:
        PORTFOLIO_PERCENTAGE = G_PORTFOLIO_PERCENTAGE
        
    if PORTFOLIO_PERCENTAGE <= 0 or PORTFOLIO_PERCENTAGE >= 1:
        raise Exception(c[2] + "\nPORTFOLIO PERCENTAGE MUST BE ABOVE 0 AND BELOW 1\n" + c[0])


    # get user input to set trade quanity 
    if G_TRADE_QUANTITY == None:
        TRADE_QUANTITY = int(input(c[3] + 
        '''\nEnter quantity of each trade, ie 1 = $1
        \n>>> ''' + c[0]))
    else:
        TRADE_QUANTITY = G_TRADE_QUANTITY
        
    if TRADE_QUANTITY <= 0:
        raise Exception(c[2] + "\nTRADE QUANTITY MUST BE ABOVE 0\n" + c[0])

    logging.debug(f"Inflow Threshold Set at - {INFLOW_THRESHOLD}")
    logging.debug(f"Portfolio precentage set at - {PORTFOLIO_PERCENTAGE}")
    logging.debug(f"Trade quantity is set at - {TRADE_QUANTITY}")
    


    return (TOKEN_ANALYST_API_KEY, BITMEX_API_KEY, BITMEX_API_SECRET)