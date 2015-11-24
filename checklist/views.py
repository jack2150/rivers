from StringIO import StringIO
from django.core.urlresolvers import reverse
from django.shortcuts import redirect, render
from checklist.models import *
from statement.models import Statement


# noinspection PyShadowingBuiltins
def enter_opinion_get_data(request, id):
    """
    Get enter opinion from web
    :param request: request
    :param id: int
    :return: redirect
    """
    enter_opinion = EnterOpinion.objects.get(id=id)

    if not enter_opinion.ownership:
        try:
            enter_opinion.get_ownership()
        except LookupError:
            print '{symbol} have no ownership...'.format(symbol=enter_opinion.symbol)

        enter_opinion.ownership = True

    if not enter_opinion.insider:
        try:
            enter_opinion.get_insider()
        except LookupError:
            print '{symbol} have no insider...'.format(symbol=enter_opinion.symbol)

        enter_opinion.insider = True

    if not enter_opinion.short_interest:
        try:
            enter_opinion.get_short_interest()
        except LookupError:
            print '{symbol} have no short interest...'.format(symbol=enter_opinion.symbol)

        enter_opinion.short_interest = True

    if not enter_opinion.analyst_rating:
        try:
            enter_opinion.get_rating()
        except LookupError:
            print '{symbol} have no rating...'.format(symbol=enter_opinion.symbol)

        enter_opinion.analyst_rating = True

    # set complete
    enter_opinion.complete = True
    enter_opinion.save()

    return redirect(reverse('admin:checklist_enteropinion_change', args=(id,)))


# noinspection PyTypeChecker,PyShadowingBuiltins
def enter_opinion_report(request, id):
    """
    Report for enter opinion before entering a position
    using 1-5 method like brokerage rating, 1 is best, 5 is worst
    :param request: request
    :param id: int
    :return: render
    """
    e = EnterOpinion.objects.get(id=id)
    m = MarketOpinion.objects.get(date=e.date)

    report = dict()

    statement = Statement.objects.latest('date')

    # POSITION OPINION #
    report['profit_day'] = round(e.profit / (e.exit_date - e.enter_date).days, 2)
    report['profit_pct'] = round(float(e.profit) / float(statement.net_liquid) * 100, 2)

    report['loss_day'] = round(e.loss / (e.exit_date - e.enter_date).days, 2)
    report['loss_pct'] = round(float(e.loss) / float(statement.net_liquid) * 100, 2)

    for key in ('profit', 'loss'):
        if report[key + '_pct'] > 5:
            report[key] = 'HIGH'
        elif report[key + '_pct'] > 2:
            report[key] = 'NORMAL'
        else:
            report[key] = 'LOW'

    report['bp_effect_pct'] = round(float(e.bp_effect) / float(statement.net_liquid) * 100, 2)
    report['bp_effect_count'] = int(round(float(statement.net_liquid) / float(e.bp_effect), 0))

    if report['bp_effect_pct'] > 10:
        report['bp_effect'] = 'HIGH'
    elif report['bp_effect_pct'] > 5:
        report['bp_effect'] = 'NORMAL'
    else:
        report['bp_effect'] = 'LOW'

    # MARKET OPINION #
    # if vix is high, good for credit spread, if low, good for debit spread
    volatility = {
        'INCREASE': {'CREDIT': 1, 'DEBIT': 5},
        'NORMAL': {'CREDIT': 3, 'DEBIT': 3},
        'DECREASE': {'CREDIT': 5, 'DEBIT': 1},
    }
    report['volatility'] = volatility[m.volatility][e.spread]

    # economics calender
    report['calendar'] = m.market_indicator * 3
    report['calendar'] += m.extra_attention * 2
    report['calendar'] += m.key_indicator
    report['calendar'] += m.special_news * 5

    # market trend
    if e.market == 'MAJOR':  # follow market indices
        report['market_trend'] = {
            'BULL': {'BULL': 1, 'RANGE': 2, 'BEAR': 3},
            'RANGE': {'BULL': 4, 'RANGE': 3, 'BEAR': 2},
            'BEAR': {'BULL': 3, 'RANGE': 4, 'BEAR': 5},
        }[m.long_trend1][m.short_trend1]

    elif e.indice in ('BOND', 'COMMODITY', 'CURRENCY'):
        report['market_trend'] = {'BULL': 1, 'RANGE': 3, 'BEAR': 5}[m.long_trend1]
    else:
        report['market_trend'] = 0

    # ENTER OPINION #
    # event report
    report['event'] = 1
    if not e.event:  # is not event trade
        report['event'] = e.earning * 5
        report['event'] += e.dividend * 2
        report['event'] += e.split * 10
        report['event'] += e.announcement * 10



    # recent news
    report['news'] = {
        'WEAK': {'BULL': 3, 'UNKNOWN': 3, 'BEAR': 3},
        'NORMAL': {'BULL': 2, 'UNKNOWN': 3, 'BEAR': 4},
        'STRONG': {'BULL': 1, 'UNKNOWN': 3, 'BEAR': 5},
    }[e.news_level][e.news_signal]

    # primary trend
    report['trend'] = {
        'BULL': {'BULL': 1, 'RANGE': 2, 'BEAR': 3},
        'RANGE': {'BULL': 2, 'RANGE': 3, 'BEAR': 4},
        'BEAR': {'BULL': 3, 'RANGE': 4, 'BEAR': 5}
    }[e.long_trend1][e.short_trend1]

    # analyst rating
    report['analyst'] = 0
    if e.analyst_rating:
        report['grade'] = 'SAME'
        if e.abr_current > e.abr_previous:  # upgrade
            report['grade'] = 'UPGRADE'
        elif e.abr_current < e.abr_previous:  # downgrade
            report['grade'] = 'DOWNGRADE'

        report['rating'] = e.abr_previous
        report['target'] = e.abr_target - e.target

    # short interest
    if e.short_interest:
        df_short = pd.read_csv(
            StringIO(e.df_short_interest), index_col=0
        )
        si = df_short['short_interest']
        si_change = round((si[0] - si[3]) / float(si[3]), 2)

        # past 2 months
        report['short_interest'] = si_change * 100
        report['short_signal'] = 3
        report['short_dtc'] = round(df_short['day_to_cover'][0], 2)
        if si_change >= 0.3:
            report['short_signal'] = 5
        elif 0.3 > si_change > 0.1:
            report['short_signal'] = 4
        elif -0.1 > si_change > -0.3:
            report['short_signal'] = 2
        elif -0.3 >= si_change:
            report['short_signal'] = 1

        # short squeeze possible
        if e.short_squeeze:
            report['short_signal'] = 1

    total_shares = 1
    # ownership
    if e.ownership:
        total_shares = long(e.ownership_held_share / e.ownership_holding_pct) * 100
        if e.ownership_na_pct > 1:  # ownership held change
            ownership = 'BULL'
        elif e.ownership_na_pct < -1:
            ownership = 'BEAR'
        else:
            ownership = 'RANGE'

        if e.ownership_top15_na_pct > 1:  # top 15 held change
            top15 = 'BULL'
        elif e.ownership_top15_na_pct < -1:
            top15 = 'BEAR'
        else:
            top15 = 'RANGE'

        report['ownership'] = {
            'BULL': {'BULL': 1, 'RANGE': 2, 'BEAR': 3},
            'RANGE': {'BULL': 2, 'RANGE': 3, 'BEAR': 4},
            'BEAR': {'BULL': 3, 'RANGE': 4, 'BEAR': 5}
        }[ownership][top15]

    # insider trade
    if e.insider:
        pct3m = round(e.insider_na_3m / float(abs(e.insider_na_12m)) * 100)

        if pct3m > 5:
            insider3m = 'BULL'
        elif pct3m < -5:
            insider3m = 'BEAR'
        else:
            insider3m = 'RANGE'

        pct12m = round(e.insider_na_12m / float(total_shares) * 100, 2)
        if pct12m > 0.25:
            insider12m = 'BULL'
        elif pct12m < -0.25:
            insider12m = 'BEAR'
        else:
            insider12m = 'RANGE'

        report['insider'] = {
            'BULL': {'BULL': 1, 'RANGE': 2, 'BEAR': 3},
            'RANGE': {'BULL': 2, 'RANGE': 3, 'BEAR': 4},
            'BEAR': {'BULL': 3, 'RANGE': 4, 'BEAR': 5}
        }[insider12m][insider3m]

        report['insider_pct'] = pct12m

    template = 'checklist/enter_opinion/report.html'

    parameters = dict(
        site_title='Enter opinion report',
        title='{symbol} enter opinion checklist report'.format(symbol=e.symbol),
        symbol=e.symbol,
        enter_opinion=e,
        market_opinion=m,
        report=report
    )

    return render(request, template, parameters)


def enter_opinion_links(request, symbol):
    """
    Enter opinion link for both market and underlying
    :param request: request
    :param symbol: str
    :return: render
    """
    symbol = symbol.upper()

    template = 'checklist/enter_opinion/link.html'

    parameters = dict(
        site_title='Opinion links',
        title='{symbol} opinion links'.format(symbol=symbol),
        symbol=symbol
    )

    return render(request, template, parameters)






























