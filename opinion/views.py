from decimal import Decimal
from django.core.exceptions import ObjectDoesNotExist
from django.db.models import Q
from django.shortcuts import render
from opinion.models import *
from statement.models import Statement


def opinion_link(request, symbol):
    """

    :param request:
    :param symbol:
    :return:
    """
    symbol = symbol.upper()

    template = 'opinion/opinion_link.html'

    parameters = dict(
        site_title='Opinion links',
        title='{symbol} opinions links'.format(symbol=symbol),
        symbol=symbol
    )

    return render(request, template, parameters)


def market_profile(request, date):
    """
    Market analysis profile using popular indicators
    It is require create every day before marker open
    :param request: request
    :param date: str
    :return: render
    """
    # market indicator section
    market_indicator = MarketIndicator.objects.get(date=date)
    keys = [
        'fund_cash_ratio', 'fear_greek_index', 'credit_balance',
        'put_call_ratio', 'investor_sentiment', 'futures_trader', 'confidence_index',
        'ted_spread', 'margin_debt', 'market_breadth', 'arms_index',
        'ma200day_pct', 'fair_value_trend',
    ]

    # reverse:
    direct0 = [
        'fund_cash_ratio', 'fear_greek_index', 'credit_balance',
        'put_call_ratio', 'investor_sentiment', 'futures_trader',
        'margin_debt', 'market_breadth', 'fair_value_trend',
    ]
    direct1 = {
        'increase': 1, 'range': 0, 'decrease': -1,
        'greed': 1, 'fear': -1,
        'bullish': 1, 'neutral': 0, 'bearish': -1,
        'overbought': 1, 'fair_value': 0, 'oversold': -1,
    }
    reverse1 = {
        'increase': -1, 'range': 0, 'decrease': 1,
        'overbought': -1, 'fair_value': 0, 'oversold': 1,
    }

    summary0 = {'bullish': 0, 'neutral': 0, 'bearish': 0, 'total': 0}
    for key in keys:
        if key in direct0:
            result = direct1[getattr(market_indicator, key)]
        else:
            result = reverse1[getattr(market_indicator, key)]

        summary0['total'] += result

        if result == 1:
            summary0['bullish'] += 1
        elif result == -1:
            summary0['bearish'] += 1
        else:
            summary0['neutral'] += 1

    # macro valuation section
    try:
        macro_valuation = MarketValuation.objects.get(date=date)
    except ObjectDoesNotExist:
        macro_valuation = MarketValuation.objects.latest('date')

    keys = ['cli_trend', 'bci_trend', 'market_scenario', 'money_supply']
    result1 = {
        'increase': 1, 'range': 0, 'decrease': -1,
        'positive': 1, 'midly_negative': 0, 'very_negative': -1,
    }
    summary1 = {'bullish': 0, 'neutral': 0, 'bearish': 0, 'total': 0}
    for key in keys:

        result = result1[getattr(macro_valuation, key)]
        summary1['total'] += result

        if result == 1:
            summary1['bullish'] += 1
        elif result == -1:
            summary1['bearish'] += 1
        else:
            summary1['neutral'] += 1

    # market opinion
    market_opinion = MarketMovement.objects.get(date=date)

    keys = [
        'volatility', 'bond', 'commodity', 'currency',
        'current_short_trend', 'current_long_trend'
    ]
    result1 = {
        'high': -1, 'normal': 0, 'low': 1,
        'bullish': 1, 'neutral': 0, 'bearish': -1,
    }
    summary2 = {'bullish': 0, 'neutral': 0, 'bearish': 0, 'total': 0}
    for key in keys:
        result = result1[getattr(market_opinion, key)]

        if key in ('bond', 'commodity'):
            result = -result

        summary2['total'] += result

        if result == 1:
            summary2['bullish'] += 1
        elif result == -1:
            summary2['bearish'] += 1
        else:
            summary2['neutral'] += 1

    if market_opinion.market_indicator > 2:
        summary2['total'] -= 1
        summary2['bearish'] += 1
    elif market_opinion.market_indicator > 0 and market_opinion.extra_attention > 2:
        summary2['neutral'] += 1
    else:
        summary2['total'] += 1
        summary2['bullish'] += 1

    template = 'opinion/market_profile.html'

    parameters = dict(
        site_title='Market profile',
        title='Market profile',
        date=date,
        market_indicator=market_indicator,
        macro_valuation=macro_valuation,
        market_opinion=market_opinion,
        summary0=summary0,
        summary1=summary1,
        summary2=summary2,
    )

    return render(request, template, parameters)


def industry_profile(request, symbol, date):
    """
    Industry analysis profile for certain symbol and date
    usually create when enter position and update only once a week
    :param request: request
    :param symbol: str
    :param date: str
    :return: render
    """
    symbol = symbol.upper()

    # fundamental analysis
    fundamental_opinion = FundamentalOpinion.objects.get(Q(symbol=symbol) & Q(date=date))

    keys5 = [
        'mean_rank', 'ownership_activity', 'guru_trade',
    ]
    keys3 = ['insider_trade', 'short_interest']
    keys1 = [
        'earning_surprise', 'earning_grow', 'dividend_grow', 'pe_ratio_trend',
        'div_yield_trend', 'valuation'
    ]
    results = {
        'buying': 1, 'holding': 0, 'selling': -1,
        'increase': 1, 'range': 0, 'decrease': -1,
        'positive': 1, 'no-surprise': 0, 'negative': -1,
        'cheap': 1, 'normal': 0, 'expensive': -1,
    }

    summary0 = {
        'bullish': {'count': 0, 'score': 0},
        'neutral': {'count': 0, 'score': 0},
        'bearish': {'count': 0, 'score': 0},
        'total': {'count': 0, 'score': 0}
    }

    for key in keys5 + keys3 + keys1:
        if key == 'mean_rank':
            result = getattr(fundamental_opinion, key)
        else:
            result = results[getattr(fundamental_opinion, key)]

            if key in keys5:
                result *= 5
            elif key in keys3:
                result *= 3

        summary0['total']['score'] += result
        summary0['total']['count'] += 1

        if result > 0:
            summary0['bullish']['count'] += 1
            summary0['bullish']['score'] += result
        elif result < 0:
            summary0['bearish']['count'] += 1
            summary0['bearish']['score'] += result
        else:
            summary0['neutral']['count'] += 1
            summary0['neutral']['score'] += result

    # industry analysis
    industry_opinion = IndustryOpinion.objects.get(Q(symbol=symbol) & Q(date=date))

    keys = [
        'index_trend', 'risk_diff', 'industry_pe',
        'industry_rank', 'industry_fa', 'fair_value'
    ]
    results = {
        'higher': 1, 'range': 0, 'lower': -1,
        'bullish': 1, 'neutral': 0, 'bearish': -1,
        'better': 1, 'average': 0, 'worst': -1,
    }

    summary1 = {'bullish': 0, 'neutral': 0, 'bearish': 0, 'total': 0}
    for key in keys:
        result = results[getattr(industry_opinion, key)]

        if key == 'index_trend' and industry_opinion.isolate:
            result = -result
        elif key in ('risk_diff', 'industry_pe', 'fair_value'):
            result = -result

        summary1['total'] += result

        if result == 1:
            summary1['bullish'] += 1
        elif result == -1:
            summary1['bearish'] += 1
        else:
            summary1['neutral'] += 1

    template = 'opinion/industry_profile.html'

    parameters = dict(
        site_title='Industry profile',
        title='{symbol} Industry profile: {industry}, {sector}'.format(
            symbol=industry_opinion.symbol.upper(),
            industry=industry_opinion.industry,
            sector=industry_opinion.sector
        ),
        symbol=symbol,
        date=date,
        fundamental_opinion=fundamental_opinion,
        industry_opinion=industry_opinion,
        summary0=summary0,
        summary1=summary1
    )

    return render(request, template, parameters)


def weekday_profile(request, symbol, date):
    """
    Weekday opinion profile for symbol date
    :param request: request
    :param symbol: str
    :param date: str
    :return: render
    """
    symbol = symbol.upper()
    weekday_opinion = WeekdayOpinion.objects.get(Q(symbol=symbol) & Q(date=date))

    keys = [
        'new_info_impact', 'put_call_ratio', 'last_5day_return',
        'today_biggest', 'consecutive_move', 'unusual_volume',
        'moving_avg200x50', 'current_short_trend', 'current_long_trend',
    ]
    results = {
        'bullish': 1, 'neutral': 0, 'bearish': -1,
        'up': 1, 'no-change': 0, 'down': -1, '': 0,
    }

    summary = {
        'bullish': {'count': 0, 'score': 0},
        'neutral': {'count': 0, 'score': 0},
        'bearish': {'count': 0, 'score': 0},
        'total': {'count': 0, 'score': 0}
    }

    for key in keys:
        value = getattr(weekday_opinion, key)
        if key == 'new_info_impact':
            if value:
                result = results[getattr(weekday_opinion, 'new_info_move')] * 5
            else:
                result = 0
        elif key == 'put_call_ratio':
            if value <= 0.66:
                result = 1
            elif 0.66 < value <= 1:
                result = 0
            else:
                result = -1
        elif key == 'last_5day_return':
            if value > 1:
                result = 1
            elif value < -1:
                result = -1
            else:
                result = 0
        else:
            result = results[value]

        # summary
        summary['total']['score'] += result
        summary['total']['count'] += 1

        if result > 0:
            summary['bullish']['count'] += 1
            summary['bullish']['score'] += result
        elif result < 0:
            summary['bearish']['count'] += 1
            summary['bearish']['score'] += result
        else:
            summary['neutral']['count'] += 1
            summary['neutral']['score'] += result

    # last_5day_return, new_info_impact & put_call_ratio

    template = 'opinion/weekday_profile.html'

    parameters = dict(
        site_title='Weekday profile',
        title='{symbol} Weekday opinion: {date}'.format(
            symbol=symbol, date=date
        ),
        symbol=symbol,
        date=date,
        weekday_opinion=weekday_opinion,
        summary=summary
    )

    return render(request, template, parameters)


def position_profile(request, symbol, date, portfolio=0):
    """
    Position opinion profile for symbol date
    :param request: request
    :param symbol: str
    :param date: str
    :param portfolio: int
    :return: render
    """
    symbol = symbol.upper()
    position_opinion = PositionOpinion.objects.get(Q(symbol=symbol) & Q(date=date))
    close_opinion = CloseOpinion.objects.filter(symbol=symbol).order_by('date')
    if close_opinion.exists():
        close_opinion = close_opinion.first()
        weekday_opinions = WeekdayOpinion.objects.filter(
            Q(symbol=symbol) & Q(date__gte=date) & Q(date__lte=close_opinion.date)
        )
    else:
        close_opinion = None
        weekday_opinions = WeekdayOpinion.objects.filter(
            Q(symbol=symbol) & Q(date__gte=date)
        ).order_by('date')

    weekday_opinion = WeekdayOpinion.objects.first()

    # write opinion
    commentary = {}
    score = {}
    others = {}

    # risk profile
    if portfolio:
        # use custom portfolio after complete portfolio
        capital_pct = {'high': 20, 'medium': 10, 'low': 0}
        others['net_liquid'] = Decimal(25000.0),
        others['stock_bp'] = others['net_liquid'] * 2,
        others['option_bp'] = others['net_liquid'],
        others['commission_ytd'] = 0
    else:
        # use default portfolio
        try:
            statement = Statement.objects.get(date=date)
        except ObjectDoesNotExist:
            try:
                statement = Statement.objects.latest('date')
            except ObjectDoesNotExist:
                capital = 25000.0
                statement = Statement(
                    net_liquid=capital,
                    stock_bp=capital * 2,
                    option_bp=capital,
                    commission_ytd=0
                )

        others['net_liquid'] = statement.net_liquid
        others['stock_bp'] = statement.stock_bp
        others['option_bp'] = statement.option_bp
        others['commission_ytd'] = statement.commission_ytd

        # commentary
        capital_pct = {'high': 20, 'medium': 10, 'low': 0}
        risk_profile = {
            'high': 'High risk, use 20% portfolio capital to trade. '
                    'You must be very confident on this position.',
            'medium': 'Average risk, use 10% portfolio capital to trade. '
                      'You must be diversify and hedge this position.',
            'low': 'Low risk, use less than 10% portfolio capital to trade. '
                   'You trade low probability position that limit your risk.',
        }

        commentary['risk_profile'] = (
            'Using default portfolio design. ' +
            risk_profile[position_opinion.risk_profile.__str__()]
        )
        score['risk_profile'] = True

    # bp effect
    bp_effect_pct = round(position_opinion.bp_effect / others['net_liquid'] * 100, 2)
    others['bp_effect_pct'] = bp_effect_pct
    score['bp_effect'] = True
    if bp_effect_pct > capital_pct['high']:
        if position_opinion.risk_profile == 'high':
            commentary['bp_effect'] = 'This is a valid high risk profile trade.'
        else:
            commentary['bp_effect'] = 'Risk too high for {risk} risk profile trade. Adjust it!'.format(
                risk=position_opinion.risk_profile
            )
            score['bp_effect'] = False
    elif bp_effect_pct >= capital_pct['medium']:
        if position_opinion.risk_profile == 'medium':
            commentary['bp_effect'] = 'This is a valid high risk profile trade.'
        else:
            commentary['bp_effect'] = 'Range {high}% to {medium}% not in risk profile. Adjust it!'.format(
                high=capital_pct['high'], medium=capital_pct['medium']
            )
            score['bp_effect'] = False
    else:
        if position_opinion.risk_profile == 'low':
            commentary['bp_effect'] = 'This is a valid high risk profile trade.'
        else:
            commentary['bp_effect'] = 'Risk too low for {risk} risk profile. Adjust it!'.format(
                risk=position_opinion.risk_profile
            )
            score['bp_effect'] = False

    # iv rank
    if position_opinion.optionable:
        score['spread'] = True
        if position_opinion.spread == 'debit':
            if weekday_opinion.iv_rank == 'above_66':
                score['spread'] = False

        else:
            if weekday_opinion.iv_rank == 'below_33':
                score['spread'] = False
    else:
        score['spread'] = True

    # max profit, max loss
    score['max_profit'] = True
    score['max_loss'] = True
    score['size'] = True
    score['event_trade'] = True

    # dte
    if position_opinion.dte <= 14:
        score['dte'] = False
    else:
        score['dte'] = True

    # movement, target price
    if weekday_opinion.close_price < position_opinion.target_price:
        if position_opinion.price_movement in ('bullish', 'neutral'):
            score['price_movement'] = True
        else:
            score['price_movement'] = False
    else:
        if position_opinion.price_movement in ('bearish', 'neutral'):
            score['price_movement'] = True
        else:
            score['price_movement'] = False

    # event holding period
    if position_opinion.event_period:
        if position_opinion.event_trade:
            score['event_period'] = True
        else:
            score['event_period'] = False
    else:
        score['event_period'] = True

    template = 'opinion/position_profile.html'

    parameters = dict(
        site_title='Position opinion profile',
        title='{symbol} Position opinion profile: {date}'.format(
            symbol=symbol, date=date
        ),
        symbol=symbol,
        date=date,
        position_opinion=position_opinion,
        weekday_opinions=weekday_opinions,
        weekday_opinion=weekday_opinion,
        commentary=commentary,
        score=score,
        others=others,
        close_opinion=close_opinion
    )

    return render(request, template, parameters)


def behavior_profile(request, date):
    """
    Behaviour opinion profile
    :param request: request
    :param date: str
    :return: render
    """
    behavior_opinion = BehaviorOpinion.objects.get(date=date)

    template = 'opinion/behavior_profile.html'

    parameters = dict(
        site_title='Behavior profile',
        title='Behavior profile: {date}'.format(
            date=date
        ),
        date=date,
        behavior_opinion=behavior_opinion
    )

    return render(request, template, parameters)
