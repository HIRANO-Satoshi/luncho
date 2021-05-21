'''
  Exchange rates

  Created on 2021/05/09

  Author: HIRANO Satoshi
'''

import datetime
import json
import time
import sys
import logging
from threading import Thread
from typing import Type, Optional, List, Dict #, Tuple, Union, Any, Generator, cast
from typing_extensions import TypedDict
import requests

from src.utils import error
from src.types import Currency, CurrencyCode, C1000
import conf
if conf.Use_Fixer_For_Forex:
    import api_keys

# exchange rates based on USD
Exchange_Rates: Dict[CurrencyCode, float] = {}  # { currencyCode: rate }

# Expiration time of Exchange_Rates
expiration: float = 0.0

# time of the last load of Exchange_Rates
last_load: float = 0

# Dollar/SDR
Dollar_Per_SDR: float = 0   # filled in load_exchange_rates()  1 SDR = $1.4...

class FixerExchangeRate(TypedDict):
    success: bool    # true if API success
    timestamp: int   # 1605081845
    base: str        # always "EUR"
    date: str        #"2020-11-11",
    rates: Dict[CurrencyCode, float]   # "AED": 4.337445

Fixer_Exchange_Rates: FixerExchangeRate = {}

def convert(source: Currency, currencyCode: CurrencyCode) -> Currency:
    if source.currencyCode == currencyCode:
        return source

    source_exchange_rate: Optional[float] = Exchange_Rates.get(source.currencyCode, None)
    if source_exchange_rate is None or source_exchange_rate == 0:
        error(source.currencyCode, "Currency code mismatch")

    to_exchange_rate: Optional[float] = Exchange_Rates.get(currencyCode, None)
    if to_exchange_rate is None:
        error(currencyCode, "Currency code mismatch")

    value: float = source.value / source_exchange_rate * to_exchange_rate
    return Currency(code=currencyCode, value=int(value))


def exchange_rate_per_USD(currencyCode: CurrencyCode) -> float:
    ''' Returns exchange rate per USD for the currencyCode.
        None if the currencyCode is not available. '''

    return Exchange_Rates.get(currencyCode, 0.0)

def load_exchange_rates(use_dummy_data: bool):
    ''' Load exchange rates and SDR from fixer or dummy data file. '''

    global Fixer_Exchange_Rates, Exchange_Rates, last_load, expiration

    if use_dummy_data:
        with open('data/dummy-fixer-exchange-2020-11-11.json', 'r', newline='', encoding="utf_8_sig") as fixer_file:
            # 168 currencies
            Fixer_Exchange_Rates = json.load(fixer_file)
    else:
        url: str
        if conf.Use_Fixer_For_Forex:
            url = ''.join(('http://data.fixer.io/api/latest?access_key=', api_keys.Fixer_Access_Key))
        else:
            url = ''.join(('https://api.exchangerate.host/latest'))

        response = requests.get(url, headers=conf.Header_To_Fetch('en'), allow_redirects=True)
        if not response.ok:   # no retry. will load after one hour.
            return
        Fixer_Exchange_Rates = json.loads(response.text)

        logging.debug('Fetched exchange rate')

    assert Fixer_Exchange_Rates['base'] == 'EUR'  # always EUR with free plan

    usd: float = Fixer_Exchange_Rates['rates']['USD']  # USD per euro
    for currecy_code, euro_value in Fixer_Exchange_Rates['rates'].items():  #type: CurrencyCode, float
        Exchange_Rates[currecy_code] = euro_value / usd   # store in USD
        if currecy_code == 'XDR':
            global Dollar_Per_SDR
            Dollar_Per_SDR = 1 / Exchange_Rates[currecy_code]
            logging.debug('Dollar/SDR = ' + str(Dollar_Per_SDR))

    last_load = time.time()

    # expires 40 sec after Forex data update time
    expiration = timeToUpdate() + 40

    from src import ppp_data
    ppp_data.update()



def cron(use_dummy_data):
    '''Cron task thread. Update exchange rate data at 00:06 UTC everyday,
       since exchangerate.host updates at 00:05. https://exchangerate.host/#/#docs"

        In case on App Engine, cron.yaml is used and this is not used.
    '''

    while True:
        time.sleep(timeToUpdate() - time.time())
        #time.sleep(10)        # test
        load_exchange_rates(use_dummy_data)


def init(use_dummy_data):
    ''' Initialize exchange rates. '''

    # load exchange rates at startup and every one hour
    load_exchange_rates(use_dummy_data)

    if conf.Is_AppEngine:
        # we use cron.yaml on GAE
        pass
    else:
        # start cron task
        thread: Thread = Thread(target=cron, args=(use_dummy_data,))
        thread.start()

def timeToUpdate():
    ''' Returns next update time in POSIX time. '''

    if conf.Use_Fixer_For_Forex:
        # Fixer update every hour. We update 3 minute every hour. 00:03, 01:03, 02:03...
        #
        #  now = datetime.datetime(2021, 5, 21, 15, 26, 27, 291409)
        #  next_hour = datetime.datetime(2021, 5, 21, 16, 26, 27, 291409)
        #  time_until_next_hour = datetime.timedelta(seconds=2012, microseconds=708591)
        #  seconds_until_next_hour = 2012
        #  time_to_update = 1621580600 (2021-05-21 16:03)
        #
        now: datetime = datetime.datetime.now()
        next_hour: datetime  = now + datetime.timedelta(hours=1)
        time_until_next_hour: datetime.timedelta = next_hour.replace(minute=0, second=0, microsecond=0) - now
        seconds_until_next_hour: int = time_until_next_hour.seconds
        time_to_update: float = time.time() + seconds_until_next_hour + 3*60
        return time_to_update
    else:
        # exchangerate.host updates every day at 00:05 https://exchangerate.host/#/#docs"
        # we update at 00:06 everyday.
        #
        #  now = datetime.datetime(2021, 5, 21, 15, 22, 7, 226310)
        #  tomorrow = datetime.datetime(2021, 5, 22, 15, 22, 7, 226310)
        #  time_until_midnight = datetime.timedelta(seconds=31072, microseconds=773690)
        #  seconds_until_midnight = 31072
        #  time_to_update = 1621609503.573357 (2021-05-22 00:06:00)
        #
        now: datetime = datetime.datetime.now()
        tomorrow: datetime  = now + datetime.timedelta(days=1)
        time_until_midnight: datetime.timedelta = datetime.datetime.combine(tomorrow, datetime.time.min) - now
        seconds_until_midnight: int = time_until_midnight.seconds
        time_to_update = time.time() + seconds_until_midnight + 6*60
        return time_to_update
