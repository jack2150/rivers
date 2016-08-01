from research.strategy.trade.strangle.cs.strangle import create_order as strangle_create
from research.strategy.trade.strangle.cs.strangle import join_data as strangle_join


def create_order(df_signal, df_all,
                 side=('follow', 'reverse', 'buy', 'sell'),
                 cycle=0, strike=0):
    """

    :param df_signal:
    :param df_all:
    :param side:
    :param cycle:
    :param strike:
    :return:
    """
    return strangle_create(
        df_signal, df_all, side, cycle, strike, -strike
    )


def join_data(df_order, df_stock, df_all, df_iv):
    """

    :param df_order:
    :param df_stock:
    :param df_all:
    :param df_iv:
    :return:
    """
    return strangle_join(
        df_order, df_stock, df_all, df_iv
    )