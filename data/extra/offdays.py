from datetime import datetime, date

market_offdays = (
    '01/21/11',
    '01/21/11',
    '05/04/11',
    '08/12/11',
    '10/19/12',
    '10/29/12',
    '10/30/12',
    '02/28/14',
    '07/18/14',
    '10/10/14',
    '01/19/15',
    '02/16/15',
    '03/09/15',
    '04/03/15',

    # skip date, thinkback error
    '04/14/15',
    '04/15/15',
    '04/16/15',
    '04/17/15',
    '07/03/15',
    '09/07/15',
)


def offday(d):
    """
    Check date is market non trading day
    :param d: str or datetime or date
    :return: boolean
    """
    if type(d) in (datetime, date):
        d = d.strftime('%m/%d/%y')

    return True if d in market_offdays else False


if __name__ == '__main__':
    assert (offday('07/18/14') is True), "Date is not holiday."
    assert (offday('04/04/15') is False), "Date is holiday."

    assert (offday(datetime.strptime('2015-02-16', '%Y-%m-%d').date()) is True)

# todo: rework this into new format