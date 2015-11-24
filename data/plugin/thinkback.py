from calendar import month_name
import codecs
import os
import re
from base.ufunc import *


class ThinkBack(object):
    STOCK_KEYS = ['date', 'last', 'net_change', 'volume', 'open', 'high', 'low']
    STOCK_HEAD = 'Last,Net Chng,Volume,Open,High,Low'

    COLUMN_HEAD = r',,Last,Mark,Delta,Gamma,Theta,Vega,Theo Price,Impl Vol,Prob.ITM,Prob.OTM,' \
                  r'Prob.Touch,Volume,Open.Int,Intrinsic,Extrinsic,Option Code,Bid,Ask,Exp,' \
                  r'Strike,Bid,Ask,Last,Mark,Delta,Gamma,Theta,Vega,Theo Price,Impl Vol,Prob.ITM,' \
                  r'Prob.OTM,Prob.Touch,Volume,Open.Int,Intrinsic,Extrinsic,Option Code,,'

    CONTRACT_KEYS = ['ex_month', 'ex_year', 'right', 'special', 'others',
                     'strike', 'name', 'option_code']

    OPTION_KEYS = ['date', 'dte',
                   'bid', 'ask', 'last', 'mark', 'delta', 'gamma', 'theta', 'vega',
                   'theo_price', 'impl_vol', 'prob_itm', 'prob_otm', 'prob_touch', 'volume',
                   'open_int', 'intrinsic', 'extrinsic']

    def __init__(self, fpath):
        self.fpath = fpath

        self.fname = os.path.basename(self.fpath)

        self.date = self.fname[:10]
        self.symbol = self.fname.split('-StockAndOptionQuoteFor').pop()[:-4]

        self.lines = [
            remove_comma(str(l.rstrip())) for l in
            codecs.open(fpath, encoding="ascii", errors="ignore").readlines()
        ]

    def get_stock(self):
        """
        Get stock csv line in file
        :return: str
        """
        return make_dict(
            self.STOCK_KEYS,
            [self.date] + self.lines[self.lines.index(self.STOCK_HEAD) + 1].split(',')
        )

    def get_cycles(self):
        """
        Get option cycle from data
        :return: list
        """
        cycles = list()
        months = [month_name[i + 1][:3].upper() for i in range(12)]

        for key, line in enumerate(self.lines):
            if line[:3] in months:
                # JAN 09  (14)  100 (CDL 7; US$ 4.06)
                # JAN 09  (11)  19/100 (US$ 3601.92)
                # JAN 15  (444)  150 (DDD 150)
                try:
                    others = ''
                    open_bracket = line.rindex('(')
                    close_bracket = line.rindex(')')

                    if close_bracket == len(line) - 1:
                        if any([x for x in ['CDL', 'US$'] if x in line]):
                            others = line[open_bracket + 1: close_bracket]
                            line = line[:open_bracket]
                        elif line.count('(') == 2:
                            others = line[line.rindex('(') + 1:line.rindex(')')]
                            if others in ('Weeklys', 'Mini', 'Quarterlys'):
                                others = ''
                            else:
                                line = line[:open_bracket]

                except ValueError:
                    others = ''

                # get cycle data from line
                data = map(remove_bracket, [l for l in line.split(' ') if l])

                if len(data) == 4:
                    data.append('Standard')

                data = [int(i) if 0 < k < 3 else i for k, i in enumerate(data)]
                dte = data.pop(2)
                data += [others]

                # if not expire yet, add into cycle
                if dte > -1:
                    cycles.append(
                        dict(line=line, data=data, dte=dte, start=key + 1, stop=0)
                    )

                # previous stop
                if len(cycles) > 1:
                    cycles[len(cycles) - 2]['stop'] = key - 1
        else:
            if len(self.lines[-1]):
                cycles[len(cycles) - 1]['stop'] = len(self.lines)
            else:
                cycles[len(cycles) - 1]['stop'] = len(self.lines) - 1

        return cycles

    def get_cycle_options(self, cycle):
        """
        Get options from csv files
        :param cycle: dict
        :return: list of dict
        """
        if self.lines[cycle['start']] != self.COLUMN_HEAD:
            raise IOError('File have a invalid column format.')

        options = list()
        for line in self.lines[cycle['start'] + 1:cycle['stop']]:
            data = [(0 if v in ('', '--', '++') else v)
                    for v in line[2:-2].replace('%', '').split(',')]

            """Bid,Ask,Exp,Strike,Bid,Ask"""
            call_contract = make_dict(
                self.CONTRACT_KEYS, cycle['data'] + [float(data[19]), 'CALL', data[15].strip()]
            )
            call_option = make_dict(
                self.OPTION_KEYS, [self.date, cycle['dte']] + map(float, data[16:18] + data[:15])
            )

            put_contract = make_dict(
                self.CONTRACT_KEYS, cycle['data'] + [float(data[19]), 'PUT', data[37].strip()]
            )
            put_option = make_dict(
                self.OPTION_KEYS, [self.date, cycle['dte']] + map(float, data[20:37])
            )

            options.append((call_contract, call_option))
            options.append((put_contract, put_option))

        return options

    def read(self):
        """
        Format the data then output dict that ready for insert
        :return: tuple (dict, list of dict)
        """
        options = list()
        for c in self.get_cycles():
            options += self.get_cycle_options(c)

        return self.get_stock(), options

# todo: fill missing options using quant lib
"""
how do you access stock.last?
from hdf5 get data using symbol and date,
then create instance of Stock using that data (without save)

how do you search data?
in Stock class, create a search...
"""