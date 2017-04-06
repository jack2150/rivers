from django.shortcuts import render


def report_earning(request, symbol):
    """

    :param request:
    :param symbol:
    :return:
    """



    title = 'Distribution report | %s' % symbol.upper()
    template = 'opinion/statistic/distribution/report.html'
    parameters = dict(
        site_title=title,
        title=title,
        symbol=symbol,

    )

    return render(request, template, parameters)
