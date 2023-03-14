import requests
from bs4 import BeautifulSoup
import csv
import datetime


headers = {
    'user-agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/110.0.0.0 Safari/537.36',
    'accept': '*/*',
    'content-type': 'application/json',
    'origin': 'https://mircli.ru',
    'referer': 'https://mircli.ru/elektricheskie-nakopitelnye-vodonagevateli/5-litrov/?page=2',
}


def get_categories() -> list[str]:
    """Получаем ссылки на все категории"""
    print("Собираем категории...")
    response = requests.get(url='https://mircli.ru', headers=headers)
    suop = BeautifulSoup(response.text, 'lxml')

    categories_url = []
    ul_categories = suop.find('ul', class_="main-menu main-menu-product-fixed")
    a_categories = ul_categories.findAll('a')

    for cat in a_categories:
        if str(cat.get('href')).startswith('/'):
            categories_url.append(f"https://mircli.ru{cat.get('href')}")

    return categories_url


def get_product_pages(category: str) -> list:
    """Получаем ссылки на все товары в категории"""
    global num_pages
    num_pages = 0
    print(f"Поиск ссылок в категории {category}")
    response = requests.get(url=f'{category}?page=1', headers=headers)
    suop = BeautifulSoup(response.text, 'lxml')

    # количество страниц со списком товаров
    try:
        num_pages = int(suop.find('div', class_="display_inline-block float-right page-navigation__page").find_next().find_next('ul', class_="pagination").find('li').find('a').get('href').split('?page=')[-1])
    except Exception:
        num_pages = 1

    print(f'Страниц с товарами {num_pages}')

    refs = []

    # получаем массив со ссылками на товары со всех страниц
    for page in range(1, num_pages + 1):
        response = requests.get(url=f'{category}?page={page}', headers=headers)
        suop = BeautifulSoup(response.text, 'lxml')

        links = suop.findAll('a', class_="prod_a")
        for link in links:
            refs.append([f"https://mircli.ru{link.get('href')}"])

    return refs


def get_product(page: list) -> list[str]:
    """Получаем все необходимые данные товара и возвращаем в виде массива"""
    response = requests.get(url=page[0], headers=headers)
    suop = BeautifulSoup(response.text, 'lxml')

    # получаем производителя
    brand = suop.find('meta', itemprop="brand").get('content')

    # получаем массив со ссылками на картинки
    pictures = []
    pics = suop.find('div', id="fotorama-product").findAll('img')
    for i in pics:
        src = str(i.get('src'))
        if src.startswith('/image'):
            pictures.append(f"https://mircli.ru{src}")

    # получаем название товара
    name = suop.find('span', class_="product-name").text

    # получаем описание товара
    description = suop.find('div', class_="show-more-block-new").text

    # получаем характеристики товара
    ul = suop.findAll('ul', class_="menu-dot")
    lis = ul[1].findAll('li')
    specs = {}
    for li in lis:
        a = str(li.find('span', class_="main").text).split('\n')[0]
        b = li.find('span', class_="page").text
        specs[a] = b

    return [brand, name, description, specs, pictures]


num_pages = 0
counter = 0
for c in get_categories():
    start = datetime.datetime.now()
    category = c.split('/')[-2]
    for i in get_product_pages(c):
        counter += 1
        with open(f'{category}.csv', 'a') as f:
            csvout = csv.writer(f)
            csvout.writerow(get_product(i))
        print(f'Товар {counter}, страница {(counter // 20) + 1}/{num_pages}')
    print(f"Затраченное время на категорию: {datetime.datetime.now() - start}")

