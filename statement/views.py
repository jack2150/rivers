import glob
import os
import codecs
from django import forms
from django.core.urlresolvers import reverse
import numpy as np
from django.shortcuts import render, redirect
from rivers.settings import BASE_DIR
from statement.models import *


# use for import
statement_path = 'demo'


def statement_import(request):
    """
    Import all statement in folders
    :param request: request
    :return: render
    """
    template = 'statement/import.html'

    last_index = lambda x, y: [k for k, l in enumerate(y[x:], start=x) if l == ''][0]

    files = list()
    fpaths = glob.glob(os.path.join(BASE_DIR, 'files', 'statement', statement_path, '*.csv'))

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
        statement.controller.add_relations()
        statement.controller.position_trades()
        statement.controller.position_expires()

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
    stats = None
    if request.method == 'POST':
        form = TruncateStatementForm(request.POST)

        if form.is_valid():
            form.truncate_data()
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
