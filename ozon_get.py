import requests
from token_site import OZON_HEADERS
import json
from exceptions_test import handle_exceptions


@handle_exceptions
def get_product_details(offer_id, session):
    """ Извлекает доп.информацию о заказе """
    url = "https://api-seller.ozon.ru/v1/product/info/description"
    data = {"offer_id": offer_id}
    req = requests.Request('POST', url, headers=OZON_HEADERS, data=json.dumps(data))

    # call function of logging
    # log_(f"{req} - {url}")

    prepped = session.prepare_request(req)
    response = session.send(prepped)
    response.raise_for_status()
    response_json = response.json()
    return response_json.get("result")


@handle_exceptions
def get_amount_prodct(offer_id, product_id, session):
    """ Вычисляет количество каждой позиции товара """
    # Метод устаревает и будет отключён 31 января 2025 года.
    # Переключиться на новую версию /v4/product/info/stocks
    url = "https://api-seller.ozon.ru/v4/product/info/stocks"
    data = {"filter":
        {
            "offer_id": [offer_id],
            "product_id": [product_id],
            "visibility": "ALL"
        },
        "last_id": '',
        'limit': 1000}
    req = requests.Request('POST', url, headers=OZON_HEADERS, data=json.dumps(data))

    # call function of logging
    # log_(f"{req} - {url}")

    prepped = session.prepare_request(req)
    response = session.send(prepped)
    response.raise_for_status()
    response_json = response.json()
    return response_json.get('items')


@handle_exceptions
def get_all_products_with_request():
    url = "https://api-seller.ozon.ru/v3/product/list"
    all_products = []
    last_id = None

    with requests.Session() as session:
        while True:
            data = {
                "filter": {},
                "limit": 1000
            }
            if last_id:
                data["last_id"] = last_id
            req = requests.Request('POST', url, headers=OZON_HEADERS, data=json.dumps(data))
            prepped = session.prepare_request(req)
            response = session.send(prepped)
            response.raise_for_status()

            # call function of logging
            # log_(f"{response} - {url}")

            response_json = response.json()
            if response_json.get("result") and response_json["result"].get("items"):
                products = response_json["result"]["items"]
                all_products.extend(products)
                if len(products) < 1000:
                    break
                last_id = products[-1].get("id")  # if exist id to pagination
                if not last_id:
                    break
            else:
                print(f"Error response: {response_json}")
                return None
    return all_products


@handle_exceptions
def unpaid_production():
    """
    Получает список неоплаченных товаров, заказанных юридическими лицами, с количеством.
    """
    url = "https://api-seller.ozon.ru/v1/posting/unpaid-legal/product/list"

    with requests.Session() as session:
        data = {
            "cursor": "",
            "limit": 1000
        }
        req = requests.Request('POST', url, headers=OZON_HEADERS, data=json.dumps(data))
        prepped = session.prepare_request(req)
        response = session.send(prepped)
        response.raise_for_status()

        response_json = response.json()
        products = response_json.get("products")
        # print(products)
        if products:
            all_unpaid_products = []
            for item in products:
                product_info = {
                    'product_id': item.get('product_id'),
                    'offer_id': item.get('offer_id'),
                    'quantity': item.get('quantity', 1),
                    'name': item.get('name'),
                    'image_url': item.get('image_url')
                }
                all_unpaid_products.append(product_info)
            return all_unpaid_products
        else:
            print("Нет неоплаченных товаров или ошибка в ответе.")
            return []


def ozon_production():
    """ Вывод продукции ozon """
    all_products_data = []
    products = get_all_products_with_request()
    unpaid_prod = unpaid_production()
    if products:
        with requests.Session() as session:  # Session for nested requests
            for product in products:
                product_id = product.get('product_id')
                offer_id = product.get("offer_id")
                unpaid_info = next((item for item in unpaid_prod if item['offer_id'] == offer_id), None)
                quantity_unpaid = unpaid_info['quantity'] if unpaid_info else 0

                if offer_id:
                    product_detail = get_product_details(offer_id, session)
                    amount_of_product = get_amount_prodct(offer_id, product_id, session)
                    # print(amount_of_product[0])
                    if product_detail:
                        name = product_detail.get('name', 'N/A')
                        stock = amount_of_product[0].get('stocks')[0].get('present')
                        reserved = amount_of_product[0].get('stocks')[0].get('reserved')
                        product_data = {
                            "product_id": product_id,
                            "offer_id": offer_id,
                            "name": name,
                            "stock": stock,
                            "reserved": reserved + quantity_unpaid,
                            "quantity_unpaid": quantity_unpaid
                        }
                        all_products_data.append(product_data)
                    else:
                        print(f"Could not get details for product with offer_id: {offer_id}")
                else:
                    print("Offer id not found")
    else:
        print("Не удалось получить товары.")

    return all_products_data


ALL_OZON_PRODUCTS = ozon_production()
if __name__ == "__main__":
    ozon = ozon_production()
    print(json.dumps(ozon, indent=4, ensure_ascii=False))
