import logging
import os
from django.core.urlresolvers import reverse
from django.shortcuts import redirect

logger = logging.getLogger('views')
output = '%-6s | %-30s'


def calc_day_iv(request, symbol):
    """
    Cli for calc day_iv
    :param request: request
    :param symbol: str
    :return: render
    """
    logger.info('Start cli for calc_iv: %s' % symbol.upper())
    os.system("start cmd /k python data/manage.py calc_iv --symbol=%s" % symbol)

    return redirect(reverse('admin:manage_underlying', kwargs={'symbol': symbol}))