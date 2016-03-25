import numpy as np
from pandas_datareader.data import get_data_google, get_data_yahoo
from opinion.models import *
from datetime import datetime
from data.models import Underlying
from django import forms
from django.core.urlresolvers import reverse
from django.shortcuts import render, redirect
from django.core.paginator import Paginator
from data.tb.raw.options import get_dte_date2
from data.web.views import web_stock_h5
from rivers.settings import QUOTE
from statement.models import *
from pandas import Series


def date_page(dates, date, link, values):
    """
    A method use for paginator for both
    position spread and position report
    :param dates: list of str
    :param date: str
    :param link: str
    :param values: dict
    :return: dict
    """
    p = Paginator(dates, 1)
    page = p.page(dates.index(date) + 1)
    next_date = p.page(dates.index(date) + 2).object_list[0] if page.has_next() else None
    previous_date = p.page(dates.index(date)).object_list[0] if page.has_previous() else None

    values['date'] = p.page(1).object_list[0]
    first_page = reverse(link, kwargs=values)
    values['date'] = p.page(len(dates)).object_list[0]
    last_page = reverse(link, kwargs=values)

    next_page = '#'
    if next_date:
        values['date'] = next_date
        next_page = reverse(link, kwargs=values)

    previous_page = '#'
    if previous_date:
        values['date'] = previous_date
        previous_page = reverse(link, kwargs=values)

    return {
        'next_page': next_page,
        'previous_page': previous_page,
        'first_page': first_page,
        'last_page': last_page
    }


def position_spreads(request, date):
    """
    Position spread view
    :param request: request
    :param date: str
    :return: render
    """
    if date:
        date = pd.datetime.strptime(date, '%Y-%m-%d')

        statement = Statement.objects.get(date=date.date())
        """:type: Statement"""
    else:
        statement = Statement.objects.order_by('date').last()
        """:type: Statement"""

    positions = Position.objects.filter(
        id__in=[p[0] for p in statement.profitloss_set.values_list('position')]
    ).order_by('symbol')

    spreads = list()
    for position in positions:
        if position.status != 'OPEN' and date.date() >= position.stop:
            stage = position.status
        else:
            if position.name == 'STOCK':
                try:
                    stage = position.current_stage(
                        position.holdingequity_set.get(statement__date=date).close_price
                    )
                except ObjectDoesNotExist:
                    stage = 'Close'
            elif position.name == 'CUSTOM':
                stage = '...'
            else:
                try:
                    stage = position.current_stage(
                        Underlying.get_price(position.symbol, date.date())['close']
                    )
                except (ObjectDoesNotExist, TypeError, IndexError):
                    stage = '...'

        opinion = dict(exists=False, condition='UNKNOWN', action='HOLD', name='')
        holding_opinion = position.holdingopinion_set.filter(date=date)
        if holding_opinion.exists():
            holding_opinion = holding_opinion.first()
            opinion['name'] = 'hold'
            opinion['exists'] = True
            opinion['condition'] = holding_opinion.condition
            opinion['action'] = holding_opinion.action

        exit_opinion = position.exitopinion_set.filter(date=date)
        if exit_opinion.exists():
            opinion['name'] = 'exit'
            opinion['exists'] = True
            opinion['action'] = 'CLOSE'

        spreads.append(dict(
            position=position,
            profit_loss=position.profitloss_set.get(statement__date=date.date()),
            opinion=opinion,
            stage=stage,
        ))

    # paginator
    dates = [s['date'].strftime('%Y-%m-%d') for s in
             Statement.objects.all().order_by('date').values('date')]

    template = 'statement/position/spreads.html'
    parameters = dict(
        site_title='Position Spreads',
        title='Spreads',
        spreads=spreads,
        date=date.date(),
        page=date_page(dates, date.strftime('%Y-%m-%d'), 'admin:position_spreads', {})
    )

    return render(request, template, parameters)


# noinspection PyShadowingBuiltins
def create_opinion(request, opinion, id, date):
    """
    Get existing or create new holding opinion
    :param request: request
    :param opinion: str
    :param id: int
    :param date: str
    :return: render
    """
    position = Position.objects.get(id=id)

    if opinion == 'hold':
        try:
            # exists open it
            holding_opinion = HoldingOpinion.objects.get(Q(position=position) & Q(date=date))
            link = reverse('admin:checklist_holdingopinion_change', args=(holding_opinion.id,))
        except ObjectDoesNotExist:
            # not exists create new
            holding_opinion = HoldingOpinion()
            holding_opinion.position = position
            holding_opinion.date = date
            holding_opinion.save()
            link = reverse('admin:checklist_holdingopinion_change', args=(holding_opinion.id,))
    elif opinion == 'exit':
        try:
            exit_opinion = CloseOpinion.objects.get(Q(position=position) & Q(date=date))
            link = reverse('admin:checklist_exitopinion_change', args=(exit_opinion.id,))
        except ObjectDoesNotExist:
            exit_opinion = CloseOpinion()
            exit_opinion.position = position
            exit_opinion.date = date
            exit_opinion.save()
            link = reverse('admin:checklist_exitopinion_change', args=(exit_opinion.id,))
    else:
        raise ValueError('Invalid url argument opinion.')

    return redirect(link)


class BlindPositionForm(forms.Form):
    position = forms.IntegerField(widget=forms.HiddenInput)
    strategy_result = forms.IntegerField()

    def clean(self):
        pos_id = self.cleaned_data['position']
        sr_id = self.cleaned_data['strategy_result']

        position = None
        try:
            position = Position.objects.get(id=int(pos_id))
        except ObjectDoesNotExist:
            self._errors['position'] = self.error_class(
                ['Position id: {id} not found.'.format(id=pos_id)]
            )

        strategy_result = None
        try:
            strategy_result = StrategyResult.objects.get(id=int(sr_id))
        except ObjectDoesNotExist:
            self._errors['strategy_result'] = self.error_class(
                ['Strategy result id: {id} not found.'.format(id=sr_id)]
            )

        # make sure both are same symbol
        if position and strategy_result:
            if position.symbol != strategy_result.symbol:
                self._errors['position'] = self.error_class(
                    ['Different symbol {symbol0} and {symbol1}'.format(
                        symbol0=position.symbol,
                        symbol1=strategy_result.symbol
                    )]
                )

        return self.cleaned_data


# noinspection PyShadowingBuiltins
def blind_strategy(request, id):
    """
    A position can be blind into a strategy result for anlaysis
    :param request:
    :param id: int
    :return: render
    """
    position = Position.objects.get(id=id)
    account_trades = position.accounttrade_set.filter(pos_effect='TO OPEN')
    strategy_results = StrategyResult.objects.filter(symbol=position.symbol)

    if strategy_results.exists():
        strategy_results = strategy_results.order_by('id').reverse()

    if request.method == 'POST':
        # create a form instance and populate it with data from the request:
        form = BlindPositionForm(request.POST)

        if form.is_valid():
            position_id = form.cleaned_data['position']
            strategy_result_id = form.cleaned_data['strategy_result']
            strategy_result = StrategyResult.objects.get(id=strategy_result_id)

            position = Position.objects.get(id=position_id)
            position.strategy_result = strategy_result
            position.save()

            return redirect(reverse(
                'admin:position_report',
                kwargs={'id': position.id, 'date': position.start.strftime('%Y-%m-%d')}
            ))
    else:
        form = BlindPositionForm(initial={
            'position': id
        })

    template = 'statement/position/blind.html'
    parameters = dict(
        site_title='Position blind strategy',
        title='Blinding strategy',
        position=position,
        account_trades=account_trades,
        form=form,
        strategy_results=strategy_results,

    )

    return render(request, template, parameters)


# noinspection PyShadowingBuiltins
def position_report(request, id, date=None):
    """
    Position report for certain date
    :param request: request
    :param id: int
    :param date: str
    :return: render
    """
    position = Position.objects.get(id=id)

    if date:
        date_query1 = {'start': position.start, 'stop': date}
        date_query2 = Q(statement__date__gte=position.start) & Q(statement__date__lte=date)
    else:
        if position.stop:
            date_query1 = {'start': position.start, 'stop': position.stop}
            date_query2 = Q(statement__date__gte=position.start) & Q(statement__date__lte=position.stop)
            date = position.stop.strftime('%Y-%m-%d')
        else:
            date = position.profitloss_set.order_by('statement__date')\
                .last().statement.date.strftime('%Y-%m-%d')
            date_query1 = {'start': position.start, 'stop': date}
            date_query2 = Q(statement__date__gte=position.start) & Q(statement__date__lte=date)

    # opinion
    holding_opinions = position.holdingopinion_set.all()

    try:
        stocks = Underlying.objects.get(symbol=position.symbol).get_stock(
            source='google', **date_query1
        )
        """:type: DataFrame"""
    except ObjectDoesNotExist:
        underlying = Underlying()
        underlying.symbol = position.symbol
        underlying.start_date = '2009-01-01'
        underlying.stop_date = position.stop if position.stop else date
        underlying.save()

        web_stock_h5(request, source='google', symbol=position.symbol.lower())
        web_stock_h5(request, source='yahoo', symbol=position.symbol.lower())

        stocks = Underlying.objects.get(symbol=position.symbol).get_stock(
            source='google', **date_query1
        )

    if not len(stocks):
        raise LookupError('< {symbol} > have no stock data'.format(symbol=position.symbol))

    # statement
    profit_losses = position.profitloss_set.filter(date_query2)
    open_trades = position.accounttrade_set.filter(pos_effect='TO OPEN')
    close_trade = position.accounttrade_set.filter(pos_effect='TO CLOSE')
    cash_balances = position.cashbalance_set.filter(date_query2)

    # basic
    basic = dict()
    date0 = datetime.strptime(date, '%Y-%m-%d').date()
    basic['open'] = stocks.ix[stocks.index[-1]]['open']  # stocks.last().open
    basic['close'] = stocks.ix[stocks.index[-1]]['close']  # float(stocks.last().close)
    basic['holding_day'] = (date0 - position.start).days
    basic['start_date'] = position.start
    basic['stop_date'] = date0
    basic['expire_date'] = None
    basic['dte'] = None
    if position.name not in ('STOCK', ''):
        ex_month, ex_year = position.holdingoption_set.first().exp.split(' ')
        basic['expire_date'] = get_dte_date2(ex_month, int(ex_year))
        basic['dte'] = (basic['expire_date'] - date0).days

    basic['quantity'] = '/'.join(['%+d' % a['qty'] for a in open_trades.values('qty')])
    basic['enter_price'] = open_trades.first().net_price
    basic['exit_price'] = '...'
    if date0 == position.stop:
        basic['exit_price'] = close_trade.first().net_price
    basic['current_pl'] = profit_losses.order_by('statement__date').last().pl_open

    basic['commission'] = sum([c.commission for c in cash_balances])
    basic['brokerage'] = sum([c.fee for c in cash_balances])
    basic['total_fee'] = basic['commission'] + basic['brokerage']
    basic['margin'] = abs(cash_balances.order_by('statement__date').first().amount)

    # condition
    conditions = [{'stage': c[0], 'expr': c[1], 'amount': c[2], 'count': 0, 'prob': 0}
                  for c in position.make_conditions()]
    for condition in conditions:
        if condition['expr'].count('<') == 2:
            condition['distance'] = '...'
            condition['average'] = '...'
        else:
            price = float([e for e in condition['expr'].format(x='').split()
                           if '=' not in e and e is not '<'].pop())
            condition['distance'] = round((price - basic['close']) / basic['close'], 4)

            condition['average'] = '...'
            if basic['dte']:
                condition['average'] = round(condition['distance'] / basic['dte'], 4)

        condition['remain'] = None
        if condition['amount'].count('<') != 2:
            amount = float([a for a in condition['amount'].format(y='').split()
                            if '=' not in a and a is not '<'].pop())

            condition['remain'] = amount - float(basic['current_pl'])

    # stock
    opinions = list()
    stat = {
        'up_count': 0, 'up_pct': 0, 'e_count': 0, 'e_pct': 0, 'dw_count': 0, 'dw_pct': 0,
        'p_count': 0, 'p_pct': 0, 'l_count': 0, 'l_pct': 0
    }
    previous = None
    reports = list()
    for _, data in stocks.iterrows():
        stock = {
            'date': data['date'].date(),
            'open': data['open'],
            'high': data['high'],
            'low': data['low'],
            'close': data['close'],
            'volume': data['volume'],
        }

        try:
            profit_loss = profit_losses.get(statement__date=data['date'].date())
        except ObjectDoesNotExist:
            profit_loss = None

        stock['pct_chg'] = 0.0
        if previous:
            stock['pct_chg'] = round((stock['close'] - previous['close']) / previous['close'], 4)
        previous = stock

        if stock['pct_chg'] > 0:
            stat['up_count'] += 1
            stat['up_pct'] = round(stat['up_count'] / float(len(stocks)), 4)
        elif stock['pct_chg'] < 0:
            stat['dw_count'] += 1
            stat['dw_pct'] = round(stat['dw_count'] / float(len(stocks)), 4)
        else:
            stat['e_count'] += 1
            stat['e_pct'] = round(stat['e_count'] / float(len(stocks)), 4)

        if profit_loss:
            if profit_loss.pl_open > 0:
                stat['p_count'] += 1
                stat['p_pct'] = round(stat['p_count'] / float(len(stocks)), 4)
            elif profit_loss.pl_open < 0:
                stat['l_count'] += 1
                stat['l_pct'] = round(stat['l_count'] / float(len(stocks)), 4)

        stage = position.current_stage(stock['close'])
        reports.append({
            'date': stock['date'],
            'stock': stock,
            'profit_loss': profit_loss,
            'stage': stage
        })

        # condition
        for key, condition in enumerate(conditions):
            if condition['stage'] == stage:
                conditions[key]['count'] += 1
                conditions[key]['percent'] = round(conditions[key]['count'] / float(len(stocks)), 4)

        # opinion
        try:
            opinion = holding_opinions.get(date=stock['date'])

            result = False
            if stock['pct_chg'] > 0.5 and opinion.opinion == 'BULL':
                result = True
            elif stock['pct_chg'] < -0.5 and opinion.opinion == 'BEAR':
                result = True
            elif -0.5 < stock['pct_chg'] < 0.5 and opinion.opinion == 'RANGE':
                result = True

            opinions.append({
                'object': opinion,
                'pct_chg': stock['pct_chg'],
                'result': result
            })
        except ObjectDoesNotExist:
            pass

    # basic
    basic['stat'] = stat
    basic['pct_chg'] = reports[-1]['stock']['pct_chg']
    basic['stage'] = position.current_stage(reports[-1]['stock']['close'])
    basic['net_move'] = reports[-1]['stock']['close'] - reports[0]['stock']['close']
    basic['pct_move'] = round(basic['net_move'] / reports[0]['stock']['close'], 4)
    basic['mean_move'] = round(Series([r['stock']['pct_chg'] for r in reports]).mean(), 4)
    basic['pct_std'] = round(Series([r['stock']['pct_chg'] for r in reports]).std(), 4)
    basic['market_opinion'] = position.market_opinion
    basic['enter_opinion'] = position.enter_opinion
    basic['exit_opinion'] = position.exitopinion_set.last()
    basic['max_profit'] = max([float(pl.pl_open) for pl in profit_losses]) / float(basic['margin'])
    basic['max_loss'] = min([float(pl.pl_open) for pl in profit_losses]) / float(basic['margin'])
    basic['max_bull'] = max([r['stock']['pct_chg'] for r in reports])
    basic['max_bear'] = min([r['stock']['pct_chg'] for r in reports])

    # strategy
    strategy_result = position.strategy_result

    # quant
    quant = dict()
    if strategy_result:
        quant['bull'] = strategy_result.algorithm_result.pct_bull - stat['up_pct']
        quant['even'] = strategy_result.algorithm_result.pct_even - stat['e_pct']
        quant['bear'] = strategy_result.algorithm_result.pct_bear - stat['dw_pct']
        quant['pct_move'] = strategy_result.algorithm_result.pct_mean - basic['pct_move']
        quant['mean_move'] = strategy_result.algorithm_result.pct_mean - basic['mean_move']
        quant['std'] = strategy_result.algorithm_result.pct_std - basic['pct_std']

        quant['min_pct'] = min([r['stock']['pct_chg'] for r in reports])
        quant['var_pct99'] = strategy_result.algorithm_result.var_pct99 - quant['min_pct']
        quant['var_pct95'] = strategy_result.algorithm_result.var_pct95 - quant['min_pct']

        # drawdown using left right
        closes = [r['stock']['close'] for r in reports]
        basic['drawdown'] = round((min(closes) - max(closes)) / max(closes), 4)
        quant['drawdown'] = strategy_result.algorithm_result.max_dd - basic['drawdown']
        quant['roll_dd'] = strategy_result.algorithm_result.r_max_dd - basic['drawdown']

        quant['profit_day'] = strategy_result.day_profit_mean - stat['p_pct']
        quant['loss_day'] = strategy_result.day_profit_mean - stat['l_pct']
        quant['max_profit'] = strategy_result.max_profit - basic['max_profit']
        quant['max_loss'] = strategy_result.max_loss - basic['max_loss']

        if strategy_result.algorithm_result.pct_max > strategy_result.algorithm_result.pct_min:
            quant['pct_max'] = strategy_result.algorithm_result.pct_max
            quant['pct_min'] = strategy_result.algorithm_result.pct_min
        else:
            quant['pct_max'] = strategy_result.algorithm_result.pct_min
            quant['pct_min'] = strategy_result.algorithm_result.pct_max

        quant['max_bull'] = quant['pct_max'] - basic['max_bull']
        quant['max_bear'] = quant['pct_min'] - basic['max_bear']

    historicals = Position.objects.filter(
        Q(symbol=position.symbol) & Q(start__lt=position.start)
    ).order_by('stop').reverse()

    last_pl = 0.0
    for historical in historicals:
        pl_close = float(historical.profitloss_set.get(statement__date=historical.stop).pl_ytd)
        historical.pl_close = pl_close - last_pl
        last_pl = pl_close

    # paginator
    dates = [pl.statement.date.strftime('%Y-%m-%d') for pl in
             position.profitloss_set.order_by('statement__date')]

    # view
    template = 'statement/position/report/index.html'

    parameters = dict(
        site_title='Position report',
        title='Position report: {symbol} {date}'.format(
            symbol=position.symbol, date=date
        ),
        date=date,
        position=position,
        basic=basic,
        stages=position.positionstage_set.all(),
        conditions=conditions,
        reports=reports,
        opinions=opinions,
        result=strategy_result,
        quant=quant,
        historicals=historicals,
        page=date_page(dates, date, 'admin:position_report', {'id': id})
    )

    return render(request, template, parameters)


def daily_import(request, date, ready_all=0):
    """
    Daily google and yahoo import
    :param request: request
    :param date: str
    :param ready_all: int
    :return: render
    """
    statement = Statement.objects.get(date=date)

    if int(ready_all):
        date = Statement.objects.order_by('date').last().date
        positions = Position.objects.all()
    else:
        date = pd.datetime.strptime(date, '%Y-%m-%d').date()

        positions = Position.objects.filter(
            id__in=[p[0] for p in statement.profitloss_set.values_list('position')]
        ).order_by('symbol')

    db = pd.HDFStore(QUOTE)
    for symbol in list(set([p.symbol for p in positions] + ['SPY'])):
        end = date
        try:
            underlying = Underlying.objects.get(symbol=symbol)
            start = underlying.stop_date
            underlying.stop_date = date
            underlying.save()
        except ObjectDoesNotExist:
            underlying = Underlying()
            underlying.symbol = symbol
            underlying.start_date = '2009-01-01'
            underlying.stop_date = date
            underlying.save()
            start = underlying.start_date

        if start == end:
            continue

        # drop if ohlc is empty
        for source, f in (('google', get_data_google), ('yahoo', get_data_yahoo)):
            try:
                df_stock = f(symbols=symbol, start=start, end=end)

                if not len(df_stock):
                    continue

                for field in ['Open', 'High', 'Low', 'Close']:
                    df_stock[field] = df_stock[field].replace('-', np.nan).astype(float)

                # do not drop if volume is empty
                df_stock['Volume'] = df_stock['Volume'].replace('-', 0).astype(long)

                # rename into lower case
                df_stock.columns = [c.lower() for c in df_stock.columns]

                if source == 'yahoo':
                    del df_stock['adj close']

                df_stock.index.names = ['date']

                # skip or insert
                # for line in data.dropna().to_csv().split('\n')[1:-1]:
                print 'import from %-10s for %-10s total: %-10d' % (source, symbol, len(df_stock))

                db.append(
                    'stock/%s/%s' % (source, symbol.lower()), df_stock,
                    format='table', data_columns=True, min_itemsize=100
                )

                # update symbol stat
                underlying.log += 'Web stock imported, source: %s symbol: %s length: %d\n' % (
                    source.upper(), symbol.upper(), len(df_stock)
                )
                underlying.save()

            except IOError:
                pass

    # close db
    db.close()

    return redirect(reverse('admin:position_spreads', kwargs={'date': date}))
