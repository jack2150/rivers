import logging
import os
from django.core.urlresolvers import reverse
from django.shortcuts import redirect

from rivers.settings import BASE_DIR

logger = logging.getLogger('views')
output = '%-6s | %-30s'


def calc_day_iv(request, symbol, insert):
    """
    Cli for calc day_iv
    :param request: request
    :param symbol: str
    :param insert: int
    :return: render
    """
    logger.info('Start cli for calc_iv: %s' % symbol.upper())

    path = os.path.join(BASE_DIR, 'data/manage.py')
    os.system("start cmd /k python %s calc_iv --symbol=%s --insert=%s" % (path, symbol, insert))

    return redirect(reverse('admin:manage_underlying', kwargs={'symbol': symbol}))
