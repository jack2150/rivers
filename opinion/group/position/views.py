from decimal import Decimal
from django.core.exceptions import ObjectDoesNotExist
from django.core.urlresolvers import reverse
from django.db.models import Q
from django.shortcuts import render, redirect
# Create your views here.
from opinion.group.position.models import PositionEnter, PositionExit, PortfolioReview
from statement.models import Statement


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
    position_opinion = PositionEnter.objects.get(Q(symbol=symbol) & Q(date=date))
    close_opinion = PositionExit.objects.filter(symbol=symbol).order_by('date')
    if close_opinion.exists():
        close_opinion = close_opinion.first()
        weekday_opinions = PositionEnter.objects.filter(
            Q(symbol=symbol) & Q(date__gte=date) & Q(date__lte=close_opinion.date)
        )
    else:
        close_opinion = None
        weekday_opinions = PositionEnter.objects.filter(
            Q(symbol=symbol) & Q(date__gte=date)
        ).order_by('date')

    weekday_opinion = PositionEnter.objects.first()

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


def weekday_profile(request, symbol, date):
    """
    Weekday opinion profile for symbol date
    :param request: request
    :param symbol: str
    :param date: str
    :return: render
    """
    symbol = symbol.upper()
    enter_opinion = PositionEnter.objects.get(Q(symbol=symbol) & Q(date=date))

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
        value = getattr(enter_opinion, key)
        if key == 'new_info_impact':
            if value:
                result = results[getattr(enter_opinion, 'new_info_move')] * 5
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
        weekday_opinion=enter_opinion,
        summary=summary
    )

    return render(request, template, parameters)


def portfolio_latest(request):
    """
    Auto get latest portfolio
    :param request: request
    :return: redirect
    """
    portfolio_review = PortfolioReview.objects.latest('date')

    return redirect(reverse('admin:opinion_portfolioreview_change', args=(portfolio_review.id,)))

