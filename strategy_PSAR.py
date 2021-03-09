# -*- coding: utf-8 -*-
"""
Created on Sat Feb 20 22:27:19 2021

@author: pramay
"""
# to be on safe side start at 9:16:15 i.e 1min 15 sec late than candle start
from kiteconnect import KiteConnect
import os
import pandas as pd
import time
import traceback

# from utils import *
from utils import fetchOHLC, PSAR, getTickSize, placeGTTOrder, placeMarketOrder, notify
cwd = os.getcwd()

# generate trading session
access_token = open("access_token.txt", 'r').read()
key_secret = open("api_key.txt", 'r').read().split()
kite = KiteConnect(api_key=key_secret[0])
kite.set_access_token(access_token)

NSE_NFO = "NSE"
LOT_SIZE = 1
if NSE_NFO == "NFO":
    LOT_SIZE = 25
n_shares = 1
quantity = n_shares*LOT_SIZE  # multiple of LOT_SIZE
capital = 3000
# tickers = ["INFY"]
tickers = ["AXISBANK"]
tickers = ["INDUSINDBK"]
ticker = tickers[0]
exchange_type = kite.EXCHANGE_NSE
if NSE_NFO == "NFO":
    exchange_type = kite.EXCHANGE_NFO
minute = 15
minute_code = "minute"
if minute > 1:
    minute_code = str(minute)+minute_code

trigger_id_gtt = {ticker: None for ticker in tickers}

product_type = kite.PRODUCT_MIS  # or kite.PRODUCT_NRML

# get dump of all nfo instruments
instrument_dump = kite.instruments(NSE_NFO)
instrument_df = pd.DataFrame(instrument_dump)


def main():
    a = 0
    b = 0
    while a < 10:
        try:
            pos_df = pd.DataFrame(kite.positions()["day"])
            break
        except:
            print("can't extract position data..retrying")
            a += 1
    while b < 10:
        try:
            ord_df = pd.DataFrame(kite.orders())
            # print("Orders --- ")
            # print(ord_df)
            break
        except:
            print("can't extract order data..retrying")
            b += 1
    # for ticker in tickers:
    print("\n**************************************************************")
    print("starting passthrough for {} at {}".format(
        ticker, time.asctime(time.localtime(time.time()))))

    try:
        a = 0
        while a < 10:
            try:
                ohlc = fetchOHLC(kite, instrument_df, ticker, minute_code, 30)
                break
            except:
                print("can't extract position data..retrying")
                a += 1
        init_len = len(ohlc)
        ohlc['psar'] = PSAR(ohlc)
        ltp = kite.ltp(NSE_NFO+':' + ticker)[NSE_NFO+':' + ticker]['last_price']
        tick_size = getTickSize(instrument_df, ticker)

        if ohlc['low'][-1] > ohlc['psar'][-1]:
            print("PSAR is below candle")
        elif (ohlc['high'][-1] < ohlc['psar'][-1]):
            print("PSAR is above candle")

        print("PSAR", ohlc['psar'][-1])
        print("Current Price - ", ltp)
        print("OPEN ", ohlc['open'][-1])
        print("Close ", ohlc['close'][-1])
        print("High ", ohlc['high'][-1])
        print("low ", ohlc['low'][-1])

        c1 = len(pos_df.columns) == 0
        c2 = (len(pos_df.columns) != 0 and ticker not in pos_df["tradingsymbol"].tolist())
        c3 = (len(pos_df.columns) != 0 and ticker in pos_df["tradingsymbol"].tolist()) and (
            pos_df[pos_df["tradingsymbol"] == ticker]["quantity"].values[0] == 0)

        # ltp_sell = tick_size * round((ltp-2)/tick_size)
        # sl_sell = tick_size * round((1.05*ltp) /tick_size)
        # strategy
        if c1 or c2 or c3:
            # BUY

            # when psar is below the candle when the condition checked
            if (ohlc['low'][-1] > ohlc['psar'][-1]) and (ohlc['low'][-2] < ohlc['psar'][-2]):
                # https://kite.trade/forum/discussion/9299/set-a-stop-loss-and-target-at-same-time#latest
                # https://kite.trade/forum/discussion/9300/receiving-this-order-price-is-not-a-multiple-of-tick-size#latest
                ltp_ = ohlc['high'][-2] + 2
                ltp_buy = tick_size * round((ltp_)/tick_size)
                sl_buy = tick_size * round((ltp_buy - 20)/tick_size)

                placeGTTOrder(kite, ticker, "buy", quantity, sl_buy, ltp_buy,
                              exchange_type, trigger_id_gtt, product_type, ltp)
                a = 0
                b = 0
                while a < 10:
                    try:
                        pos_df = pd.DataFrame(kite.positions()["day"])
                        break
                    except:
                        print("can't extract position data..retrying")
                        a += 1
                while b < 10:
                    try:
                        ord_df = pd.DataFrame(kite.orders())
                        break
                    except:
                        print("can't extract order data..retrying")
                        b += 1

            # when psar is above candle when condition checked but in between moves below
            # this case will be missed in above condition as when above condition checks already a new candle is formed.

            # for Ex. at 9:15:10 we start our code and PSAR is above the candle. Now we check again at 10:15:10 and PSAR is still above
            # the candle so it again goes to sleep. But now at 10:30 PSAR comes below the cnadle,
            # then when the code checks again at 11:15:10 the PSAR is below and also prev PSAR(10:15) is below so it wont buy.
            # But we have to buy at high(10:15)+2

            # if already order pending then break
            d = ord_df.loc[(ord_df['tradingsymbol'] == ticker) & (
                ord_df['status'].isin(["TRIGGER PENDING", "OPEN", "PENDING"]))]

            if (d.empty) and (ohlc['low'][-1] > ohlc['psar'][-1]) and (ohlc['low'][-2] > ohlc['psar'][-2]) and (ohlc['low'][-3] < ohlc['psar'][-3]):
                print("BUY was missed but taken care of !!")
                ltp_ = ohlc['high'][-2] + 2
                ltp_buy = tick_size * round((ltp_)/tick_size)
                sl_buy = tick_size * round((ltp_buy - 20)/tick_size)

                placeGTTOrder(kite, ticker, "buy", quantity, sl_buy, ltp_buy,
                              exchange_type, trigger_id_gtt, product_type, ltp)
                pos_df = pd.DataFrame(kite.positions()["day"])

            # current candle is below , prev is also below and prev prev is above

        c4 = (len(pos_df.columns) != 0 and ticker in pos_df["tradingsymbol"].tolist()) and (
            pos_df[pos_df["tradingsymbol"] == ticker]["quantity"].values[0] != 0)

        if c4:
            # means already buy or sell in positions
            print("     Checking for sell      ")
            trigger_id = trigger_id_gtt[ticker]

            a = 0
            while a < 10:
                try:
                    pos_df = pd.DataFrame(kite.positions()["day"])
                    break
                except:
                    print("can't extract position data..retrying")
                    a += 1

            # if already buy
            # 2nd condition if sl hit then move out from loop
            while (pos_df[pos_df["tradingsymbol"] == ticker]["quantity"].values[0] != 0):
                a = 0
                while a < 10:
                    try:
                        ohlc_live = fetchOHLC(kite, instrument_df, ticker, minute_code, 30)
                        break
                    except:
                        print("can't extract ohlc data..retrying")
                        a += 1

                ohlc_live['psar'] = PSAR(ohlc_live)

                if len(ohlc_live) == (init_len + 1):
                    print("Breaking out -- {} ".format(time.asctime(time.localtime(time.time()))))
                    break
                if (pos_df[pos_df["tradingsymbol"] == ticker]["quantity"].values[0] > 0) and ((ohlc_live['high'][-1] < ohlc_live['psar'][-1]) and (ohlc_live['high'][-2] > ohlc_live['psar'][-2])):
                    placeMarketOrder(kite, ticker, "sell", quantity,
                                     exchange_type, product_type)

                    if trigger_id:
                        print("Deleting GTT")
                        kite.delete_gtt(trigger_id)

                    break
                a = 0
                while a < 10:
                    try:
                        pos_df = pd.DataFrame(kite.positions()["day"])
                        break
                    except:
                        print("can't extract position data..retrying")
                        a += 1

    except Exception:
        notify(error=True)
        notify(error=True)
        notify(error=True)
        print("API error for ticker :", ticker)
        print(traceback.format_exc())


starttime = time.time()
timeout = time.time() + 60*60*6  # 60 seconds times 360 meaning 6 hrs
while time.time() <= timeout:
    try:
        main()
        print("Sleeping for ", max(0, (60*minute - ((time.time() - starttime) % (60.0*minute)))))
        time.sleep(max(0, (60*minute - ((time.time() - starttime) % (60.0*minute)))))
    except KeyboardInterrupt:
        print('\n\nKeyboard exception received. Exiting.')
        import sys
        sys.exit()
