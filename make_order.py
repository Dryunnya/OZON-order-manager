import requests
import json
from datetime import datetime

from token_site import ORGANIZATION_ID, COUNTERPARTY_ID
from connect_Ozon_Sclad_productid import id_connect
from token_site import SCLAD_HEADERS
from check_status_order import purchases
from shipment_sclad import update_ozon_stocks
from token_site import get_all_tokens
from exceptions_test import handle_exceptions

# from loggirovanie import log_

get_all_tokens()

""" Константа содержащая в себе смежную информацию о товаре из МоЙ Склад и Ozon. 
То есть сращивае OFFER_DCT озона с информацией из моего склада также совпадающей по OFER_DCT."""
OFFER_DCT = id_connect()


# COUNTERPARTY_ID = "49637d54-d77c-11ef-0a80-19c6003757d4"  # ID контрагента для запросов
# COUNTERPARTY_ID = "e876f867-62a6-11ee-0a80-1094000cda45"  # ID контрагента для запросов


def order_list():
    """
    Получает все заказы, используя пагинацию.
    """
    orders = []
    limit = 1000  # Максимальное число элементов за один запрос
    offset = 0

    while True:
        params = {
            "limit": limit,
            "offset": offset
        }
        url = "https://api.moysklad.ru/api/remap/1.2/entity/customerorder"

        response = requests.get(url=url, headers=SCLAD_HEADERS, params=params)
        if response.status_code != 200:
            print(f"Ошибка при получении заказов: {response.status_code} {response.text}")
            break
        data = response.json()
        rows = data.get('rows', [])
        if not rows:
            break
        orders.extend(rows)
        if len(rows) < limit:
            break
        offset += limit

    return orders


@handle_exceptions
def get_max_order_number():
    """
    Обходит все заказы и ищет максимальный числовой номер заказа.
    """
    orders = order_list()
    max_number = 0
    for order in orders:
        name = order.get('name')
        try:
            num = int(name)
            if num > max_number:
                max_number = num
        except (ValueError, TypeError):
            continue
    return str(max_number + 1)


print(get_max_order_number())


def momentum():
    ''' Формирует дату создания заказа '''
    current_datetime = datetime.now()
    datetime_string = current_datetime.strftime('%Y-%m-%d %H:%M:%S')
    return datetime_string


@handle_exceptions
def get_all_orders(COUNTERPARTY_ID):
    all_orders = []
    url = "https://api.moysklad.ru/api/remap/1.2/entity/customerorder"
    params = {
        "limit": 1000,
        "offset": 0,
        'filter': f'agent=https://api.moysklad.ru/api/remap/1.2/entity/counterparty/{COUNTERPARTY_ID};organization=https://api.moysklad.ru/api/remap/1.2/entity/organization/{ORGANIZATION_ID}'
    }

    with requests.Session() as session:
        while True:
            response = session.get(url, headers=SCLAD_HEADERS, params=params)
            if response.status_code != 200:
                print(f"Ошибка при получении заказов: {response.status_code} {response.text}")
                break
            data = response.json()
            rows = data.get('rows', [])
            if not rows:
                break
            all_orders.extend(rows)

            # Проверяем, есть ли следующая страница
            meta = data.get('meta', {})
            if 'nextPage' in meta and meta['nextPage']:
                # например, meta['nextPage'] содержит следующий offset
                params['offset'] = meta['nextPage']
            else:
                # Нет следующей страницы
                break
    return all_orders


@handle_exceptions
def delete_order(order_id):
    """Удаляет заказ по ID."""
    url = f"https://api.moysklad.ru/api/remap/1.2/entity/customerorder/{order_id}"

    params = {
        'limit': 0,
        'offset': 100,
    }
    response = requests.delete(url, headers=SCLAD_HEADERS, params=params)
    response.raise_for_status()
    print(f"Заказ с ID {order_id} успешно удален.")
    return True


@handle_exceptions
def make_an_order(status_ord, items_data):
    with requests.Session() as session:
        while True:
            positions = []
            state_dct = {"meta": {
                "href": f"https://api.moysklad.ru/api/remap/1.2/entity/customerorder/metadata/states/{status_ord}",
                "type": "state",
                "mediaType": "application/json"}}
            store_id = {"meta": {
                "href": f"https://api.moysklad.ru/api/remap/1.2/entity/store/f4993c8f-a7bd-11ed-0a80-068a00169c2f",
                "type": "store",
                "mediaType": "application/json"}}
            for offer_id, purchase in items_data.items():
                positions.append({
                    "quantity": purchase['quantity'],
                    # 'warehouse': store_id,
                    "price": float(purchase['price']) * 100,  # Converts to float before using.
                    "discount": 0,
                    "vat": 0,
                    "assortment": {
                        "meta": {
                            "href": f"https://api.moysklad.ru/api/remap/1.2/entity/product/{purchase['product_id']}",
                            "type": "product",
                            "mediaType": "application/json"
                        }
                    },
                    "reserve": purchase['quantity']
                })
            contract_id = "46a27495-2cfc-11ef-0a80-022e00317aa5"
            data = {
                "name": get_max_order_number(),
                "organization": {
                    "meta": {
                        "href": f"https://api.moysklad.ru/api/remap/1.2/entity/organization/{ORGANIZATION_ID}",
                        "type": "organization",
                        "mediaType": "application/json"
                    }
                },
                "moment": momentum(),
                "applicable": True,
                "vatEnabled": False,
                "agent": {
                    "meta": {
                        "href": f"https://api.moysklad.ru/api/remap/1.2/entity/counterparty/{COUNTERPARTY_ID}",
                        "type": "counterparty",
                        "mediaType": "application/json"
                    },
                },
                'state': state_dct,
                "positions": positions,
                'store': store_id,
                "contract": {  # Добавляем информацию о договоре
                    "meta": {
                        "href": f"https://api.moysklad.ru/api/remap/1.2/entity/contract/{contract_id}",
                        "type": "contract",
                        "mediaType": "application/json"
                    }
                }
            }
            url = 'https://api.moysklad.ru/api/remap/1.2/entity/customerorder'
            response = requests.Request('POST', url=url, headers=SCLAD_HEADERS, data=json.dumps(data))
            prepped = session.prepare_request(response)
            response = session.send(prepped)
            response.raise_for_status()
            response_json = response.json()
            update_ozon_stocks()
            return response_json.get('id')


if __name__ == '__main__':
    """ Передаем в ф-цию создания заказа всю необходимую информаци: 
    id продукта, его цену, дату создания заказа, количество заказанного товара."""
    items = purchases()  # Функция, которая возвращает данные о товарах

    orders = get_all_orders(COUNTERPARTY_ID)
    if orders is not None:
        target_status = {'awaiting_deliver': 'f4d2aabf-a7bd-11ed-0a80-068a00169c58'}
        print(f"Найдено {len(orders)} заказов.")
        for status_ord, elem in items.items():
            #  Ищем заказы с нужной датой и статусом
            existing_order = None
            for order in orders:
                try:
                    order_state_href = order.get("state", {}).get("meta", {}).get('href', '')
                    order_status = order_state_href.split('/')[-1]
                    if order_status == status_ord:
                        existing_order = order
                        target_id = order.get('id')
                        break  # Нашли нужный заказ, выходим из цикла
                except ValueError:
                    print(
                        f"Предупреждение: Неверный формат даты в заказе с ID: {order.get('id')}. Пропускаем этот заказ.")
                    continue
            if existing_order and status_ord == target_status['awaiting_deliver']:
                print(
                    f"Заказ с ID {target_id} и статусом {status_ord} найден. Пропускаем, так как заказ уже передан курьеру.")
                continue  # Skip to the next status_ord in the outer loop
            if existing_order:
                print(f"Заказ с ID {target_id} и статусом {status_ord} найден. Удаляем...")
                if delete_order(target_id):
                    print(f"Заказ с ID {target_id} успешно удален. Создаем новый...")
                    new_order_id = make_an_order(status_ord, elem)
                    if new_order_id:
                        print(f"Новый заказ успешно создан с ID: {new_order_id}")
                    else:
                        print("Не удалось создать новый заказ.")
                else:
                    print("Не удалось удалить существующий заказ.")
            else:
                print(f"Заказ со статусом {status_ord} не найден. Создаем новый...")
                new_order_id = make_an_order(status_ord, elem)
                if new_order_id:
                    print(f"Новый заказ успешно создан с ID: {new_order_id}")
                else:
                    print("Не удалось создать новый заказ.")
        else:
            print("Все заказы обработаны.")
