"""
London Breakout Bot in MetaTrader5 on GBPJPY

Trading Rules:

1) Enter Trade if M15 candle breaks High or Low of Asian Session
2) Set SL in the middle of the asian range
3) Close Trades at the end of the EU session
"""

import MetaTrader5 as mt5
import pandas as pd
from datetime import datetime, timedelta, time
import pytz
from time import sleep


def get_session_high_low(symbol):
    start_dt = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0, tzinfo=pytz.timezone('UTC'))
    end_dt = datetime.now().replace(hour=8, minute=0, second=0, microsecond=0, tzinfo=pytz.timezone('UTC'))

    rates = mt5.copy_rates_range(symbol, mt5.TIMEFRAME_M15, start_dt, end_dt)
    rates_df = pd.DataFrame(rates)
    rates_df['time'] = pd.to_datetime(rates_df['time'], unit='s')

    session_high = rates_df['high'].max()
    session_low = rates_df['low'].min()

    return session_high, session_low


def get_current_candle_open(symbol):
    current_open = mt5.copy_rates_from_pos(symbol, mt5.TIMEFRAME_M15, 0, 1)
    return current_open[0][1]


def market_order(symbol, volume, order_type, deviation=20, magic=15, stoploss=0.0, strategy_name='London Breakout'):
    order_type_dict = {
        'buy': mt5.ORDER_TYPE_BUY,
        'sell': mt5.ORDER_TYPE_SELL
    }

    price_dict = {
        'buy': mt5.symbol_info_tick(symbol).ask,
        'sell': mt5.symbol_info_tick(symbol).bid
    }

    request = {
        "action": mt5.TRADE_ACTION_DEAL,
        "symbol": symbol,
        "volume": volume,  # FLOAT
        "type": order_type_dict[order_type],
        "price": price_dict[order_type],
        "sl": stoploss,  # FLOAT
        "tp": 0.0,  # FLOAT
        "deviation": deviation,  # INTERGER
        "magic": magic,  # INTERGER
        "comment": strategy_name,
        "type_time": mt5.ORDER_TIME_GTC,
        "type_filling": mt5.ORDER_FILLING_IOC,  # mt5.ORDER_FILLING_FOK
    }

    order_result = mt5.order_send(request)
    return (order_result)


def close_position(position, deviation=20, magic=15, symbol='GBPJPY', strategy_name='London Breakout'):
    order_type_dict = {
        0: mt5.ORDER_TYPE_SELL,
        1: mt5.ORDER_TYPE_BUY
    }

    price_dict = {
        0: mt5.symbol_info_tick(symbol).bid,
        1: mt5.symbol_info_tick(symbol).ask
    }

    request = {
        "action": mt5.TRADE_ACTION_DEAL,
        "position": position['ticket'],  # select the position you want to close
        "symbol": position['symbol'],
        "volume": position['volume'],  # FLOAT
        "type": order_type_dict[position['type']],
        "price": price_dict[position['type']],
        "deviation": deviation,  # INTERGER
        "magic": magic,  # INTERGER
        "comment": strategy_name,
        "type_time": mt5.ORDER_TIME_GTC,
        "type_filling": mt5.ORDER_FILLING_IOC,
    }

    order_result = mt5.order_send(request)
    return (order_result)


def close_all_positions(order_type, magic=15):
    order_type_dict = {
        'buy': 0,
        'sell': 1
    }

    if mt5.positions_total() > 0:
        positions = mt5.positions_get()

        positions_df = pd.DataFrame(positions, columns=positions[0]._asdict().keys())
        positions_df = positions_df[positions_df['magic'] == magic]

        if order_type != 'all':
            positions_df = positions_df[(positions_df['type'] == order_type_dict[order_type])]

        for i, position in positions_df.iterrows():
            order_result = close_position(position)

            print('order_result: ', order_result)


# Trading Account Link in Youtube Description - Sign Up at ICMarkets https://icmarkets.com/?camp=60457
login = 123
password = 'password'
server = 'ICMarkets-Server'

# initialize and login to MT5
mt5.initialize()
# mt5.login(login, password, server)  # disregard if you are already logged in to the initialized platform


# Trading Logic
symbol = 'GBPJPY'
volume = 0.01

while True:
    # Trade Entry Logic
    session_high, session_low = get_session_high_low(symbol)
    print('session high', session_high)
    print('session_low', session_low)

    current_open = get_current_candle_open(symbol)
    print('current open', current_open)

    stoploss = session_high - (session_high - session_low) / 2

    if time(8, 0, 0) <= datetime.now().time() < time(12, 0, 0) and mt5.positions_total() == 0:
        if current_open > session_high:
            market_order(symbol, volume, 'buy', deviation=20, magic=15, stoploss=stoploss,
                         strategy_name='London Breakout')

        elif current_open < session_low:
            market_order(symbol, volume, 'sell', deviation=20, magic=15, stoploss=stoploss,
                         strategy_name='London Breakout')

    # Trade Exit Logic
    if datetime.now().time() >= time(16, 0, 0):
        close_all_positions('all')

    # Check Trading signals every second
    sleep(1)
