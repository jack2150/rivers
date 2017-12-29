import json
import logging
import numpy as np
import pandas as pd
from bootstrap3_datetime.widgets import DateTimePicker
import datetime
from django import forms
from django.core.urlresolvers import reverse
from django.shortcuts import render, redirect
from opinion.group.option.models import OptionStat, OptionStatTimeSaleContract, \
    OptionStatTimeSaleTrade


logger = logging.getLogger('views')


class OptionTimeSaleForm(forms.Form):
    symbol = forms.CharField(widget=forms.TextInput(
        attrs={'class': 'form-control vTextField', 'readonly': 'readonly'}
    ))
    date = forms.DateField(
        widget=DateTimePicker(
            options={"format": "YYYY-MM-DD", "pickTime": False, 'readonly': 'readonly'}
        )
    )
    raw_data = forms.CharField(widget=forms.Textarea(
        attrs={'class': 'form-control vLargeTextField'}
    ))

    @staticmethod
    def buy_or_sell(mark, price):
        result = 'BUY/SELL'
        if mark > price:
            result = 'SELL'
        elif mark < price:
            result = 'BUY'

        return result

    def process(self):
        """
        Process input raw data into dataframe
        :return: str, pd.DataFrame
        """
        symbol = str(self.cleaned_data['symbol']).upper()
        date = pd.to_datetime(self.cleaned_data['date'])
        lines = self.cleaned_data['raw_data'].split('\n')

        data = []

        for l in lines:
            l = l.replace('--', '0').replace('%', '')

            d = str(l.strip()).split('\t')
            if len(d) == 9:
                d.append('')
            elif len(d) != 10:
                continue

            if len(d[0].split(' ')) == 2:
                d[0] = d[0].split(' ')[1]

            d[2] = d[2].replace(',', '')
            d[1] = d[1] + 'ALL' if d[1][-1] == 'C' else d[1] + 'UT'

            data.append(d)

        df_trade = pd.DataFrame(data, columns=[
            'time', 'option', 'qty', 'price', 'exchange', 'market',
            'delta', 'iv', 'underlying_price', 'condition'
        ])

        logger.info('df_timesale raw length: %d' % len(df_trade))

        df_trade['price'] = df_trade['price'].astype('float')
        df_trade['qty'] = df_trade['qty'].astype('int')
        df_trade['mark'] = df_trade['market'].apply(
            lambda x: np.mean([float(n) for n in x.split('x')])
        )
        df_trade['trade'] = df_trade.apply(lambda x: self.buy_or_sell(x['mark'], x['price']), axis=1)

        # option into field
        df_trade['ex_date'] = pd.to_datetime(df_trade['option'].apply(
            lambda x: datetime.datetime.strptime(' '.join(x.split(' ')[0:3]), '%d %b %y')
        ))
        df_trade['strike'] = df_trade['option'].apply(lambda x: x.split(' ')[-2]).astype('float')
        df_trade['name'] = df_trade['option'].apply(lambda x: x.split(' ')[-1])

        # market into bid/ask
        df_trade['bid'] = df_trade['market'].apply(lambda x: x.split('x')[0]).astype('float')
        df_trade['ask'] = df_trade['market'].apply(lambda x: x.split('x')[1]).astype('float')

        # round
        df_trade = df_trade.round({'price': 2, 'mark': 2, 'strike': 2, 'bid': 2, 'ask': 2})
        df_trade = df_trade.sort_values('qty')
        # ts(df)

        # group qty
        group = df_trade.groupby('option')
        df_sum = group.sum()
        df_mean = group.mean()
        df_first = group.first()

        df_contract = pd.concat([
            df_sum[['qty']], df_mean[['strike', 'bid', 'ask', 'price', 'mark']],
            df_first[['ex_date', 'name']]
        ], axis=1)  # with index
        """:type: pd.DataFrame"""
        logger.info('df_timesale report length: %d' % len(df_contract))
        df_contract = df_contract.reset_index()
        # df_timesale = df_timesale[df_timesale['trade'] != 'unknown']

        # df_result['symbol'] = symbol
        df_contract['date'] = date

        df_contract = df_contract[[
            'date', 'option', 'ex_date', 'strike', 'name', 'bid', 'ask', 'qty', 'price', 'mark'
        ]].reset_index(drop=True)
        df_contract = df_contract.round({'price': 2, 'mark': 2})
        """:type: pd.DataFrame"""
        # ts(df_timesale)

        return symbol, date, df_contract, df_trade


def timesale_create(request, obj_id):
    """
    Insert new option time & sale data and generate report

    :param request: request
    :param obj_id: int
    :return: render
    """
    option_stat = OptionStat.objects.get(id=obj_id)

    if request.method == 'POST':
        # create a form instance and populate it with data from the request:
        form = OptionTimeSaleForm(request.POST)

        if form.is_valid():
            symbol, date, df_contract, df_trade = form.process()

            option_stat.raw_data = form.cleaned_data['raw_data']
            option_stat.save()

            # reset
            option_stat.optionstattimesaletrade_set.all().delete()
            option_stat.optionstattimesalecontract_set.all().delete()

            # save contract
            ts_contracts = []
            for index, data in df_contract.sort_values('qty', ascending=False)[:10].iterrows():
                ts_contract = OptionStatTimeSaleContract(
                    option_stat=option_stat,
                    option=data['option'],
                    ex_date=data['ex_date'],
                    strike=data['strike'],
                    name=data['name'],
                    qty=data['qty'],
                    bid=data['bid'],
                    ask=data['ask'],
                    price=data['price'],
                    mark=data['mark'],
                )

                ts_contracts.append(ts_contract)

            OptionStatTimeSaleContract.objects.bulk_create(ts_contracts)

            # save trade
            ts_trades = []
            for index, data in df_trade.sort_values('qty', ascending=False)[:20].iterrows():
                ts_trade = OptionStatTimeSaleTrade(
                    option_stat=option_stat,
                    option=data['option'],
                    ex_date=data['ex_date'],
                    strike=data['strike'],
                    name=data['name'],
                    qty=data['qty'],
                    bid=data['bid'],
                    ask=data['ask'],
                    price=data['price'],
                    mark=data['mark'],

                    trade=data['trade'],
                    time=data['time'],
                    exchange=data['exchange'],
                    delta=data['delta'],
                    iv=data['iv'],
                    underlying_price=data['underlying_price'],
                    condition=data['condition'],
                )

                ts_trades.append(ts_trade)

            OptionStatTimeSaleTrade.objects.bulk_create(ts_trades)

            return redirect(reverse('timesale_report', kwargs={'obj_id': option_stat.id}))
    else:
        form = OptionTimeSaleForm(
            initial={
                'symbol': option_stat.report.symbol,
                'date': option_stat.date,
            }
        )

    title = 'Timesale create <%s> %s' % (option_stat.report.symbol, option_stat.date)
    template = 'opinion/option/timesale/create.html'
    parameters = dict(
        site_title=title,
        title=title,
        option_stat=option_stat,
        form=form
    )

    return render(request, template, parameters)


def timesale_report(request, obj_id):
    """
    Output option time & sale report for datatable view
    :param request: request
    :param obj_id: int
    :return: render
    """
    option_stat = OptionStat.objects.get(id=obj_id)

    ts_trades = option_stat.optionstattimesaletrade_set.order_by('qty').reverse()
    ts_contracts = option_stat.optionstattimesalecontract_set.order_by('qty').reverse()

    contracts = []
    for contract in ts_contracts.all():
        contracts.append({
            'option': contract.option,
            'ex_date': contract.ex_date.strftime('%Y-%m-%d'),
            'strike': '%.2f' % contract.strike,
            'name': contract.name,
            'qty': contract.qty,
            'bid': '%.2f' % contract.bid,
            'ask': '%.2f' % contract.ask,
            'price': '%.2f' % contract.price,
            'mark': '%.2f' % contract.mark,
            'buy': 'BUY +%d %s 100 %s @%.2f LMT' % (
                contract.qty,
                option_stat.report.symbol.upper(),
                contract.option,
                contract.price
            ),
            'sell': 'BUY +%d %s 100 %s @%.2f LMT' % (
                contract.qty,
                option_stat.report.symbol.upper(),
                contract.option,
                contract.price
            )
        })

    contracts = json.dumps(contracts)

    # trades
    qty_mod = {
        'BUY': '+', 'SELL': '-', 'BUY/SELL': '+-'
    }

    trades = []
    for trade in ts_trades.all():
        if trade.trade == 'SELL':
            margin = trade.price * trade.qty * 100 * 8
        else:
            margin = trade.price * trade.qty * 100

        trades.append({
            'time': trade.time.strftime('%H:%M:%S'),
            'option': trade.option,
            'ex_date': trade.ex_date.strftime('%Y-%m-%d'),
            'strike': '%.2f' % trade.strike,
            'name': trade.name,
            'trade': trade.trade,
            'qty': trade.qty,
            'bid': '%.2f' % trade.bid,
            'ask': '%.2f' % trade.ask,
            'price': '%.2f' % trade.price,
            'mark': '%.2f' % trade.mark,
            'exchange': trade.exchange,

            'delta': '%.2f' % trade.delta,
            'iv': '%.2f' % trade.iv,
            'underlying_price': '%.2f' % trade.underlying_price,
            'condition': trade.condition,
            'value': '%.0f' % (trade.price * trade.qty * 100),
            'margin': '%.0f' % margin,
            'fill': trade.fill.upper(),

            'order': '%s %s%d %s 100 %s @%.2f LMT' % (
                trade.trade.upper(),
                qty_mod[trade.trade],
                trade.qty,
                option_stat.report.symbol.upper(),
                trade.option,
                trade.price
            )
        })

    trades = json.dumps(trades)

    # template
    title = 'Timesale report <%s> %s' % (option_stat.report.symbol, option_stat.date)
    template = 'opinion/option/timesale/report.html'
    parameters = dict(
        site_title=title,
        title=title,
        option_stat=option_stat,
        contracts=contracts,
        trades=trades,
    )

    return render(request, template, parameters)


def report_option_stat(request, obj_id):
    """

    :param request:
    :param obj_id:
    :return:
    """
    option_stat = OptionStat.objects.get(id=obj_id)
    # option_stat.optionstatopeninterest_set

    # template
    title = 'Timesale report <%s> %s' % (option_stat.report.symbol, option_stat.date)
    template = 'opinion/option/report.html'
    parameters = dict(
        site_title=title,
        title=title,
        option_stat=option_stat,
    )

    return render(request, template, parameters)

# todo: this 1