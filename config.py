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
# set Inflow threshold to base trades off of (float > 0)
G_INFLOW_THRESHOLD = None

# set percentage of portfolio (bitmex wallet) available to with trade (float > 0 and < 1)
G_PORTFOLIO_PERCENTAGE = None

# set default trade quantity ie 1 = $1 must be an integer > 0
G_TRADE_QUANTITY = None