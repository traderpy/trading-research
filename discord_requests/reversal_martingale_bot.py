import MetaTrader5 as mt5
import pandas as pd
import time


# function to send a market order
def market_order(symbol, volume, order_type, deviation=20):
    tick = mt5.symbol_info_tick(symbol)

    order_dict = {'buy': 0, 'sell': 1}
    price_dict = {'buy': tick.ask, 'sell': tick.bid}

    request = {
        "action": mt5.TRADE_ACTION_DEAL,
        "symbol": symbol,
        "volume": volume,
        "type": order_dict[order_type],
        "price": price_dict[order_type],
        "deviation": deviation,
        "magic": 100,
        "comment": "python market order",
        "type_time": mt5.ORDER_TIME_GTC,
        "type_filling": mt5.ORDER_FILLING_IOC,
    }

    order_result = mt5.order_send(request)

    return order_result


def close_position(position, deviation=20, magic=15, strategy_name='Python Bot'):
    order_type_dict = {
        0: mt5.ORDER_TYPE_SELL,
        1: mt5.ORDER_TYPE_BUY
    }

    price_dict = {
        0: mt5.symbol_info_tick(position['symbol']).bid,
        1: mt5.symbol_info_tick(position['symbol']).ask
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


def close_all_positions(order_type):
    order_type_dict = {
        'buy': 0,
        'sell': 1
    }

    if mt5.positions_total() > 0:
        positions = mt5.positions_get()

        positions_df = pd.DataFrame(positions, columns=positions[0]._asdict().keys())

        if order_type != 'all':
            positions_df = positions_df[(positions_df['type'] == order_type_dict[order_type])]

        for i, position in positions_df.iterrows():
            order_result = close_position(position)

            print('order_result: ', order_result)


def get_positions():
    if mt5.positions_total():
        positions = mt5.positions_get()
        positions_df = pd.DataFrame(positions, columns=positions[0]._asdict().keys())

        return positions_df


if __name__ == '__main__':
    mt5.initialize()
    mt5.login()

    # enter ticket number of current open trade
    ticket = 102051939

    monitored_trade = mt5.positions_get(ticket=ticket)[0]

    trade_counter = 0
    max_trades = 3

    while trade_counter < max_trades:
        print(monitored_trade)

        # buy position
        if monitored_trade.type == 0:
            profit_in_points = monitored_trade.price_current - monitored_trade.price_open
        # sell position
        elif monitored_trade.type == 1:
            profit_in_points = monitored_trade.price_open - monitored_trade.price_current

        print(round(profit_in_points, 6) * 100000)

        # if profit of current position exceeds 80 pips
        if profit_in_points > 0.008:
            close_all_positions('all')
        # if loss of current positions exceeds 20 pips
        elif profit_in_points < -0.002:

            # reverse buy order
            if monitored_trade.type == 0:
                # reverse positions with double positions size
                res = market_order(monitored_trade.symbol, monitored_trade.volume * 2, 'sell')

                print(res)
                trade_counter += 1

                # updated new tracked trade
                new_ticket = res.order
                time.sleep(1)  # waiting for position to appear in positions
                monitored_trade = mt5.positions_get(ticket=new_ticket)[0]

            # reverse sell order
            elif monitored_trade.type == 1:
                # reverse positions with double positions size
                res = market_order(monitored_trade.symbol, monitored_trade.volume * 2, 'buy')

                print(res)
                trade_counter += 1

                # updated new tracked trade
                new_ticket = res.order
                time.sleep(1)  # waiting for position to appear in positions
                monitored_trade = mt5.positions_get(ticket=new_ticket)[0]

        time.sleep(1)
