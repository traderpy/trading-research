"""
Author: TraderPy
Link: https://www.youtube.com/channel/UC9xYCyyR_G3LIuJ_LlTiEVQ

Risk Disclaimer:
Trading the financial markets imposes a risk of financial loss.
TraderPy is not responsible for any financial losses that viewers suffer.
Content is educational only and does not serve as financial advice.
Information or material is provided ‘as is’ without any warranty.
"""

# Simple Moving Average Crossover Strategy

import MetaTrader5 as mt5  # install using 'pip install MetaTrader5'
import pandas as pd  # install using 'pip install pandas'
from datetime import datetime
import time


# function to send a market order
def market_order(symbol, volume, order_type, **kwargs):
    tick = mt5.symbol_info_tick(symbol)

    order_dict = {'buy': 0, 'sell': 1}
    price_dict = {'buy': tick.ask, 'sell': tick.bid}

    request = {
        "action": mt5.TRADE_ACTION_DEAL,
        "symbol": symbol,
        "volume": volume,
        "type": order_dict[order_type],
        "price": price_dict[order_type],
        "deviation": DEVIATION,
        "magic": 100,
        "comment": "python market order",
        "type_time": mt5.ORDER_TIME_GTC,
        "type_filling": mt5.ORDER_FILLING_IOC,
    }

    order_result = mt5.order_send(request)
    print(order_result)

    return order_result


# function to close an order base don ticket id
def close_order(ticket):
    positions = mt5.positions_get()

    for pos in positions:
        tick = mt5.symbol_info_tick(pos.symbol)
        type_dict = {0: 1, 1: 0}  # 0 represents buy, 1 represents sell - inverting order_type to close the position
        price_dict = {0: tick.ask, 1: tick.bid}

        if pos.ticket == ticket:
            request = {
                "action": mt5.TRADE_ACTION_DEAL,
                "position": pos.ticket,
                "symbol": pos.symbol,
                "volume": pos.volume,
                "type": type_dict[pos.type],
                "price": price_dict[pos.type],
                "deviation": DEVIATION,
                "magic": 100,
                "comment": "python close order",
                "type_time": mt5.ORDER_TIME_GTC,
                "type_filling": mt5.ORDER_FILLING_IOC,
            }

            order_result = mt5.order_send(request)
            print(order_result)

            return order_result

    return 'Ticket does not exist'


# function to get the exposure of a symbol
def get_exposure(symbol):
    positions = mt5.positions_get(symbol=symbol)
    if positions:
        pos_df = pd.DataFrame(positions, columns=positions[0]._asdict().keys())
        exposure = pos_df['volume'].sum()

        return exposure


# calculate sma
def get_sma(symbol, timeframe, sma_period):
    bars = mt5.copy_rates_from_pos(symbol, timeframe, 1, sma_period)
    bars_df = pd.DataFrame(bars)

    sma = bars_df.close.mean()

    return sma


if __name__ == '__main__':

    # strategy parameters
    SYMBOL = "EURUSD"
    VOLUME = 1.0
    TIMEFRAME = mt5.TIMEFRAME_M1
    FAST_SMA_PERIOD = 10
    SLOW_SMA_PERIOD = 100
    DEVIATION = 20

    mt5.initialize()

    while True:
        # calculating account exposure
        exposure = get_exposure(SYMBOL)

        # calculating sma
        fast_sma = get_sma(SYMBOL, TIMEFRAME, FAST_SMA_PERIOD)
        slow_sma = get_sma(SYMBOL, TIMEFRAME, SLOW_SMA_PERIOD)

        # trading logic
        if fast_sma > slow_sma:
            # if we have a BUY signal, close all short positions
            for pos in mt5.positions_get():
                if pos.type == 1:  # pos.type == 1 represent a sell order
                    close_order(pos.ticket)

            # if there are no open positions, open a new long position
            if not mt5.positions_total():
                market_order(SYMBOL, VOLUME, 'buy')

        elif fast_sma < slow_sma:
            # if we have a SELL signal, close all short positions
            for pos in mt5.positions_get():
                if pos.type == 0:  # pos.type == 0 represent a buy order
                    close_order(pos.ticket)

            # if there are no open positions, open a new short position
            if not mt5.positions_total():
                market_order(SYMBOL, VOLUME, 'sell')

        print('time: ', datetime.now())
        print('exposure: ', exposure)
        print('fast_sma: ', fast_sma)
        print('slow_sma: ', slow_sma)
        print('-------\n')

        # update every 1 second
        time.sleep(1)