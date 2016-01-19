from datetime import datetime, date

market_holiday = [
    ("New Year's Day", '2015-01-01'),
    ('Martin Luther King, Jr. Day', '2015-01-19'),
    ("Washington's Birthday", '2015-02-17'),
    ('Good Friday', '2015-04-28'),
    ('Memorial Day', '2015-05-25'),
    ('Independence Day', '2015-07-04'),
    ('Labor Day', '2015-09-01'),
    ('Thanksgiving Day', '2015-11-27'),
    ('Christmas Day', '2015-12-25'),
    ("New Year's Day", '2014-01-01'),
    ('Martin Luther King, Jr. Day', '2014-01-20'),
    ("Washington's Birthday", '2014-02-17'),
    ('Good Friday', '2014-04-18'),
    ('Memorial Day', '2014-05-26'),
    ('Independence Day', '2014-07-04'),
    ('Labor Day', '2014-09-01'),
    ('Thanksgiving Day', '2014-11-27'),
    ('Christmas Day', '2014-12-25'),
    ("New Year's Day", '2013-01-01'),
    ('Martin Luther King, Jr. Day', '2013-01-21'),
    ("Washington's Birthday", '2013-02-18'),
    ('Good Friday', '2013-03-29'),
    ('Memorial Day', '2013-05-27'),
    ('Independence Day', '2013-07-04'),
    ('Labor Day', '2013-09-02'),
    ('Thanksgiving Day', '2013-11-28'),
    ('Christmas Day', '2013-12-25'),
    ("New Year's Day", '2012-01-02'),
    ('Martin Luther King, Jr. Day', '2012-01-16'),
    ("Washington's Birthday", '2012-02-20'),
    ('Good Friday', '2012-04-06'),
    ('Memorial Day', '2012-05-28'),
    ('Independence Day', '2012-07-04'),
    ('Labor Day', '2012-09-03'),
    ('Thanksgiving Day', '2012-11-22'),
    ('Christmas Day', '2012-12-25'),
    ("New Year's Day", '2011-01-01'),
    ('Martin Luther King, Jr. Day', '2011-01-17'),
    ("Washington's Birthday", '2011-02-21'),
    ('Good Friday', '2011-04-22'),
    ('Memorial Day', '2011-05-30'),
    ('Independence Day', '2011-07-04'),
    ('Labor Day', '2011-09-05'),
    ('Thanksgiving Day', '2011-11-24'),
    ('Christmas Day', '2011-12-26'),
    ("New Year's Day", '2010-01-01'),
    ('Martin Luther King, Jr. Day', '2010-01-18'),
    ("Washington's Birthday", '2010-02-15'),
    ('Good Friday', '2010-04-02'),
    ('Memorial Day', '2010-05-31'),
    ('Independence Day', '2010-07-05'),
    ('Labor Day', '2010-09-06'),
    ('Thanksgiving Day', '2010-11-25'),
    ('Christmas Day', '2010-12-24'),
    ("New Year's Day", '2009-01-01'),
    ('Martin Luther King, Jr. Day', '2009-01-19'),
    ("Washington's Birthday", '2009-02-16'),
    ('Good Friday', '2009-04-10'),
    ('Memorial Day', '2009-05-25'),
    ('Independence Day', '2009-07-03'),
    ('Labor Day', '2009-09-07'),
    ('Thanksgiving Day', '2009-11-26'),
    ('Christmas Day', '2009-12-25'),
    ("New Year's Day", '2008-01-01'),
    ('Martin Luther King, Jr. Day', '2008-01-21'),
    ("Washington's Birthday", '2008-02-18'),
    ('Good Friday', '2008-03-21'),
    ('Memorial Day', '2008-05-26'),
    ('Independence Day', '2008-07-04'),
    ('Labor Day', '2008-09-01'),
    ('Thanksgiving Day', '2008-11-27'),
    ('Christmas Day', '2008-12-25'),
    ("New Year's Day", '2007-01-01'),
    ('Martin Luther King, Jr. Day', '2007-01-15'),
    ("President's Day", '2007-02-19'),
    ('Good Friday', '2007-04-06'),
    ('Memorial Day', '2007-05-28'),
    ('Independence Day', '2007-07-04'),
    ('Labor Day', '2007-09-03'),
    ('Thanksgiving Day', '2007-11-22'),
    ('Christmas Day', '2007-12-25'),
    ("New Year's Day", '2006-01-02'),
    ('Martin Luther King, Jr. Day', '2006-01-16'),
    ("President's Day", '2006-02-20'),
    ('Good Friday', '2006-04-14'),
    ('Memorial Day', '2006-05-29'),
    ('Independence Day', '2006-07-04'),
    ('Labor Day', '2006-09-04'),
    ('Thanksgiving Day', '2006-11-23'),
    ('Christmas Day', '2006-12-25')
]

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


def holiday(d):
    """
    Return true if date is holiday
    :param d: str or datetime or date
    :return: boolean
    """
    if type(d) in (datetime, date):
        d = d.strftime('%Y-%m-%d')

    return True if d in [h for _, h in market_holiday] else False


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
    assert (holiday('2015-11-27') is True), "Date is not holiday."
    assert (holiday('2013-09-03') is False), "Date is holiday."

    assert (holiday(datetime.strptime('2015-01-19', '%Y-%m-%d').date()) is True)

    assert (offday('07/18/2014') is True), "Date is not holiday."
    assert (offday('04/04/2015') is False), "Date is holiday."

    assert (offday(datetime.strptime('2015-02-16', '%Y-%m-%d').date()) is True)
