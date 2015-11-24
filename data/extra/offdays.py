from datetime import datetime, date

market_offdays = [
    '01/21/2011',
    '05/04/2011',
    '08/12/2011',
    '10/19/2012',
    '10/29/2012',
    '10/30/2012',
    '02/28/2014',
    '07/18/2014',
    '10/10/2014',
    '01/19/2015',
    '02/16/2015',
    '03/09/2015',
    '04/03/2015',
    '04/14/2015',
    '04/15/2015',
    '04/16/2015',
    '04/17/2015',
    '07/03/2015',
    '09/07/2015'
]


def offday(d):
    """
    Check date is market non trading day
    :param d: str or datetime or date
    :return: boolean
    """
    if type(d) in (datetime, date):
        d = d.strftime('%m/%d/%Y')

    return True if d in market_offdays else False


if __name__ == '__main__':
    assert (offday('07/18/2014') is True), "Date is not holiday."
    assert (offday('04/04/2015') is False), "Date is holiday."

    assert (offday(datetime.strptime('2015-02-16', '%Y-%m-%d').date()) is True)
