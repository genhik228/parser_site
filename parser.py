import os
import sys

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from bs4 import BeautifulSoup
import re
import pandas as pd
import time
import requests
from datetime import date
import datetime

def pars_info(element, articul, name, size, count, price, sale, price_of_sale, urls, page_list, page_i=None):
    soup = BeautifulSoup(element.get_attribute('innerHTML'), 'html.parser')
    product_div = soup.find_all("div", {"class": "product"})
    print('Товаров для обработки:', len(product_div))
    for i in range(len(product_div)):
        print('Процесс обработки:', str(i + 1), 'из', len(product_div))
        price_div = re.findall('\d+', product_div[i].find("div", {"class": "price"}).get_text(strip=True)) # price
        names = product_div[i].select_one('h2')   # name
        names.select_one('span').decompose()
        names = names.text
        names = names[1:]
        href = product_div[i].find_all(href=True)[0]['href']  # href
        time.sleep(1)
        product_href = requests.get(href)
        product_html = BeautifulSoup(product_href.text, "html.parser")
        art = product_html.find("div", {"class": "acticle"}).text.split('Артикул: ')[1].strip() # aricul
        size_list = product_html.find_all("span", {"class": "swatch-label"}) # size
        for r in size_list:
            razmer = r.text
            if 'US' in r.text:
                razmer = razmer.replace('US ', '')
            size.append(razmer)
            name.append(names)
            urls.append(href)
            articul.append(art)
            if page_i is not None:
                page_list.append(url + "page/" + str(page_i + 2))
            else:
                page_list.append(url)
            if len(price_div) == 1:
                price.append(int(price_div[0]))
                sale.append('')
                price_of_sale.append('')
            elif len(price_div) == 3:
                price.append(int(price_div[0]))
                sale.append(price_div[1] + ' %')
                price_of_sale.append(int(price_div[2]))
    return articul, name, size, count, price, sale, price_of_sale, urls, page_list

start = datetime.datetime.now()
print('Время старта: ' + str(start))


articul, name, size, count, price, sale, price_of_sale, urls, page_list = [], [], [], [], [], [], [], [], []
browser = webdriver.Firefox()

url_list = ["https://run365.ru/product-category/zhenshhiny/", 'https://run365.ru/product-category/muzhchiny/',
            'https://run365.ru/product-category/deti/', 'https://run365.ru/product-category/aksessuary/']

for url in url_list:
    browser.get(url)
    print('Начало обработки страницы', url)
    element = browser.find_element(By.CLASS_NAME, 'all_tovar')
    articul, name, size, count, price, sale, price_of_sale, urls, page_list = pars_info(element, articul, name, size,
                                                                                        count, price, sale,
                                                                                        price_of_sale, urls, page_list)
    print('Завершение обработки страницы:', str(datetime.datetime.now() - start), url)

    page_div = browser.find_element(By.CLASS_NAME, 'woocommerce-pagination')
    page_soup = BeautifulSoup(page_div.get_attribute('innerHTML'), 'html.parser')
    page_numbers = page_soup.find_all("a", {"class": "page-numbers"})
    print('Страниц для обработки:', page_numbers)
    for page_i in range(int(page_numbers[-2].text) - 1):
        print('Процесс обработки страниц:', str(page_i + 1), 'из', page_numbers)
        browser.find_element(By.CLASS_NAME, 'next').click()
        print('Начало обработки страницы', url + "page/" + str(page_i + 2))
        element = browser.find_element(By.CLASS_NAME, 'all_tovar')
        articul, name, size, count, price, sale, price_of_sale, urls, page_list = pars_info(element, articul, name,
                                                                                            size, count, price, sale,
                                                                                            price_of_sale, urls,
                                                                                            page_list, page_i=page_i)
        print('Завершение обработки страницы:', str(datetime.datetime.now() - start), url + "page/" + str(page_i + 2))

print('SAVE RESULT')
count = [1 for i in range(len(name))]
data = pd.DataFrame({'Артикул': articul, 'Название товара': name, 'Размер US': size, 'Количество': count,
                     'Цена РРЦ (зачеркнутая цена)': price, 'Скидка': sale, 'Цена со скидкой': price_of_sale,
                     'Страница парсинга': urls, 'Cтраница': page_list})
data.drop_duplicates(inplace=True)
data.to_excel(str(date.today()) + '.run365.xlsx', index=False)
finish = datetime.datetime.now()
print('Время окончания: ' + str(finish))
print('Время работы: ' + str(finish - start))

