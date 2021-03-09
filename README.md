# Python-Algo-Trading-Zerodha
This repo contains sample templates for implementing strategies in python. 

I have used Zerodha's kiteconnect api for developing sample strategies.

## Zerodha kiteconnect
Here are some important links that you may need to go through to understand the login and other related stuff.

1. [KiteConnect API Doc](https://kite.trade/docs/connect/v3/)
2. [KiteConnect Python Doc](https://kite.trade/docs/pykiteconnect/v3/)
3. [KiteConnect github page](https://github.com/zerodhatech/pykiteconnect)
4. [KiteConnect developer login](https://developers.kite.trade/login)
5. [KiteConnect developer forum](https://kite.trade/forum/)

## Install dependencies

``` pip install -r requirements.txt ```

## Automate the login process

### For first time run

1. ```pip install selenium```
2. Download the correct webdriver from [here](https://pypi.org/project/selenium/) and place the .exe file in the directory having ```access_token.py```
3. Create api_key.txt file with the following info - 
    * API KEY - Obtained from the trading app in your developer account.
    * API SECRET - Obtained from the trading app in your developer account.
    * USER ID - Zerodha Kite user id.
    * PASSWORD - Zerodha Kite password.
    * PIN - Zerodha Kite pin.

#### ```python access_token.py```

## Strategy
Buy when PSAR crosses below candle and sell when PSAR crosses above candle.
The code for the same is in ```strategy_PSAR.py``` and other utility functions are in ```utils.py```

## Daily Usage

It is recommended to change the global variables in ```strategy_PSAR.py``` as per the new startegy. Also run the ```strategy_PSAR.py``` a minute later than candle start( if working with larger duration candles like 15minutes or bigger). For ex. if you want to start at 9:15 AM run the code at 9:16 AM to avoid some signals being missed.

1. run ```python access_token.py```
2. run ```strategy_PSAR.py```

## NOTE_1 -  This is just a sample strategy to get started with kiteconnect and zerodha. It is always recommended to use one's own strategy for best results.
## NOTE_2 - For coding technical indicators use [pandas-ta](https://github.com/twopirllc/pandas-ta) and NOT [TA-Lib](https://www.google.com/url?sa=t&rct=j&q=&esrc=s&source=web&cd=&cad=rja&uact=8&ved=2ahUKEwjrjfvJo6PvAhWO4XMBHUdlAf0QFjAAegQIAhAD&url=https%3A%2F%2Fpypi.org%2Fproject%2FTA-Lib%2F&usg=AOvVaw2pqi0Y5nrF2nJuDzzPky1D). TA-Lib gave wrong PSAR values many times during PSAR reversals.