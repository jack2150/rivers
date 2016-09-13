import logging
import glob
import os
import codecs
from django import forms
from django.core.urlresolvers import reverse
import numpy as np
from django.shortcuts import render, redirect
from rivers.settings import BASE_DIR, STATEMENT_DIR
from statement.models import *


# use for import
STATEMENT_PATH = 'real0'
STATEMENT_NAME = 'TD Ameritrade USA'
logger = logging.getLogger('views')


def last_index(x, y):
    """
    :param x: list
    :param y: list
    :return: int
    """
    return [k for k, l in enumerate(y[x:], start=x) if l == ''][0]


def get_value(x):
    """
    :param x: str
    :return: float
    """
    return float((x[1:-1] if '(' in x else x).replace('$', ''))


def statement_import(request):
    """
    Import all statement in folders
    :param request: request
    :return: render
    """
    logger.info('Import all statement in folder')
    template = 'statement/import.html'

    files = list()
    fpaths = glob.glob(os.path.join(STATEMENT_DIR, STATEMENT_PATH, '*.csv'))

    # for fpath in [f for f in fpaths if '05-11' in f]:
    for fpath in fpaths:  #
        logger.info(fpath)
        date = os.path.basename(fpath)[:10]

        # duplicate date
        if Statement.objects.filter(date=date).exists():
            logger.info('Statement import skip, date exists: %s' % date)
            continue  # skip below and next file
        else:
            logger.info('Statement date not exists, import: %s' % date)

        lines = [
            # remove_comma(str(re.sub('[\r\n]', '', line))) for line in  # replace dash
            remove_comma(str(line.rstrip())) for line in  # replace dash
            codecs.open(fpath, encoding="ascii", errors="ignore").readlines()
        ]

        # statement section
        logger.info('Statement obj section')
        acc_index = lines.index('Account Summary')
        statement = Statement()
        # statement.name = STATEMENT_NAME
        statement.date = date
        statement.csv_data = codecs.open(fpath, encoding="ascii", errors="ignore").read()
        statement.load_csv(lines[acc_index + 1:acc_index + 5])
        statement.save()
        logger.info('Statement obj end')

        # cash balance
        logger.info('Cash balance obj section')
        cb_index = lines.index('Cash Balance')
        for line in lines[cb_index + 2:last_index(cb_index, lines) - 1]:
            values = line.split(',')
            if values[2]:  # go type
                cash_balance = CashBalance()
                cash_balance.statement = statement
                cash_balance.load_csv(line)
                cash_balance.save()
        logger.info('Cash balance obj end')

        # account order, more than 14 split
        logger.info('Account order obj section')
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
            # df['Spread'] = df.apply(lambda x: np.nan if 'RE #' in x['Spread'] else x['Spread'], axis=1)
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
        logger.info('Account order obj end')

        # account trade
        logger.info('Account trade obj section')
        at_index = lines.index('Account Trade History')
        at_lines = [line.split(',') for line in lines[at_index + 2:last_index(at_index, lines)]]
        if len(at_lines):
            df = DataFrame(at_lines, columns=lines[at_index + 1].split(','))
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

        logger.info('Account trade obj end')

        # holding equity
        logger.info('Holding equity obj section')
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
            logger.info('No holding equity')
            pass
        logger.info('Holding equity obj end')

        # holding option
        logger.info('Holding options obj section')
        try:
            ho_index = lines.index('Options')
            for line in lines[ho_index + 2:last_index(ho_index, lines) - 1]:
                holding_option = HoldingOption()
                holding_option.statement = statement
                holding_option.load_csv(line)
                holding_option.save()

                symbols.append(holding_option.symbol)
        except ValueError:
            logger.info('No holding options')
        logger.info('Holding options obj end')

        # profit loss
        logger.info('Profit loss obj section')
        symbols = set(symbols)
        try:
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

                    if get_value(values[4]) or (get_value(values[6]) and get_value(values[7])):
                        profit_loss.load_csv(line)
                        profit_loss.save()
        except ValueError:
            pass
        logger.info('Profit loss obj end')

        # create positions
        statement.controller.add_relations()
        statement.controller.position_trades()
        statement.controller.position_expires()

        # todo: relation multi-days

        # append into files data
        files.append(dict(
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

    # Statement.objects.all().delete()

    return render(request, template, parameters)


class TruncateStatementForm(forms.Form):
    confirm = forms.BooleanField(
        widget=forms.HiddenInput(
            attrs={'class': 'form-control vTextField', 'readonly': 'readonly'}
        )
    )

    @staticmethod
    def truncate_data():
        """
        Remove all data for single symbol
        """
        Statement.objects.all().delete()
        Position.objects.all().delete()


def truncate_statement(request):
    """
    Truncate all statement data
    :param request: request
    :return: render
    """
    logger.info('Truncate all statements')
    stats = None
    if request.method == 'POST':
        form = TruncateStatementForm(request.POST)

        if form.is_valid():
            form.truncate_data()
            logger.info('All statements removed')
            return redirect(reverse('admin:app_list', args=('statement',)))
    else:
        form = TruncateStatementForm(
            initial={'confirm': True}
        )

        stats = dict()
        stats['statement'] = Statement.objects.count()

        try:
            stats['start_date'] = Statement.objects.order_by('date').first().date
            stats['stop_date'] = Statement.objects.order_by('date').last().date
        except AttributeError:
            stats['start_date'] = '...'
            stats['stop_date'] = '...'

        stats['position'] = Position.objects.count()
        stats['position_stage'] = PositionStage.objects.count()
        stats['profit_loss'] = ProfitLoss.objects.count()
        stats['account_order'] = AccountOrder.objects.count()
        stats['account_trade'] = AccountTrade.objects.count()
        stats['cash_balance'] = CashBalance.objects.count()
        stats['holding_equity'] = HoldingEquity.objects.count()
        stats['holding_option'] = HoldingOption.objects.count()

    # view
    template = 'statement/truncate.html'

    parameters = dict(
        site_title='Truncate statement',
        title='Truncate statement',
        form=form,
        stats=stats
    )

    return render(request, template, parameters)
