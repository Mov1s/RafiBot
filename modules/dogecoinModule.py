from ircBase import *
import urllib2
import json
from decimal import Decimal

CRYPTSY_API_URL = 'http://pubapi.cryptsy.com/api.php?method=singlemarketdata&marketid=132'
COINBASE_API_URL = 'https://coinbase.com/api/v1/prices/spot_rate'

#Response for the 'doge ma' expression
@respondtoregex('(doge|DOGE)(ma|me)? (.*)')
def doge_ma_response(message, **extra_args):
    doge = get_cryptsy_query()
    btc = get_coinbase_query()
    per10k = doge*Decimal(10000)*btc
    response = "Current price: %s BTC or $%0.2f per 10000 DOGE with a BTC value of $%0.2f" % (doge,per10k,btc)
    return message.new_response_message(response)

#Searches cryptsy and averages all of the latest doge transaction prices
def get_cryptsy_query():
    try:
        url = CRYPTSY_API_URL
        response = urllib2.urlopen(url)
        response_string = response.read()
        response_JSON = json.loads(response_string)
        avg_price = Decimal(0)
        count = 0
        trades = response_JSON[u'return'][u'markets'][u'DOGE'][u'recenttrades']

        for trade in trades:
            avg_price += Decimal(trade[u'price']) 
            count += 1

        avg_price = Decimal(avg_price)/ Decimal(count)    
        return avg_price
    except:
        return 0
        
#Gets the spot price for bitcoins from coinbase    
def get_coinbase_query():
    try:
        url = COINBASE_API_URL
        response = urllib2.urlopen(url)
        response_string = response.read()
        response_JSON = json.loads(response_string) 
        return Decimal(response_JSON[u'amount'])
    except:
        return 0
