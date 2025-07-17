import requests
from token_site import SCLAD_HEADERS
import json
from ozon_get import ozon_production

# from loggirovanie import log_

ozon = ozon_production()
ozon_offer_id = []
for elem in ozon:
    ozon_offer_id.append([elem['offer_id'], elem['name']])


def get_product_info(product_id):
    """Получает полную информацию о товаре по его ID из МоегоСклада."""
    url_product = f"https://api.moysklad.ru/api/remap/1.2/entity/product/{product_id}"
    response_product = requests.get(url=url_product, headers=SCLAD_HEADERS)
    if response_product.status_code == 200:
        return response_product.json()
    else:
        print(
            f"Ошибка получения данных о продукте {product_id}: {response_product.status_code} - {response_product.text}")
        return None


def find_product_by_ozon_article(ozon_article):
    """Ищет товар в МоемСкладе по значению атрибута 'артикул для ОЗОНА'."""
    limit = 1000
    offset = 0
    while True:
        params = (
            ("limit", limit),
            ("offset", offset),
            ("search", ozon_article)
        )
        url_list = f"https://api.moysklad.ru/api/remap/1.2/entity/product"
        response_list = requests.get(url=url_list, headers=SCLAD_HEADERS, params=params)
        if response_list.status_code == 200:
            products_list = response_list.json()
            if 'rows' in products_list and products_list['rows']:
                for product in products_list['rows']:
                    for attribute in product.get('attributes', []):
                        if attribute.get('name') == 'артикул для ОЗОНА' and attribute.get('value') == ozon_article:
                            return product['id']  # Нашли соответствие
                offset += limit
            else:
                break  # Больше нет товаров
        else:
            print(f"Ошибка при получении списка товаров: {response_list.status_code} - {response_list.text}")
            return None  # Ошибка при запросе
    return None  # Не нашли товар с таким offer_id


def get_product_name(product_id):
    """Получает название товара по ID."""
    url = f"https://api.moysklad.ru/api/remap/1.2/entity/product/{product_id}"
    response = requests.get(url, headers=SCLAD_HEADERS)
    if response.status_code == 200:
        product_data = response.json()
        return product_data.get("name", "Неизвестный товар")  # Возвращаем имя, если есть, иначе "Неизвестный товар"
    else:
        return "Неизвестный товар"


def get_stock_data(product_id):
    """Получает данные о запасах и резервах для конкретного товара."""
    url = f"https://api.moysklad.ru/api/remap/1.2/report/stock/bystore?filter=product=https://api.moysklad.ru/api/remap/1.2/entity/product/{product_id}"
    response = requests.get(url, headers=SCLAD_HEADERS)
    if response.status_code == 200:
        return response.json()
    else:
        print(
            f"Ошибка при получении данных о запасах для {get_product_name(product_id)}: {response.status_code} - {response.text}")
        return None


def calculate_available_stock(product_id):
    """Рассчитывает доступные остатки для товара (запас - резерв)."""
    stock_data = get_stock_data(product_id)
    if stock_data and 'rows' in stock_data and stock_data['rows']:
        total_stock = 0
        total_reserved = 0
        for item in stock_data['rows']:
            total_stock += item.get('stockByStore')[0].get('stock', 0)  # Суммируем запасы по всем складам
            total_reserved += item.get('stockByStore')[0].get('reserve', 0)  # Суммируем резервы по всем складам

        available_stock = total_stock - total_reserved

        product_stock_data = {
            'product_id': product_id,
            'stock': total_stock,
            'reserved': total_reserved,
            'available': available_stock,
        }
        # print(product_stock_data)
        return product_stock_data
    else:
        print(f'Нет данных о запасах для "{get_product_name(product_id)}" или ошибка в формате данных.')
        return None


def mysclad_production():
    offer_id_to_product_id = {}
    for offer_id in ozon_offer_id:
        product_id = find_product_by_ozon_article(offer_id[0])  # Ищем товар по offer_id
        if product_id:
            offer_id_to_product_id[offer_id[0]] = product_id  # Записываем в словарь
            print(f"Найдено соответствие: offer_id={offer_id[0]} -> name={offer_id[1]}")
        else:
            print(f"Не найдено товара с offer_id={offer_id[0]}: {offer_id[1]}")
    all_products = []
    for offer_id, product_id in offer_id_to_product_id.items():
        product_data = get_product_info(product_id)  # Получаем полную информацию
        if product_data:
            # Рассчитываем остатки
            stock_info = calculate_available_stock(product_id)
            if stock_info:
                stock = stock_info.get('stock')
                reserved = stock_info.get('reserved')
                available = stock_info.get('available')
            else:
                # Устанавливаем значения по умолчанию, если stock_info равно None
                stock = 0
                reserved = 0
                available = 0
            product_info = {
                'product_id': product_data['id'],
                'Name': product_data.get('name'),
                'price': product_data.get('salePrices')[0].get('value'),
                'артикул для ОЗОНА': next((attr.get('value') for attr in product_data.get('attributes', []) if
                                           attr.get('name') == 'артикул для ОЗОНА'), None),
                'Расчёт остатков': next((attr.get('value') for attr in product_data.get('attributes', []) if
                                         attr.get('name') == 'Функция Расчёт Остатков'), None),
                "stock": stock,
                "reserved": reserved,
                "available": available,
            }
            all_products.append(product_info)
    return all_products


ALL_SCLAD_PRODUCTS = mysclad_production()
# 4. Вывод результатов
if __name__ == '__main__':
    for product in ALL_SCLAD_PRODUCTS:
        print(json.dumps(product, indent=4, ensure_ascii=False))
