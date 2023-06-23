import MetaTrader5 as mt5
import pandas as pd


def get_ohlc(symbol, timeframe, start, end):
    bars = mt5.copy_rates_range(symbol, timeframe, start, end)
    bars_df = pd.DataFrame(bars)
    bars['time'] = pd.to_datetime(bars_df)
    return bars_df


def get_ticks(symbol, start, end):
    bars = mt5.copy_ticks_range(symbol, start, end, mt5.COPY_TICKS_ALL)
    tick_df = pd.DataFrame(bars)
    tick_df['time'] = pd.to_datetime(tick_df)
    return tick_df
