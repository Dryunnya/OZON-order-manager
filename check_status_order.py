import requests
import json
from token_site import OZON_HEADERS
from connect_Ozon_Sclad_productid import id_connect
from ozon_get import unpaid_production
from exceptions_test import handle_exceptions

# from loggirovanie import log_
from datetime import datetime, timedelta

check_order = id_connect()

state_sp = ['awaiting_packaging', 'awaiting_deliver']  # УБРАТЬ delivered, ОН ТЕСТОВЫЙ
UNPAID = unpaid_production()
""" Смотрим какие заказы были проведены исходя их статуса, который занесён в state_sp. 
Для наших целей достаточно проверять заказы со статусом awaiting_registration """


def momentu_yesterday():
    ''' Формирует дату вчерашнего '''
    yesterday = datetime.now() - timedelta(days=2)
    datetime_string = yesterday.strftime('%Y-%m-%d')
    return datetime_string


def momentu_today():
    ''' Формирует дату проверки в какой момент сформировлся заказ '''
    current_datetime = datetime.now()
    datetime_string = current_datetime.strftime('%Y-%m-%d')
    return datetime_string


@handle_exceptions
def delivered_order_list(status, date_since, date_to):
    ''' Вытаскивает товары с разними статусами '''
    offset = 0
    limit = 1000
    all_postings = []
    with requests.Session() as session:
        data = {
            "dir": "ASC",
            "filter": {
                "delivery_method_id": [],
                "is_quantum": False,
                "order_id": 0,
                "provider_id": [],
                "since": f'2025-01-03T00:00:00Z',
                "status": status,
                "to": f'{date_to}T23:59:59Z',
                "warehouse_id": []
            },
            "limit": limit,
            "offset": offset,
            "with": {
                "analytics_data": True,
                "barcodes": True,
                "financial_data": True,
                "translit": True
            }
        }
        url = 'https://api-seller.ozon.ru/v3/posting/fbs/list'
        req = requests.Request('POST', url, headers=OZON_HEADERS, data=json.dumps(data))
        prepped = session.prepare_request(req)
        response = session.send(prepped)
        response.raise_for_status()
        response_json = response.json()
        '''настроилл пагинацию (переход по страницам)'''
        postings = response_json.get('result', {}).get('postings', [])  # Возвращаем пустой список если postings нет
        if not postings:
            return all_postings  # Выходим, если больше нет данных

        all_postings.extend(postings)
        offset += limit

        if len(postings) < limit:
            return all_postings


# статусы совпадают поскольку, нет отдельного статуса похволяюшего рассмотреть 'driver_pickup'
status_dct = {
    'awaiting_packaging': 'f4d2a9bd-a7bd-11ed-0a80-068a00169c56',
    'awaiting_deliver': 'f4d2a9bd-a7bd-11ed-0a80-068a00169c56'}

'''Добавил глобальную переменную date_unpaid, чтобы задать время для закзов, которые ещё не были оплачены'''
date_unpaid = None


def purchases():
    global date_unpaid
    '''Обрабатываем товар со статусом и неоплаченные товары, объединяя их при необходимости.'''
    SCLAD_PURCHASE = {}

    # Обрабатываем заказы по статусам
    for status in state_sp:
        if status == 'driver_pickup':
            order_list = {status: delivered_order_list(status, momentu_today(), momentu_today())}
        else:
            order_list = {status: delivered_order_list(status, momentu_yesterday(), momentu_today())}
        delivered_orders = order_list.get(status)
        if delivered_orders:
            for order in delivered_orders:
                date_unpaid = order.get('shipment_date')
                for product in order.get('products', []):
                    offer_id = product.get('offer_id')
                    if offer_id in check_order:
                        status_value = status_dct.get(status)
                        if status_value not in SCLAD_PURCHASE:
                            SCLAD_PURCHASE[status_value] = {}
                        # Проверка, есть ли уже товар в структуре
                        if offer_id in SCLAD_PURCHASE[status_value]:
                            # Если есть, увеличиваем quantity
                            SCLAD_PURCHASE[status_value][offer_id]['quantity'] += product.get('quantity')
                        else:
                            # Если нет, добавляем новую запись
                            SCLAD_PURCHASE[status_value][offer_id] = {
                                'product_id': check_order[offer_id].get('product_id'),
                                'price': product.get('price'),
                                'quantity': product.get('quantity'),
                                'moment': order.get('shipment_date'),
                            }

    # Обрабатываем неоплаченные товары
    for tovar in UNPAID:
        offer_id = tovar['offer_id']
        # print(tovar['product_id'])
        # print('price', str(check_order[offer_id]['price']/100), check_order[offer_id]) # неоплаченный товар и его цена
        if offer_id in SCLAD_PURCHASE['f4d2a9bd-a7bd-11ed-0a80-068a00169c56']:
            # Уже есть, увеличиваем quantity
            SCLAD_PURCHASE['f4d2a9bd-a7bd-11ed-0a80-068a00169c56'][offer_id]['quantity'] += tovar['quantity']
        else:
            # Нет, добавляем новую запись
            SCLAD_PURCHASE['f4d2a9bd-a7bd-11ed-0a80-068a00169c56'][offer_id] = {
                'product_id': check_order[offer_id]['product_id'],
                'price': f"{str(check_order[offer_id]['price'] / 100)}000",
                'quantity': tovar['quantity'],
                'moment': date_unpaid,
            }

    return SCLAD_PURCHASE


if __name__ == '__main__':
    print(json.dumps(purchases(), indent=4, ensure_ascii=False))
