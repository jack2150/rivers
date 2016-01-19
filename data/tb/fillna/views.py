import logging
import os
from django.core.urlresolvers import reverse
from django.shortcuts import redirect

logger = logging.getLogger('views')


def fillna_normal_h5(request, symbol):
    """
    Fill missing rows for df_normal
    :param request: request
    :param symbol: str
    :return: render
    """
    logger.info('Start cli for fillna_normal: %s' % symbol)
    os.system("start cmd /k python data/manage.py fillna_clean --symbol=%s --name=normal" % symbol)

    return redirect(reverse('admin:manage_underlying', kwargs={'symbol': symbol}))
