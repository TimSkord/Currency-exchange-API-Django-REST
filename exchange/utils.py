from collections import defaultdict

import pandas as pd
from rest_framework.generics import get_object_or_404

from exchange.models import Currency, Exchange


def melt_data(df_raw):
    melted_df = df_raw.melt(id_vars=['Date'], var_name='currency_pair', value_name='price')
    melted_df[['base_currency', 'quote_currency']] = melted_df['currency_pair'].str.split('/', expand=True)
    final_df = melted_df[['Date', 'base_currency', 'quote_currency', 'price']]
    return final_df


def get_or_create_currency(tag):
    currency, created = Currency.objects.get_or_create(tag=tag)
    return currency


def upload_csv(file_path):
    df = pd.read_csv(file_path)
    data = melt_data(df)
    exchange_instances = []

    for record in data.to_dict(orient='records'):
        base_currency = get_or_create_currency(record['base_currency'])
        quote_currency = get_or_create_currency(record['quote_currency'])
        exchange_instance = Exchange(
            date=record['Date'],
            base_currency=base_currency,
            quote_currency=quote_currency,
            price=record['price']
        )
        exchange_instances.append(exchange_instance)

    Exchange.objects.bulk_create(exchange_instances)


def calculate_rate(base_currency_tag, quote_currency_tag, date):
    base_currency_id = get_object_or_404(Currency, tag=base_currency_tag).id
    quote_currency_id = get_object_or_404(Currency, tag=quote_currency_tag).id
    direct_rate = find_direct_rate(base_currency_id, quote_currency_id, date)
    if direct_rate is not None:
        return direct_rate

    return find_indirect_rate(base_currency_id, quote_currency_id, date)


def find_direct_rate(base_currency_id, quote_currency_id, date):
    try:
        exchange = Exchange.objects.get(
            base_currency=base_currency_id,
            quote_currency=quote_currency_id,
            date=date,
        )
        return exchange.price
    except Exchange.DoesNotExist:
        pass


def find_indirect_rate(base_currency_id, quote_currency_id, date):
    exchanges = Exchange.objects.filter(date=date)
    values = exchanges.values_list('base_currency', 'quote_currency', 'price')
    dict_of_rates = {(c1, c2): p for c1, c2, p in values}
    graph = build_graph(dict_of_rates.keys())
    paths = find_all_paths(graph, base_currency_id, quote_currency_id)
    best_rate = chose_best_rate(paths, dict_of_rates)
    return round(best_rate, 4)


def build_graph(connections):
    graph = defaultdict(list)
    for connection in connections:
        graph[connection[0]].append(connection[1])
        graph[connection[1]].append(connection[0])
    return graph


def find_all_paths(graph, start, end, path=[]):
    path = path + [start]
    if start == end:
        return [path]
    if start not in graph:
        return []
    paths = []
    for node in graph[start]:
        if node not in path:
            new_paths = find_all_paths(graph, node, end, path)
            for p in new_paths:
                paths.append(p)
    return paths


def get_rate_by_path(path, dict_of_rates):
    rate = 1
    for i in range(len(path) - 1):
        key = tuple(path[i: i + 2])
        rate *= dict_of_rates.get(key) or 1 / dict_of_rates.get(key[::-1])
    return rate


def chose_best_rate(all_paths, dict_of_rates):
    rates = []
    for path in all_paths:
        price = get_rate_by_path(path, dict_of_rates)
        rates.append(price)
    if rates:
        return min(rates)
