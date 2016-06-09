import codecs
import os
import re
import pandas as pd
from calendar import month_name
from base.ufunc import *


MONTHS = [month_name[m + 1][:3].upper() for m in range(12)]
SPECIAL = ['Weeklys', 'Mini', 'Quarterlys']
STOCK_COLUMN = 'Last,Net Chng,Volume,Open,High,Low'
STOCK_NAMES = [
    'last', 'net_change', 'volume', 'open', 'high', 'low'
]
OPTION_COLUMN = r',,Last,Mark,Delta,Gamma,Theta,Vega,Theo Price,Impl Vol,Prob.ITM,Prob.OTM,' \
                r'Prob.Touch,Volume,Open.Int,Intrinsic,Extrinsic,Option Code,Bid,Ask,Exp,' \
                r'Strike,Bid,Ask,Last,Mark,Delta,Gamma,Theta,Vega,Theo Price,Impl Vol,Prob.ITM,' \
                r'Prob.OTM,Prob.Touch,Volume,Open.Int,Intrinsic,Extrinsic,Option Code,,'
STRIKE_POS = 19
CALL_START, CALL_STOP = 0, 19
CALL_NAMES = [
    'last', 'mark', 'delta', 'gamma', 'theta', 'vega',
    'theo_price', 'impl_vol', 'prob_itm', 'prob_otm', 'prob_touch', 'volume',
    'open_int', 'intrinsic', 'extrinsic', 'option_code',
    'bid', 'ask'  # bid ask at back, with dte
]
PUT_START, PUT_STOP = 20, 40
PUT_NAMES = [
    'bid', 'ask',  # bid ask at front
    'last', 'mark', 'delta', 'gamma', 'theta', 'vega',
    'theo_price', 'impl_vol', 'prob_itm', 'prob_otm', 'prob_touch', 'volume',
    'open_int', 'intrinsic', 'extrinsic', 'option_code'  # with dte
]

CONTRACT_NAMES = [
    'option_code', 'name', 'strike', 'ex_date', 'right', 'special', 'others',
]

CONTRACT_KEYS = [
    'ex_month', 'ex_year', 'right', 'special', 'others',
    'strike', 'name', 'option_code'
]


class ThinkBack(object):
    def __init__(self, fpath):
        self.fpath = fpath
        self.fname = os.path.basename(self.fpath)
        self.date = pd.to_datetime(self.fname[:10])
        self.symbol = self.fname.split('-StockAndOptionQuoteFor').pop()[:-4]

        self.lines = [
            remove_comma(str(l.rstrip())) for l in
            codecs.open(fpath, encoding="ascii", errors="ignore").readlines()
        ]

    def get_stock(self):
        """
        Get stock data from csv line
        :return: dict
        """
        data = self.lines[self.lines.index(STOCK_COLUMN) + 1].split(',')
        stock = {k: float(v) for k, v in zip(STOCK_NAMES, data)}
        stock['date'] = self.date
        stock['volume'] = int(stock['volume'])

        return stock

    def get_cycles(self):
        """
        Get cycle in the top of each option chain
        weekly not more JAN1 or FEB2, direct 16 JAN 09
        :return: dict
        """
        cycles = []
        for key, line in enumerate(self.lines):
            items = line.split(' ')

            if len(items) < 4:
                continue

            if items[1] in MONTHS:
                items = [i for i in items if i]

                date = pd.datetime.strptime('-'.join(items[0:3]), '%d-%b-%y')
                dte = int(items[3][1:-1])
                right = items[4]  # in str format

                special = 'Standard'
                others = ''
                try:
                    temp = ' '.join(items[5:])
                    group = re.split(r'\(([^)]+)\)', temp)
                    group = [g.strip() for g in group if g not in ('', ' ')]

                    if len(group) == 1:
                        if group[0] in SPECIAL:
                            special = group[0]
                        elif 'US$' in group[0] or 'CDL' in group[0]:
                            others = group[0]
                        else:
                            raise LookupError('special/others not found for string: %s' % group[0])
                    elif len(group) == 2:
                        special = group[0]
                        others = group[1]
                        # print 'special: %s, others: %s' % (special, others)
                except IndexError:
                    pass  # no special and others

                cycles.append({
                    'start': key + 1,
                    'stop': 0,
                    'dte': dte,
                    'line': line,
                    'date': date,
                    'right': right,
                    'special': special,
                    'others': others
                })

        # add stop
        for c0, c1 in zip(cycles[:-1], cycles[1:]):
            c0['stop'] = c1['start'] - 2
        else:
            cycles[-1]['stop'] = len(self.lines)

        return cycles

    def get_cycle_options(self, cycle):
        """
        Test get cycle option from lines
        :param cycle: dict
        :return: list
        """
        lines = self.lines[cycle['start']:cycle['stop']]

        if lines[0] != OPTION_COLUMN:
            raise IOError('Invalid column format: %s' % self.fpath)

        options = []
        for line in lines[1:]:
            # line split to data
            data = line[2:-2].replace('%', '').split(',')

            # format data
            for i, d in enumerate(data):
                if d in ('', '--', '++', '<empty>'):
                    data[i] = '.0'

            # get strike
            strike = round(float(data[STRIKE_POS]), 2)

            # call/put options
            call_option = {k: v for k, v in zip(CALL_NAMES, data[CALL_START:CALL_STOP])}
            put_option = {k: v for k, v in zip(PUT_NAMES, data[PUT_START:PUT_STOP])}

            # set dte, date
            call_option['dte'] = cycle['dte']
            put_option['dte'] = cycle['dte']
            call_option['date'] = self.date
            put_option['date'] = self.date

            # format options
            for option in (call_option, put_option):
                for key, value in option.items():
                    if key == 'dte':
                        option[key] = int(value)
                    elif key not in ('date', 'option_code'):
                        option[key] = float(value)

            # call/put contracts
            call_contract = {
                'option_code': call_option['option_code'],
                'name': 'CALL',
                'strike': strike,
                'ex_date': cycle['date'],
                'right': cycle['right'],
                'special': cycle['special'],
                'others': cycle['others']
            }
            put_contract = {
                'option_code': put_option['option_code'],
                'name': 'PUT',
                'strike': strike,
                'ex_date': cycle['date'],
                'right': cycle['right'],
                'special': cycle['special'],
                'others': cycle['others']
            }

            # add into options
            options.append((call_contract, call_option))
            options.append((put_contract, put_option))

        return options

    def get_options(self):
        """
        Test get options for each cycles
        :return: list
        """
        cycles = self.get_cycles()

        options = []
        for cycle in cycles:
            options += self.get_cycle_options(cycle)

        return options
