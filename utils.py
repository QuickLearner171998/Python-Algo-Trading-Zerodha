# -*- coding: utf-8 -*-
"""
Created on Fri Feb 19 14:22:14 2021

@author: pramay
"""

import datetime as dt
import pandas as pd
import numpy as np
import time
import talib
from termcolor import colored
import pandas_ta as ta


def instrumentLookup(instrument_df, symbol):
    """Looks up instrument token for a given script from instrument dump"""
    try:
        return instrument_df[instrument_df.tradingsymbol == symbol].instrument_token.values[0]
    except:
        return -1


def getTickSize(instrument_df, symbol):
    """gets the tick size for a given script from instrument dump"""
    try:
        return instrument_df[instrument_df.tradingsymbol == symbol].tick_size.values[0]
    except:
        return -1


def fetchOHLC(kite, instrument_df, ticker, interval, duration):
    """extracts historical data and outputs in the form of dataframe"""
    instrument = instrumentLookup(instrument_df, ticker)
    data = pd.DataFrame(kite.historical_data(instrument, dt.date.today() -
                                             dt.timedelta(duration), dt.date.today(), interval))
    # data.drop(data.tail(1).index, inplace=True)
    data.set_index("date", inplace=True)
    return data


def rsi(df, n):
    "function to calculate RSI"
    delta = df["close"].diff().dropna()
    u = delta * 0
    d = u.copy()
    u[delta > 0] = delta[delta > 0]
    d[delta < 0] = -delta[delta < 0]
    u[u.index[n-1]] = np.mean(u[:n])  # first value is average of gains
    u = u.drop(u.index[:(n-1)])
    d[d.index[n-1]] = np.mean(d[:n])  # first value is average of losses
    d = d.drop(d.index[:(n-1)])
    rs = u.ewm(com=n, min_periods=n).mean()/d.ewm(com=n, min_periods=n).mean()
    return 100 - 100 / (1+rs)


def PSAR_V1(data, acc=0.02, maxi=0.2):
    return talib.SAR(data['high'], data['low'], acceleration=acc, maximum=maxi)


def PSAR(data):
    # https://github.com/mrjbq7/ta-lib/issues/196
    # https://github.com/twopirllc/pandas-ta#installation
    temp_data = data.ta.psar()
    return temp_data['PSARl_0.02_0.2'].combine_first(temp_data['PSARs_0.02_0.2'])


def notify(error=False):
    """make sound to notify"""

    import winsound
    if not error:
        frequency = 500  # Set Frequency To 2500 Hertz
        duration = 200  # Set Duration To 1000 ms == 1 second
    else:
        frequency = 500  # Set Frequency To 2500 Hertz
        duration = 100  # Set Duration To 1000 ms == 1 second

    winsound.Beep(frequency, duration)


def notifyGTTOrder(kite, symbol, buy_sell, quantity, sl_price, ltp, exchange, trigger_id_gtt, product_type, target=None):
    # make sound to notify
    notify()
    if buy_sell == "buy":
        print(colored("{} - Placing {} order at {}. Given Price - {}".format(symbol,
                                                                             buy_sell, time.asctime(time.localtime(time.time())), ltp), 'green', 'on_grey'))
    else:
        print(colored("{} - Placing {} order at {}. Given Price - {}".format(symbol,
                                                                             buy_sell, time.asctime(time.localtime(time.time())), ltp), 'red', 'on_grey'))

    if buy_sell == "buy":
        t_type = kite.TRANSACTION_TYPE_BUY
        t_type_sl = kite.TRANSACTION_TYPE_SELL
    elif buy_sell == "sell":
        t_type = kite.TRANSACTION_TYPE_SELL
        t_type_sl = kite.TRANSACTION_TYPE_BUY

    print("Placing GTT order type {} at {}".format(
        t_type_sl, time.asctime(time.localtime(time.time()))))
    print("SL Price ", sl_price)


def placeGTTOrder(kite, symbol, buy_sell, quantity, sl_price, buy_price, exchange, trigger_id_gtt, product_type, current_price, target=None):
    # make sound to notify
    notify()
    if buy_sell == "buy":
        print(colored("{} - Placing {} order at {}. Given Price - {}".format(symbol,
                                                                             buy_sell, time.asctime(time.localtime(time.time())), buy_price), 'green', 'on_grey'))
    else:
        print(colored("{} - Placing {} order at {}. Given Price - {}".format(symbol,
                                                                             buy_sell, time.asctime(time.localtime(time.time())), buy_price), 'red', 'on_grey'))

    # print("{} - Placing {} order at {}".format(symbol, buy_sell, time.asctime( time.localtime(time.time()))))

    if buy_sell == "buy":
        t_type = kite.TRANSACTION_TYPE_BUY
        t_type_sl = kite.TRANSACTION_TYPE_SELL
    elif buy_sell == "sell":
        t_type = kite.TRANSACTION_TYPE_SELL
        t_type_sl = kite.TRANSACTION_TYPE_BUY

    if buy_price < current_price:
        # place limit for different price
        # https://kite.trade/forum/discussion/9328/buy-price-in-kite-place-order#latest
        print("LIMIT as current price is higher that the desired buy price")
        kite.place_order(tradingsymbol=symbol,
                         exchange=exchange,
                         transaction_type=t_type,
                         quantity=quantity,
                         order_type=kite.ORDER_TYPE_LIMIT,
                         price=buy_price,
                         product=product_type,
                         variety=kite.VARIETY_REGULAR,
                         validity=kite.VALIDITY_DAY)
    else:
        print("SL as the buy_price is higher than the current price")
        kite.place_order(tradingsymbol=symbol,
                         exchange=exchange,
                         transaction_type=t_type,
                         quantity=quantity,
                         order_type=kite.ORDER_TYPE_SL,
                         price=buy_price,
                         trigger_price=buy_price,
                         product=product_type,
                         variety=kite.VARIETY_REGULAR,
                         validity=kite.VALIDITY_DAY)

    order_dict = [{"transaction_type": t_type_sl, "quantity": quantity,
                   'order_type': kite.ORDER_TYPE_LIMIT, "product": product_type, "price": sl_price},
                  {"transaction_type": t_type_sl, "quantity": quantity,
                   'order_type': kite.ORDER_TYPE_LIMIT, "product": product_type, "price": target}
                  ]
    print("Placing GTT order type {} at {}".format(
        t_type_sl, time.asctime(time.localtime(time.time()))))

    # trigger_id = kite.place_gtt(kite.GTT_TYPE_OCO, symbol, exchange, [sl_price, target], ltp, order_dict)

    trigger_id = kite.place_gtt(kite.GTT_TYPE_SINGLE, symbol, exchange, [
                                sl_price], buy_price, [order_dict[0]])
    trigger_id_gtt[symbol] = trigger_id['trigger_id']
    print()
    print(trigger_id_gtt)


def notifyMarketOrder(kite, symbol, buy_sell, quantity, exchange, product_type):
    # make sound to notify
    notify()

    if buy_sell == "buy":
        print(colored("{} - Placing Market {} order at {}".format(symbol, buy_sell,
                                                                  time.asctime(time.localtime(time.time()))), 'cyan', 'on_grey'))
    else:
        print(colored("{} - Placing Market {} order at {}".format(symbol, buy_sell,
                                                                  time.asctime(time.localtime(time.time()))), 'yellow', 'on_grey'))


def placeMarketOrder(kite, symbol, buy_sell, quantity, exchange, product_type):
    # make sound to notify
    notify()

    if buy_sell == "buy":
        print(colored("{} - Placing Market {} order at {}".format(symbol, buy_sell,
                                                                  time.asctime(time.localtime(time.time()))), 'cyan', 'on_grey'))
    else:
        print(colored("{} - Placing Market {} order at {}".format(symbol, buy_sell,
                                                                  time.asctime(time.localtime(time.time()))), 'yellow', 'on_grey'))

    if buy_sell == "buy":
        t_type = kite.TRANSACTION_TYPE_BUY
    elif buy_sell == "sell":
        t_type = kite.TRANSACTION_TYPE_SELL

    # place normal market order
    kite.place_order(tradingsymbol=symbol,
                     exchange=exchange,
                     transaction_type=t_type,
                     quantity=quantity,
                     order_type=kite.ORDER_TYPE_MARKET,
                     product=product_type,
                     variety=kite.VARIETY_REGULAR)


def ModifyOrder(kite, symbol, order_id, price):
    # Modify order given order id
    print("{} - Modifying order at {}".format(symbol, time.asctime(time.localtime(time.time()))))
    print("Setting Stop Loss ", price)
    kite.modify_order(order_id=order_id,
                      price=price,
                      trigger_price=price,
                      order_type=kite.ORDER_TYPE_SL,
                      variety=kite.VARIETY_REGULAR)
