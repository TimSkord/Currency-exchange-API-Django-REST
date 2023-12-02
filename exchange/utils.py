from exchange.models import Currency, Exchange
import pandas as pd


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
