import glob
import os
import codecs
import re
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

    for fpath in fpaths:  # [f for f in fpaths if '04-24' in f]:
        date = os.path.basename(fpath)[:10]

        # duplicate date
        if Statement.objects.filter(date=date).exists():
            continue  # skip below and next file
        else:
            # print 'run: ', fpath
            files.append(dict(
                path=fpath,
                fname=os.path.basename(fpath),
                date=date
            ))

        lines = [
            str(re.sub('[\r\n]', '', line)) for line in
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
        for line in lines[cb_index + 2:last_index(cb_index, lines) - 2]:
            cash_balance = CashBalance()
            cash_balance.statement = statement
            cash_balance.load_csv(line)
            cash_balance.save()

        # account order
        ao_index = lines.index('Account Order History')
        last = list()
        for line in lines[ao_index + 2:last_index(ao_index, lines)]:
            values = line.split(',')

            try:
                # skip future and forex
                if values[7] and values[3] not in ('FUTURE', 'FOREX') and values[11] != '':
                    if values[2] == '':  # no time in row
                        for i in range(len(values)):
                            if values[i] == '':
                                values[i] = last[i]
                        else:
                            if 'RE #' in values[3]:  # skip re
                                values[3] = last[3]

                            if values[10] == 'STOCK':  # stock no exp and strike
                                values[8] = ''
                                values[9] = ''

                    account_order = AccountOrder()
                    account_order.statement = statement
                    account_order.load_csv(','.join(values))
                    account_order.save()

                    last = values
            except IndexError:
                pass

        # account trade
        at_index = lines.index('Account Trade History')
        last = list()
        for line in lines[at_index + 2:last_index(at_index, lines)]:
            values = line.split(',')

            if values[2] not in ('FUTURE', 'FOREX'):  # skip future and forex
                if values[1] == '':
                    for i in range(len(values)):
                        if values[i] == '' or values[i] in ('DEBIT', 'CREDIT'):
                            values[i] = last[i]
                    else:
                        if values[9] == 'STOCK':  # stock no exp and strike
                            values[7] = ''
                            values[8] = ''

                account_trade = AccountTrade()
                account_trade.statement = statement
                account_trade.load_csv(','.join(values))
                account_trade.save()

                last = values

        # holding equity
        try:
            he_index = lines.index('Equities')

            for line in lines[he_index + 2:last_index(he_index, lines) - 1]:
                holding_equity = HoldingEquity()
                holding_equity.statement = statement
                holding_equity.load_csv(line)
                holding_equity.save()
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
        except ValueError:
            pass

        # profit loss
        # df = DataFrame()
        pl_index = lines.index('Profits and Losses ')
        for line in lines[pl_index + 2:last_index(pl_index, lines) - 1]:
            values = line.split(',')
            if '/' not in values[0]:  # skip future
                if values[0] and values[6] and values[7]:  # only have margin req and close value
                    profit_loss = ProfitLoss()
                    profit_loss.statement = statement
                    profit_loss.load_csv(line)
                    profit_loss.save()

                    #df = df.append(profit_loss.to_hdf())

                    #print df.to_string(line_width=200)

    parameters = dict(
        files=files
    )

    return render(request, template, parameters)

    # todo: back into django 1.6