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


def statement_import(request, name_id):
    """
    Import all statement in folders
    :param request: request
    :param name_id: int
    :return: render
    """
    statement_name = StatementName.objects.get(id=name_id)
    logger.info('Statement Name: %s' % statement_name)
    logger.info('Import all statement in folder: %s' % statement_name.path)

    files = list()
    fpaths = glob.glob(os.path.join(STATEMENT_DIR, statement_name.path, '*.csv'))

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
        acc_index = lines.index('Account Summary')
        statement = Statement()
        statement.statement_name = statement_name
        statement.date = date
        statement.csv_data = codecs.open(fpath, encoding="ascii", errors="ignore").read()
        statement.load_csv(lines[acc_index + 1:acc_index + 5])
        statement.save()
        logger.info('[%s] Net liquid: %s' % (date, statement.net_liquid))

        # cash balance
        cash_balances = []
        cb_index = lines.index('Cash Balance')
        for line in lines[cb_index + 2:last_index(cb_index, lines) - 1]:
            values = line.split(',')
            if values[2]:  # go type
                cash_balance = CashBalance()
                cash_balance.statement = statement
                cash_balance.load_csv(line)
                # cash_balance.save()
                cash_balances.append(cash_balance)

        if len(cash_balances):
            CashBalance.objects.bulk_create(cash_balances)
            logger.info('[%s] Cash balance: %d' % (date, len(cash_balances)))

        # account order, more than 14 split
        account_orders = []
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
            df = pd.DataFrame(ao_lines, columns=lines[ao_index + 1].split(','))
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
                # account_order.save()
                account_orders.append(account_order)

            if len(account_orders):
                AccountOrder.objects.bulk_create(account_orders)
                logger.info('[%s] Account order: %d' % (date, len(account_orders)))

        # account trade
        account_trades = []
        at_index = lines.index('Account Trade History')
        at_lines = [line.split(',') for line in lines[at_index + 2:last_index(at_index, lines)]]
        if len(at_lines):
            df = pd.DataFrame(at_lines, columns=lines[at_index + 1].split(','))
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
                # account_trade.save()
                account_trades.append(account_trade)

            if len(account_trades):
                AccountTrade.objects.bulk_create(account_trades)
                logger.info('[%s] Account trade: %s' % (date, len(account_trades)))

        # holding equity
        holding_equities = []
        symbols = list()
        try:
            he_index = lines.index('Equities')

            for line in lines[he_index + 2:last_index(he_index, lines) - 1]:
                holding_equity = HoldingEquity()
                holding_equity.statement = statement
                holding_equity.load_csv(line)
                # holding_equity.save()
                holding_equities.append(holding_equity)

                symbols.append(holding_equity.symbol)

            if len(holding_equities):
                HoldingEquity.objects.bulk_create(holding_equities)
                logger.info('[%s] Holding equity: %d' % (date, len(holding_equities)))
        except ValueError:
            logger.info('[%s] Holding equity: %d' % (date, 0))

        # holding option
        try:
            ho_index = lines.index('Options')
            holding_options = []
            for line in lines[ho_index + 2:last_index(ho_index, lines) - 1]:
                holding_option = HoldingOption()
                holding_option.statement = statement
                holding_option.load_csv(line)
                # holding_option.save()
                holding_options.append(holding_option)

                symbols.append(holding_option.symbol)

            if len(holding_options):
                HoldingOption.objects.bulk_create(holding_options)
                logger.info('[%s] Holding options: %d' % (date, len(holding_options)))
        except ValueError:
            logger.info('[%s] Holding options: %d' % (date, 0))

        # profit loss
        profit_losses = []
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
                            # profit_loss.save()
                            profit_losses.append(profit_loss)

            if len(profit_losses):
                ProfitLoss.objects.bulk_create(profit_losses)
                logger.info('[%s] Profit loss: %d' % (date, len(profit_losses)))
        except ValueError:
            pass

        # done import statement, position trades
        statement.refresh_from_db()
        statement.reset_controller()

        # create positions
        statement.controller.add_relations()
        statement.controller.position_trades()
        statement.controller.position_expires()

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

    # template page
    template = 'statement/import.html'
    parameters = dict(
        title='Statement Import',
        files=files
    )

    return render(request, template, parameters)


class TruncateStatementForm(forms.Form):
    confirm = forms.BooleanField(
        widget=forms.HiddenInput(
            attrs={'class': 'form-control vTextField', 'readonly': 'readonly'}
        )
    )

    @staticmethod
    def truncate_data(statement_name):
        """
        Remove all data for single symbol
        :param statement_name: StatementName
        """
        Position.objects.filter(name=statement_name).all().delete()
        Statement.objects.filter(name=statement_name).all().delete()


def statement_truncate(request, name_id):
    """
    Truncate all statement data
    :param request: request
    :param name_id: int
    :return: render
    """
    statement_name = StatementName.objects.get(id=name_id)
    logger.info('%s' % statement_name)
    logger.info('Truncate all statements for: %s' % statement_name.path)

    stats = None
    if request.method == 'POST':
        form = TruncateStatementForm(request.POST)

        if form.is_valid():
            form.truncate_data(statement_name)
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
