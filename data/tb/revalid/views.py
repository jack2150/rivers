import logging
import os
from django.core.urlresolvers import reverse
from django.shortcuts import redirect

logger = logging.getLogger('views')


def valid_clean_h5(request, symbol):
    """
    Fill missing rows for df_normal
    :param request: request
    :param symbol: str
    :return: render
    """
    logger.info('Start cli for clean_valid: %s' % symbol)
    os.system("start cmd /k python data/manage.py valid_clean --symbol=%s" % symbol)

    return redirect(reverse('admin:manage_underlying', kwargs={'symbol': symbol}))
