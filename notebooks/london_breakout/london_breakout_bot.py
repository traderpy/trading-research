import MetaTrader5 as mt5
import pandas as pd
from datetime import datetime, timedelta, time
from time import sleep
import pytz


def get_session_high_low():
    start_dt = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0, tzinfo=pytz.timezone('UTC'))
    end_dt = datetime.now().replace(hour=8, minute=0, second=0, microsecond=0, tzinfo=pytz.timezone('UTC'))

    rates = mt5.copy_rates_range('GBPJPY', mt5.TIMEFRAME_M15, start_dt, end_dt)
    rates_df = pd.DataFrame(rates)
    rates_df['time'] = pd.to_datetime(rates_df['time'], unit='s')
    print(rates_df)

    session_high = rates_df['high'].max()
    session_low = rates_df['low'].min()

    return session_high, session_low


def get_last_close():
    last_candle = mt5.copy_rates_from_pos('GBPJPY', mt5.TIMEFRAME_M15, 0, 1)
    return last_candle[0][1]


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
        "type_filling": mt5.ORDER_FILLING_IOC,
    }

    order_result = mt5.order_send(request)
    return (order_result)


def get_num_closed_trades_today():
    start_dt = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
    end_dt = datetime.now().replace(hour=23, minute=59, second=59, microsecond=0)

    deals = mt5.history_deals_get(start_dt, end_dt)

    if len(deals) == 0:
        return 0

    deals_df = pd.DataFrame(deals, columns=deals[0]._asdict().keys())
    closed_deals = deals_df[deals_df['entry'] == 1].reset_index()

    return closed_deals.shape[0]


if __name__ == '__main__':
    mt5.initialize(path=r'C:\Program Files\MetaTrader 5 IC Markets (SC)\terminal64.exe')
    mt5.login(11100246, 'ICMarketsSC-MT5-4')

    volume = 0.5

    while True:
        session_high, session_low = get_session_high_low()
        print(datetime.now())
        print('session high', session_high)
        print('session low', session_low)

        last_candle_open = get_last_close()
        print('last candle open', last_candle_open)
        print('---\n')

        stoploss = session_high - (session_high - session_low) / 2

        if datetime.now().time() >= time(16, 0, 0):
            close_all_positions('all')

        num_closed_positions = get_num_closed_trades_today()
        # security logic
        if mt5.positions_total() or num_closed_positions:
            sleep(1)
            continue

        if time(8, 0, 0) <= datetime.now().time() < time(12, 0, 0) and mt5.positions_total() == 0:
            if last_candle_open > session_high:
                market_order('GBPJPY', volume, 'buy', deviation=20, magic=15, stoploss=stoploss,
                             strategy_name='London Breakout')
            elif last_candle_open < session_low:
                market_order('GBPJPY', volume, 'sell', deviation=20, magic=15, stoploss=stoploss,
                             strategy_name='London Breakout')

        sleep(1)



