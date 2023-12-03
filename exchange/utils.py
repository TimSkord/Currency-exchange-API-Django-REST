from collections import defaultdict
from decimal import Decimal
from typing import List, Dict, Tuple, Optional, Any

import pandas as pd
from django.http import Http404
from rest_framework import status
from rest_framework.generics import get_object_or_404
from rest_framework.response import Response
from rest_framework.views import exception_handler

from exchange.models import Currency, Exchange


def melt_data(df_raw: pd.DataFrame) -> pd.DataFrame:
    """
    Transforms a DataFrame of currency exchange rates into a melted format.

    Parameters:
    df_raw (pd.DataFrame): A DataFrame with currency exchange rates, where each column
                           represents a currency pair and each row represents a date.

    Returns:
    pd.DataFrame: A transformed DataFrame where each row contains a single record of
                  currency pair and its exchange rate for a date.
    """
    melted_df = df_raw.melt(id_vars=['Date'], var_name='currency_pair', value_name='price')
    melted_df[['base_currency', 'quote_currency']] = melted_df['currency_pair'].str.split('/', expand=True)
    final_df = melted_df[['Date', 'base_currency', 'quote_currency', 'price']]
    return final_df


def get_or_create_currency(tag: str) -> Currency:
    """
    Retrieves a Currency object by its tag, or creates a new one if it does not exist.

    Parameters:
    tag (str): The tag of the currency (e.g., 'USD').

    Returns:
    Currency: The retrieved or newly created Currency object.
    """
    currency, created = Currency.objects.get_or_create(tag=tag)
    return currency


def upload_csv(file_path: str) -> None:
    """
    Loads data from a CSV file and saves it to the database.

    Parameters:
    file_path (str): Path to the CSV file.
    """
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


def calculate_rate(base_currency_tag: str, quote_currency_tag: str, date: str) -> Optional[Decimal]:
    """
    Calculates the exchange rate for a given currency pair on a specific date.
    It tries to find a direct rate first; if not available, it calculates an indirect rate.

    Parameters:
    base_currency_tag (str): The tag of the base currency.
    quote_currency_tag (str): The tag of the quote currency.
    date (date): The date for the exchange rate.

    Returns:
    Optional[float]: The calculated exchange rate, or None if no rate is found.
    """
    #  I sacrifice two queries, but then everything goes on without JOIN.
    base_currency_id = get_object_or_404(Currency, tag=base_currency_tag).id
    quote_currency_id = get_object_or_404(Currency, tag=quote_currency_tag).id
    direct_rate = find_direct_rate(base_currency_id, quote_currency_id, date)
    if direct_rate is not None:
        return direct_rate

    return find_indirect_rate(base_currency_id, quote_currency_id, date)


def find_direct_rate(base_currency_id: int, quote_currency_id: int, date: str) -> Optional[Decimal]:
    """
    Attempts to find a direct exchange rate for a given currency pair on a specific date.

    Parameters:
    base_currency_id (int): The ID of the base currency.
    quote_currency_id (int): The ID of the quote currency.
    date (date): The date for which the exchange rate is needed.

    Returns:
    Optional[float]: The direct exchange rate if found, otherwise None.
    """
    try:
        exchange = Exchange.objects.get(
            base_currency=base_currency_id,
            quote_currency=quote_currency_id,
            date=date,
        )
        return exchange.price
    except Exchange.DoesNotExist:
        pass


def find_indirect_rate(base_currency_id: int, quote_currency_id: int, date: str) -> Decimal:
    """
    Finds an indirect exchange rate for a currency pair on a given date if a direct rate does not exist.
    It calculates the rate by finding possible conversion paths through other currencies and
    selecting the path with the minimum exchange rate.

    Parameters:
    base_currency_id (int): The ID of the base currency.
    quote_currency_id (int): The ID of the quote currency.
    date (str): The date for which the exchange rate is requested.

    Returns:
    float: The calculated indirect exchange rate.

    Raises:
    Http404: If no indirect path can be found for the currency conversion.
    """
    exchanges = Exchange.objects.filter(date=date)
    values = exchanges.values_list('base_currency', 'quote_currency', 'price')
    #  Oh yes, I use tuple as keys in the dictionary, first time it's come in handy!
    dict_of_rates = {(base_currency, quote_currency): price for base_currency, quote_currency, price in values}
    graph = build_graph(dict_of_rates.keys())
    paths = find_all_paths(graph, base_currency_id, quote_currency_id)
    best_rate = chose_best_rate(paths, dict_of_rates)
    if best_rate is None:
        raise Http404
    return Decimal(best_rate).quantize(Decimal('0.0001'))


def build_graph(connections: List[Tuple[int, int]]) -> Dict[int, List[int]]:
    """
    Builds a graph from a list of connections, where each connection is a tuple of two currency IDs.

    This function creates a bidirectional graph, meaning if there is a connection from A to B,
    there is also an implied connection from B to A.

    Parameters:
    connections (List[Tuple[int, int]]): A list of tuples where each tuple represents a connection
                                         between two currencies (by their IDs).

    Returns:
    Dict[int, List[int]]: A dictionary representing the graph. The keys are currency IDs and the values
                           are lists of IDs of currencies directly exchangeable with the key currency.
    """
    graph = defaultdict(list)
    for connection in connections:
        graph[connection[0]].append(connection[1])
        graph[connection[1]].append(connection[0])
    return graph


def find_all_paths(graph: Dict[int, List[int]], start: int, end: int, path: List[int] = []) -> List[List[int]]:
    """
    Finds all possible paths between two nodes (currencies) in a graph (currency conversion network).

    Parameters:
    graph (Dict[int, List[int]]): A graph representing currency conversion network where keys are currency IDs
                                  and values are lists of IDs of directly exchangeable currencies.
    start (int): The ID of the starting node (base currency).
    end (int): The ID of the ending node (quote currency).
    path (List[int], optional): The current path being explored. Defaults to an empty list.

    Returns:
    List[List[int]]: A list of all possible paths from start to end.
    """
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


def get_rate_by_path(path: List[int], dict_of_rates: Dict[Tuple[int, int], float]) -> float:
    """
    Calculates the exchange rate for a given conversion path.

    Parameters:
    path (List[int]): The conversion path as a list of currency IDs.
    dict_of_rates (Dict[Tuple[int, int], float]): Dictionary of available direct exchange rates.

    Returns:
    float: The calculated exchange rate for the given path.
    """
    rate = 1
    for i in range(len(path) - 1):
        key = tuple(path[i: i + 2])
        rate *= dict_of_rates.get(key) or 1 / dict_of_rates.get(key[::-1])
    return rate


def chose_best_rate(all_paths: List[List[int]], dict_of_rates: Dict[Tuple[int, int], float]) -> Optional[float]:
    """
    Chooses the best exchange rate from all available conversion paths.

    Parameters:
    all_paths (List[List[int]]): All possible conversion paths.
    dict_of_rates (Dict[Tuple[int, int], float]): Dictionary of available direct exchange rates.

    Returns:
    Optional[float]: The best exchange rate, or None if no valid paths are found.
    """
    rates = []
    for path in all_paths:
        price = get_rate_by_path(path, dict_of_rates)
        rates.append(price)
    if rates:  # If I understand correctly, we want the most favorable rate, not the fastest.
        return min(rates)


def custom_exception_handler(exc: Exception, context: Dict[str, Any]) -> Response:
    """
    A custom exception handler for Django REST Framework.

    This function provides a custom response for exceptions that are not handled by the default
    exception handler of Django REST Framework. If the default handler returns a response, it is used.
    Otherwise, a custom response with status 500 (Internal Server Error) is returned.

    Parameters:
    exc (Exception): The exception that was raised.
    context (Dict[str, Any]): A dictionary containing contextual information about the exception.

    Returns:
    Response: A Response object to be returned by the view.
    """
    response = exception_handler(exc, context)

    if response is None:
        return Response(
            {'detail': "When they promised everyone five hundred each, they obviously didn't mean it. "
                       "Internal server error. Sorry."},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
    return response
