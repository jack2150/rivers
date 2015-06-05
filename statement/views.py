import glob
import os
import codecs
import re
import numpy as np
from django.shortcuts import render
from rivers.settings import BASE_DIR
from statement.models import *


def statement_import(request):
    """
    Import all statement in folders
    :param request: request
    :return: render
    """
    template = 'statement/import.html'

    last_index = lambda x, y: [k for k, l in enumerate(y[x:], start=x) if l == ''][0]

    files = list()
    fpaths = glob.glob(os.path.join(BASE_DIR, 'files', 'statements', 'tests', '*.csv'))

    #for fpath in [f for f in fpaths if '05-11' in f]:
    for fpath in fpaths:  #
        date = os.path.basename(fpath)[:10]

        # duplicate date
        if Statement.objects.filter(date=date).exists():
            continue  # skip below and next file
        #else:
        #    print 'saving statement: ', fpath

        lines = [
            #remove_comma(str(re.sub('[\r\n]', '', line))) for line in  # replace dash
            remove_comma(str(line.rstrip())) for line in  # replace dash
            codecs.open(fpath, encoding="ascii", errors="ignore").readlines()
        ]

        # statement section
        acc_index = lines.index('Account Summary')
        statement = Statement()
        statement.date = date
        statement.csv_data = codecs.open(fpath, encoding="ascii", errors="ignore").read()
        statement.load_csv(lines[acc_index + 1:acc_index + 5])
        statement.save()

        # cash balance
        cb_index = lines.index('Cash Balance')
        for line in lines[cb_index + 2:last_index(cb_index, lines) - 1]:
            values = line.split(',')
            if values[2]:  # go type
                cash_balance = CashBalance()
                cash_balance.statement = statement
                cash_balance.load_csv(line)
                cash_balance.save()

        # account order, more than 14 split
        ao_index = lines.index('Account Order History')
        ao_lines = list()
        for key, line in enumerate(lines[ao_index + 2:last_index(ao_index, lines)]):
            if len(line.split(',')) >= 14:
                values = line.split(',')

                if 'REJECTED' in values[14]:
                    values[14] = 'REJECTED'

                values = values[:15]
                ao_lines.append(values)

        if len(ao_lines):
            df = DataFrame(ao_lines, columns=lines[ao_index + 1].split(','))
            #df['Spread'] = df.apply(lambda x: np.nan if 'RE #' in x['Spread'] else x['Spread'], axis=1)
            df = df.replace('', np.nan).fillna(method='pad')  # fill empty
            df['Exp'] = df.apply(
                lambda x: np.nan if 'STOCK' in (x['Spread'], x['Type']) else x['Exp'], axis=1
            )
            df['Strike'] = df.apply(
                lambda x: np.nan if 'STOCK' in (x['Spread'], x['Type']) else x['Strike'], axis=1
            )
            df = df[df.apply(lambda x: False if '/' in x['Symbol'] else True, axis=1)]  # no future forex

            ao_lines = df.drop(df.columns[0], axis=1).to_csv().split('\n')[1:-1]  # back into csv lines

            for line in ao_lines:
                account_order = AccountOrder()
                account_order.statement = statement
                account_order.load_csv(line)
                account_order.save()

        # account trade
        at_index = lines.index('Account Trade History')
        at_lines = [line.split(',') for line in lines[at_index + 2:last_index(at_index, lines)]]
        if len(at_lines):
            df = DataFrame(at_lines, columns=lines[at_index+1].split(','))
            df = df.replace('', np.nan).replace('DEBIT', np.nan).fillna(method='pad')  # remove debit
            df['Exp'] = df.apply(
                lambda x: np.nan if 'STOCK' in (x['Spread'], x['Type']) else x['Exp'], axis=1
            )
            df['Strike'] = df.apply(
                lambda x: np.nan if 'STOCK' in (x['Spread'], x['Type']) else x['Strike'], axis=1
            )

            for symbol in df['Symbol'].unique():  # remove credit
                df_symbol = df[df['Symbol'] == symbol]
                net_price = float(df_symbol.loc[df_symbol.index.values[0], 'Net Price'])

                if len(df_symbol[df_symbol['Net Price'] == 'CREDIT']):
                    df.loc[df['Symbol'] == symbol, 'Net Price'] = net_price * -1

            # drop future and forex
            df = df[df.apply(lambda x: False if '/' in x['Symbol'] else True, axis=1)]
            at_lines = df.drop('', 1).to_csv().split('\n')[1:-1]  # back into csv lines

            for line in at_lines:
                account_trade = AccountTrade()
                account_trade.statement = statement
                account_trade.load_csv(line)
                account_trade.save()

        # holding equity
        symbols = list()
        try:
            he_index = lines.index('Equities')

            for line in lines[he_index + 2:last_index(he_index, lines) - 1]:
                holding_equity = HoldingEquity()
                holding_equity.statement = statement
                holding_equity.load_csv(line)
                holding_equity.save()

                symbols.append(holding_equity.symbol)
        except ValueError:
            pass

        # holding option
        try:
            ho_index = lines.index('Options')
            for line in lines[ho_index + 2:last_index(ho_index, lines) - 1]:
                holding_option = HoldingOption()
                holding_option.statement = statement
                holding_option.load_csv(line)
                holding_option.save()

                symbols.append(holding_option.symbol)
        except ValueError:
            pass

        # profit loss
        # df = DataFrame()
        symbols = set(symbols)
        pl_index = lines.index('Profits and Losses')
        for line in lines[pl_index + 2:last_index(pl_index, lines) - 1]:
            values = line.split(',')
            if '/' not in values[0]:  # skip future
                profit_loss = ProfitLoss()
                profit_loss.statement = statement
                if values[0] in symbols:  # symbol in holdings
                    profit_loss.load_csv(line)
                    profit_loss.save()
                elif len(values[0]):
                    f = lambda x: float((x[1:-1] if '(' in x else x).replace('$', ''))
                    if f(values[4]) or (f(values[6]) and f(values[7])):
                        profit_loss.load_csv(line)
                        profit_loss.save()

        # create positions
        #statement.controller.add_relations()
        #statement.controller.position_trades()
        #statement.controller.position_expires()

        files.append(dict(
            #path=fpath,
            # date=date,
            fname=os.path.basename(fpath),
            net_liquid=statement.net_liquid,
            stock_bp=statement.stock_bp,
            option_bp=statement.option_bp,
            commission_ytd=statement.commission_ytd,
            cash_balance=statement.cashbalance_set.count(),
            account_order=statement.accountorder_set.count(),
            account_trade=statement.accounttrade_set.count(),
            holding_equity=statement.holdingequity_set.count(),
            holding_option=statement.holdingoption_set.count(),
            profit_loss=statement.profitloss_set.count(),
        ))

    parameters = dict(
        title='Statement Import',
        files=files
    )

    #Statement.objects.all().delete()

    return render(request, template, parameters)


def position_spreads(request, date):
    """
    Import all statement in folders
    :param request: request
    :return: render
    """
    template = 'statement/position/spreads.html'

    if date:
        statement = Statement.objects.get(date=date)
        """:type: Statement"""
    else:
        statement = Statement.objects.order_by('date').last()
        """:type: Statement"""

    positions = Position.objects.filter(
        id__in=[p[0] for p in statement.profitloss_set.values_list('position')]
    ).order_by('symbol')

    spreads = list()
    for position in positions:
        spreads.append(dict(
            position=position,
            profit_loss=position.profitloss_set.get(statement__date=date),
        ))

    # todo: no price on option spread, do data first

    parameters = dict(
        title='Position Spreads',
        spreads=spreads
    )

    return render(request, template, parameters)