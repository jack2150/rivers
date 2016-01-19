import logging
import os

from django.core.urlresolvers import reverse
from django.shortcuts import redirect

logger = logging.getLogger('views')


def valid_option_h5(request, symbol):
    """
    Extract then import raw csv data into h5 db
    :param request: request
    :param symbol: str
    :return: render
    """
    logger.info('Start cli for valid_raw: %s' % symbol)
    os.system("start cmd /k python data/manage.py valid_raw --symbol=%s" % symbol)

    return redirect(reverse('admin:manage_underlying', kwargs={'symbol': symbol}))
