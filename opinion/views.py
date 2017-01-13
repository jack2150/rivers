from django.shortcuts import render


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

# todo: symbol date report, for all detail, position & technical
# todo: market & mindset & quest date report, all market
