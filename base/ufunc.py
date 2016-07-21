def remove_comma(line):
    """
    Replace comma inside str line
    :param line: str
    :return: str
    """
    if '"' in line:
        values = line.split('"')
        for k, i in enumerate(values):
            if k % 2 and ',' in i:
                values[k] = i.replace(',', '')

        line = ''.join(values)
    return line


def remove_bracket(line):
    """
    Remove brackets on first item of a list
    :param line: str
    :return: str
    """
    return line.replace('(', '').replace(')', '')


def make_dict(key, values):
    """
    Make a dict join together key and values
    :param key: list
    :param values: list
    :return: dict
    """
    return {k: v for k, v in zip(key, values)}


def ts(df):
    """
    Output dataframe
    :param df: pd.DataFrame
    """
    print df.to_string(line_width=1000)