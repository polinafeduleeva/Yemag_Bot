import xml.etree.ElementTree as ET
from config import *


def prepare_code(code):
    code = code.upper()
    res = ''
    for s in code:
        if s in REPLACE:
            res += REPLACE[s]
        else:
            res += s
    return res


def load_data(db):
    namespaces = {'ns': 'urn:1C.ru:commerceml_2'}
    try:
        tree = ET.parse(db)
    except:
        return {}, {}, {}, {}, {}, 1
    root = tree.getroot()

    stocks_id = {}
    sizes = {}
    stocks = {}
    prices = {}
    colors = {}
    names = {}
    elements = root.find('.//ns:ТипыЦен', namespaces)
    price_id = ''
    for elem in elements:
        if elem.find('ns:Наименование', namespaces).text == "Розница":
            price_id = elem.find('ns:Ид', namespaces).text
    elements = root.find('.//ns:Склады', namespaces)
    for elem in elements:
        stocks_id[elem.find('ns:Ид', namespaces).text] = elem.find('ns:Наименование', namespaces).text
    elements = root.find('.//ns:Предложения', namespaces)
    for elem in elements:
        try:
            code = prepare_code(elem.find('ns:Артикул', namespaces).text)
            name = elem.find('ns:Наименование', namespaces).text
            print(code)
            count = elem.find('ns:Количество', namespaces).text
            size_arr = elem.find('ns:ХарактеристикиТовара', namespaces)
            price_arr = elem.find('ns:Цены', namespaces)
            for e in price_arr:
                if e.find('ns:ИдТипаЦены', namespaces).text == price_id:
                    price = e.find('ns:ЦенаЗаЕдиницу', namespaces).text
                    break
            else:
                price = price_arr.find('ns:ЦенаЗаЕдиницу', namespaces)
            try:
                stock = elem.find('ns:Склад', namespaces)
                stock = stock.attrib['ИдСклада']
                stock = stocks_id[stock]
            except:
                stock = ''
            size = ''
            for e in size_arr:
                if e.find('ns:Наименование', namespaces).text.lower() == 'размер':
                    size = e.find('ns:Значение', namespaces).text
            if code not in sizes:
                sizes[code] = [size]
            elif size not in sizes[code]:
                sizes[code].append(size)
            color = ''
            for e in size_arr:
                if e.find('ns:Наименование', namespaces).text.lower() == 'цвет характеристики':
                    color = e.find('ns:Значение', namespaces).text
            enum = 'шт'
            try:
                enum = elem.find('ns:БазоваяЕдиница', namespaces)
                enum = enum.attrib['НаименованиеПолное']
                if enum[0].lower() == 'ш':
                    enum = 'шт.'
                else:
                    enum = 'пары'
            except:
                pass
            if stock and int(count):
                if stock not in stocks:
                    stocks[stock] = {code: {size: f'{count} {enum.lower()}'}}
                elif code not in stocks[stock]:
                    stocks[stock][code] = {size: f'{count} {enum.lower()}'}
                else:
                    stocks[stock][code][size] = f'{count} {enum.lower()}'
            prices[code] = price
            names[code] = ' '.join(name.split()[:-2])
            if size:
                if code not in colors:
                    colors[code] = {size: [color.lower()]}
                elif size not in colors[code]:
                    colors[code][size] = [color.lower()]
                elif color.lower() not in colors[code][size]:
                    colors[code][size].append(color)
        except Exception as err:
            print(err)
    return sizes, stocks, prices, colors, names, 0
