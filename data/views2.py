from django.shortcuts import render
import pandas as pd
from data.plugin.clean.clean import *
from rivers.settings import QUOTE


def clean_option(request, symbol):
    """

    :param request:
    :param symbol:
    :return:
    """
    db = pd.HDFStore(QUOTE)
    df_rate = db.select('treasury/RIFLGFCY01_N_B')['rate']  # series
    df_stock = db.select('stock/thinkback/%s' % symbol.lower())
    df_close = df_stock['close']  # series
    df_contract = db.select('option/%s/contract' % symbol.lower())
    df_option = db.select('option/%s/raw' % symbol.lower())
    df_option = df_option.reset_index()
    try:
        df_dividend = db.select('event/dividend/%s' % symbol.lower())
        div_yield = get_div_yield(df_stock, df_dividend)
    except KeyError:
        div_yield = pd.Series(
            np.zeros(len(df_stock)), index=df_stock.index
        )

    db.close()
    db.close()

    #df_contract = df_contract[df_contract['option_code'] == 'AIG170120C50']
    #df_contract = df_contract[df_contract['option_code'] == 'AIG160115C90']

    df_new = pd.DataFrame()
    output = 'U | %-16s | %s: %s => %s' % ('update', '%-12s', '%6.2f', '%6.2f')
    for _, c in df_contract.iterrows():
        # check is same symbol
        if symbol.upper() not in c['option_code']:
            print 'C | %-16s | skip: symbol is not match' % c['option_code']
            raise ValueError('Invalid symbol in option_code: %s' % c['option_code'])

        df_data = df_option[df_option['option_code'] == c['option_code']]
        df_data = df_data.sort_index()

        print 'C | %-16s | length: %d, right: %s, special: %s, others: %s' % (
            c['option_code'], len(df_data), c['right'], c['special'], c['others']
        )

        for __, data in df_data.iterrows():
            index = data['date']
            print 'I | %-16s | close: %.2f, bid: %.2f, ask %.2f' % (
                index.strftime('%Y-%m-%d'), df_close[index], data['bid'], data['ask']
            )
            try:
                calc = CleanOption(
                    option_code=data['option_code'],
                    today=index,
                    rf_rate=df_rate[index],
                    close=df_close[index],
                    bid=data['bid'],
                    ask=data['ask'],
                    impl_vol=data['impl_vol'] if data['impl_vol'] > 0 else 0.01,
                    div=div_yield[index]
                    # div=d
                )
            except IndexError as e:
                print 'E | %-16s | skip: %s' % (index.strftime('%Y-%m-%d'), e.message)
                continue

            # only price greater than 0.1 then will clean
            if data['ask'] < 0.05:
                print 'D | %-16s | skip: ask price less than 0.05 skip: %6.2f' % (
                    index.strftime('%Y-%m-%d'), data['ask']
                )
                continue

            # get iv is no available
            if data['impl_vol'] == 0:
                try:
                    impl_vol = calc.get_impl_vol(True)
                    print output % ('impl_vol', data['impl_vol'], impl_vol)
                    df_data.loc[df_data['date'] == index, 'impl_vol'] = impl_vol
                except ValueError as e:
                    print 'E | %-16s | skip: %s' % (index.strftime('%Y-%m-%d'), e.message)

            # theory price
            if data['theo_price'] == 0:
                theo_price = calc.theo_price()
                print output % ('theo_price', data['theo_price'], theo_price)
                df_data.loc[df_data['date'] == index, 'theo_price'] = theo_price

            # greek
            greek = calc.greek()
            prob = calc.prob()

            greek_count = 0
            for key in ['delta', 'gamma', 'theta', 'vega']:
                if data[key] == 0:
                    greek_count += 1
            else:
                if greek_count == 4:
                    print output % ('delta', data['delta'], greek['delta'])
                    print output % ('gamma', data['gamma'], greek['gamma'])
                    print output % ('theta', data['theta'], greek['theta'])
                    print output % ('vega', data['vega'], greek['vega'])
                    df_data.loc[df_data['date'] == index, 'delta'] = np.float(greek['delta'])
                    df_data.loc[df_data['date'] == index, 'gamma'] = greek['gamma']
                    df_data.loc[df_data['date'] == index, 'theta'] = greek['theta']
                    df_data.loc[df_data['date'] == index, 'vega'] = greek['vega']

            # probability
            prob_count = 0
            for key in ['prob_itm', 'prob_otm', 'prob_touch']:
                if data[key] == 0:
                    prob_count += 1
            else:
                if prob_count == 3:
                    print output % ('prob_itm', data['prob_itm'], prob['prob_itm'])
                    print output % ('prob_otm', data['prob_otm'], prob['prob_otm'])
                    print output % ('prob_touch', data['prob_touch'], prob['prob_touch'])
                    df_data.loc[df_data['date'] == index, 'prob_itm'] = prob['prob_itm']
                    df_data.loc[df_data['date'] == index, 'prob_otm'] = prob['prob_otm']
                    df_data.loc[df_data['date'] == index, 'prob_touch'] = prob['prob_touch']

            # intrinsic, extrinsic
            intrinsic, extrinsic = calc.moneyness()
            if data['extrinsic'] <= 0:
                print output % ('extrinsic', data['extrinsic'], extrinsic)
                df_data.loc[df_data['date'] == index, 'extrinsic'] = extrinsic

            if data['intrinsic'] <= 0:
                print output % ('intrinsic', data['intrinsic'], intrinsic)
                df_data.loc[df_data['date'] == index, 'intrinsic'] = intrinsic

            # day to expire
            dte = calc.dte()
            if data['dte'] != dte:
                print output % ('dte', data['dte'], dte)
                df_data.loc[df_data['date'] == index, 'dte'] = dte
                #exit()

        # add back into df_new
        df_new = pd.concat([df_new, df_data])

        print ''

    # insert back into db
    if len(df_new):
        db = pd.HDFStore(QUOTE)
        try:
            db.remove('option/%s/data' % symbol.lower())
        except KeyError:
            pass
        db.append('option/%s/data' % symbol.lower(), df_new)
        db.close()
        # print df_new.to_string(line_width=500)

    template = 'data/clean_option.html'
    parameters = dict(
        site_title='Clean option data',
        title='Clean option data: %s' % symbol.upper(),
        symbol=symbol.upper(),
    )

    return render(request, template, parameters)


def clean_option2(request, symbol):
    """
    Speed up version of clean option data
    :param request: request
    :param symbol: str
    :return: render
    """
    db = pd.HDFStore(QUOTE)
    df_rate = db.select('treasury/RIFLGFCY01_N_B')['rate']  # series
    df_stock = db.select('stock/thinkback/%s' % symbol.lower())
    df_close = df_stock['close']  # series
    df_contract = db.select('option/%s/contract' % symbol.lower())
    df_option = db.select('option/%s/raw' % symbol.lower())
    df_option = df_option.reset_index()
    try:
        df_dividend = db.select('event/dividend/%s' % symbol.lower())
        div_yield = get_div_yield(df_stock, df_dividend)
    except KeyError:
        div_yield = pd.Series(
            np.zeros(len(df_stock)), index=df_stock.index
        )

    db.close()

    #import numba
    #@numba.jit
    def clean(x):
        raw = ','.join(map(lambda x: str(round(x, 4)), [
            x['impl_vol'], x['theo_price'],
            x['intrinsic'], x['extrinsic'], x['dte'],
            x['prob_itm'], x['prob_otm'], x['prob_touch'],
            x['delta'], x['gamma'], x['theta'], x['vega']
        ]))
        try:
            c = CleanOption(
                option_code=x['option_code'],
                today=x['date'],
                rf_rate=df_rate[x['date']],
                close=df_close[x['date']],
                bid=x['bid'],
                ask=x['ask'],
                impl_vol=x['impl_vol'] if x['impl_vol'] > 0 else 0.01,
                div=div_yield[x['date']]
                # div=d
            )

            impl_vol = x['impl_vol']
            if x['impl_vol'] == 0:
                try:
                    impl_vol = c.get_impl_vol(True)
                except ValueError:
                    pass  # get iv is no available

            theo_price = x['theo_price']
            if x['theo_price'] == 0:
                theo_price = c.theo_price() + 0

            intrinsic = x['intrinsic']
            extrinsic = x['extrinsic']
            i, e = c.moneyness()
            if x['intrinsic'] <= 0:
                intrinsic = i
            if x['extrinsic'] <= 0:
                extrinsic = e

            dte = x['dte']
            if dte != c.dte():
                dte = c.dte()

            prob_itm = x['prob_itm']
            prob_otm = x['prob_otm']
            prob_touch = x['prob_touch']
            prob = c.prob()
            prob_count = 0
            for key in ['prob_itm', 'prob_otm', 'prob_touch']:
                if x[key] == 0:
                    prob_count += 1

            if prob_count == 3:
                prob_itm = prob['prob_itm']
                prob_otm = prob['prob_otm']
                prob_touch = prob['prob_touch']

            delta = x['delta']
            gamma = x['gamma']
            theta = x['theta']
            vega = x['vega']
            greek = c.greek()
            greek_count = 0
            for key in ['delta', 'gamma', 'theta', 'vega']:
                if x[key] == 0:
                    greek_count += 1

            if greek_count == 4:
                delta = greek['delta']
                gamma = greek['gamma']
                theta = greek['theta']
                vega = greek['vega']

            raw = ','.join(map(lambda x: str(round(x, 4)), [
                impl_vol, theo_price, intrinsic, extrinsic, dte,
                prob_itm, prob_otm, prob_touch, delta, gamma, theta, vega
            ]))
        except IndexError:
            pass

        return raw

    # start
    df_c100 = df_contract.head(100)
    df_all = pd.merge(df_option, df_c100, how='inner', on=['option_code'])
    #print df_all.to_string(line_width=500)

    print df_all.apply(clean, axis=1)

    #print df_all.to_string(line_width=500)

    template = 'data/clean_option.html'
    parameters = dict(
        site_title='Clean option data',
        title='Clean option data: %s' % symbol.upper(),
        symbol=symbol.upper(),
    )

    return render(request, template, parameters)



# todo: also too slow find solution