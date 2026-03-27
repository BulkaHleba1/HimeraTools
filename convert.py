#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys
import json
import datetime
import urllib.request
import xml.etree.ElementTree as ET
from pathlib import Path

try:
    from colorama import init, Fore, Style
    init(autoreset=True)
    COLORAMA = True
except ImportError:
    COLORAMA = False
    class Fore:
        RED = GREEN = YELLOW = BLUE = MAGENTA = CYAN = WHITE = RESET = ''
    class Style:
        BRIGHT = DIM = NORMAL = RESET_ALL = ''

TOOLS_DIR = os.path.expanduser("~/.tools")
CURRENCY_CACHE = os.path.join(TOOLS_DIR, "currency_cache.json")
DECIMALS = 5

def cprint(text, color=None, style=None, end='\n'):
    if COLORAMA and color:
        color_code = getattr(Fore, color.upper(), '')
        style_code = getattr(Style, style.upper(), '') if style else ''
        print(f"{style_code}{color_code}{text}{Style.RESET_ALL}", end=end)
    else:
        print(text, end=end)

def ensure_tools_dir():
    os.makedirs(TOOLS_DIR, exist_ok=True)

def select_from_list(items, prompt="Выберите номер: "):
    for i, item in enumerate(items, 1):
        print(f"{i}. {item}")
    while True:
        choice = input(prompt).strip()
        if not choice:
            return None
        if choice.isdigit() and 1 <= int(choice) <= len(items):
            return int(choice) - 1
        cprint("Неверный номер.", color='RED')

UNITS = {
    "Длина": {
        "base": "м",
        "factors": {
            "м": 1.0,
            "км": 1000.0,
            "дм": 0.1,
            "см": 0.01,
            "мм": 0.001,
            "миля": 1609.344,
            "фут": 0.3048,
            "дюйм": 0.0254,
            "ярд": 0.9144
        }
    },
    "Масса": {
        "base": "кг",
        "factors": {
            "кг": 1.0,
            "г": 0.001,
            "мг": 1e-6,
            "т": 1000.0,
            "фунт": 0.45359237,
            "унция": 0.028349523125
        }
    },
    "Объём": {
        "base": "л",
        "factors": {
            "л": 1.0,
            "мл": 0.001,
            "м³": 1000.0,
            "галлон (англ.)": 4.54609,
            "галлон (амер.)": 3.785411784,
            "баррель (нефт.)": 158.987294928
        }
    },
    "Температура": {
        "base": "K",
        "convert": {
            "K": lambda x: x,
            "°C": lambda k: k - 273.15,
            "°F": lambda k: k * 9/5 - 459.67
        },
        "inverse": {
            "K": lambda x: x,
            "°C": lambda c: c + 273.15,
            "°F": lambda f: (f + 459.67) * 5/9
        }
    },
    "Скорость": {
        "base": "м/с",
        "factors": {
            "м/с": 1.0,
            "км/ч": 0.27777778,
            "миль/ч": 0.44704,
            "узел": 0.514444444,
            "фут/с": 0.3048
        }
    },
    "Площадь": {
        "base": "м²",
        "factors": {
            "м²": 1.0,
            "км²": 1_000_000.0,
            "га": 10_000.0,
            "акр": 4046.8564224,
            "фут²": 0.09290304,
            "дюйм²": 0.00064516
        }
    },
    "Время": {
        "base": "с",
        "factors": {
            "с": 1.0,
            "мин": 60.0,
            "ч": 3600.0,
            "сут": 86400.0,
            "неделя": 604800.0,
            "мес (ср.)": 2629746.0,
            "год (ср.)": 31556952.0
        }
    },
    "Сила (Ньютоны)": {
        "base": "Н",
        "factors": {
            "Н": 1.0,
            "кН": 1000.0,
            "дина": 1e-5,
            "кгс": 9.80665,
            "фунт-сила": 4.4482216152605
        }
    },
    "Давление (Паскали)": {
        "base": "Па",
        "factors": {
            "Па": 1.0,
            "кПа": 1000.0,
            "МПа": 1_000_000.0,
            "бар": 100_000.0,
            "атм": 101325.0,
            "мм рт. ст.": 133.3223684,
            "psi": 6894.757293168
        }
    }
}

CURRENCY_NAMES = {
    "USD": "Доллар США",
    "EUR": "Евро",
    "GBP": "Фунт стерлингов",
    "CNY": "Китайский юань",
    "JPY": "Японская иена",
    "CHF": "Швейцарский франк",
    "CAD": "Канадский доллар",
    "AUD": "Австралийский доллар",
}

def fetch_currency_rates():
    url = "https://www.cbr.ru/scripts/XML_daily.asp"
    try:
        with urllib.request.urlopen(url) as response:
            data = response.read()
        root = ET.fromstring(data)
        rates = {}
        for valute in root.findall('Valute'):
            code = valute.find('CharCode').text
            value = float(valute.find('Value').text.replace(',', '.'))
            nominal = int(valute.find('Nominal').text)
            rates[code] = value / nominal
        rates["RUB"] = 1.0
        return rates
    except Exception as e:
        cprint(f"Ошибка получения курсов валют: {e}", color='RED')
        return None

def get_currency_rates(force_update=False):
    ensure_tools_dir()
    if not force_update and os.path.exists(CURRENCY_CACHE):
        try:
            with open(CURRENCY_CACHE, 'r', encoding='utf-8') as f:
                cache = json.load(f)
            cache_date = datetime.datetime.fromisoformat(cache['date'])
            if (datetime.datetime.now() - cache_date).days < 1:
                return cache['rates']
        except (ValueError, KeyError):
            pass
    rates = fetch_currency_rates()
    if rates:
        cache = {
            'date': datetime.datetime.now().isoformat(),
            'rates': rates
        }
        with open(CURRENCY_CACHE, 'w', encoding='utf-8') as f:
            json.dump(cache, f, indent=4)
        return rates
    else:
        if os.path.exists(CURRENCY_CACHE):
            with open(CURRENCY_CACHE, 'r', encoding='utf-8') as f:
                cache = json.load(f)
            cprint("Используются устаревшие курсы валют.", color='YELLOW')
            return cache['rates']
        return None

def convert_temperature(value, from_unit, to_unit):
    inverse = UNITS["Температура"]["inverse"]
    if from_unit not in inverse:
        raise ValueError(f"Неизвестная единица: {from_unit}")
    kelvin = inverse[from_unit](value)
    convert = UNITS["Температура"]["convert"]
    if to_unit not in convert:
        raise ValueError(f"Неизвестная единица: {to_unit}")
    return convert[to_unit](kelvin)

def convert_physical(value, from_unit, to_unit, category):
    data = UNITS[category]
    factors = data["factors"]
    base_unit = data["base"]
    if from_unit not in factors or to_unit not in factors:
        raise ValueError("Неизвестная единица в категории")
    base_value = value * factors[from_unit]
    result = base_value / factors[to_unit]
    return result

def convert_currency(value, from_currency, to_currency, rates):
    if from_currency not in rates or to_currency not in rates:
        raise ValueError("Неизвестная валюта (нет курса)")
    rubles = value * rates[from_currency]
    result = rubles / rates[to_currency]
    return result

def currency_menu():
    rates = get_currency_rates()
    if not rates:
        cprint("Не удалось загрузить курсы валют. Попробуйте позже.", color='RED')
        return
    currencies = sorted([c for c in rates.keys() if c != "RUB"])
    currency_list = [f"{code} - {CURRENCY_NAMES.get(code, '')}" for code in currencies]
    currency_list = ["RUB - Российский рубль"] + currency_list
    currencies_with_rub = ["RUB"] + currencies
    while True:
        cprint("\n--- Конвертер валют ---", color='BLUE', style='BRIGHT')
        try:
            val_str = input("Введите сумму (или 'q' для выхода): ").strip()
            if val_str.lower() == 'q':
                break
            value = float(val_str.replace(',', '.'))
        except ValueError:
            cprint("Ошибка: введите число.", color='RED')
            continue
        cprint("Выберите исходную валюту:", color='CYAN')
        from_idx = select_from_list(currency_list, "Исходная: ")
        if from_idx is None:
            continue
        from_cur = currencies_with_rub[from_idx]
        cprint("Выберите целевую валюту:", color='CYAN')
        to_idx = select_from_list(currency_list, "Целевая: ")
        if to_idx is None:
            continue
        to_cur = currencies_with_rub[to_idx]
        try:
            result = convert_currency(value, from_cur, to_cur, rates)
            cprint(f"{value:.{DECIMALS}f} {from_cur} = {result:.{DECIMALS}f} {to_cur}", color='GREEN', style='BRIGHT')
        except ValueError as e:
            cprint(f"Ошибка: {e}", color='RED')

def category_menu(category_name):
    data = UNITS[category_name]
    if category_name == "Температура":
        units_list = list(data["convert"].keys())
    else:
        units_list = list(data["factors"].keys())
    while True:
        cprint(f"\n--- {category_name} ---", color='BLUE', style='BRIGHT')
        try:
            val_str = input("Введите значение (или 'q' для выхода): ").strip()
            if val_str.lower() == 'q':
                break
            value = float(val_str.replace(',', '.'))
        except ValueError:
            cprint("Ошибка: введите число.", color='RED')
            continue
        cprint("Выберите исходную единицу:", color='CYAN')
        from_idx = select_from_list(units_list, "Исходная: ")
        if from_idx is None:
            continue
        from_unit = units_list[from_idx]
        cprint("Выберите целевую единицу:", color='CYAN')
        to_idx = select_from_list(units_list, "Целевая: ")
        if to_idx is None:
            continue
        to_unit = units_list[to_idx]
        try:
            if category_name == "Температура":
                result = convert_temperature(value, from_unit, to_unit)
            else:
                result = convert_physical(value, from_unit, to_unit, category_name)
            cprint(f"{value:.{DECIMALS}f} {from_unit} = {result:.{DECIMALS}f} {to_unit}", color='GREEN', style='BRIGHT')
        except ValueError as e:
            cprint(f"Ошибка: {e}", color='RED')

def main_menu():
    while True:
        cprint("\n=== Конвертер величин ===", color='BLUE', style='BRIGHT')
        print("Выберите категорию:")
        categories = list(UNITS.keys()) + ["Валюта"]
        for i, cat in enumerate(categories, 1):
            print(f"{i}. {cat}")
        print("0. Выход")
        choice = input("> ").strip()
        if choice == '0':
            cprint("Выход.", color='GREEN')
            break
        if not choice.isdigit():
            cprint("Неверный ввод.", color='RED')
            continue
        idx = int(choice) - 1
        if idx < 0 or idx >= len(categories):
            cprint("Неверный номер.", color='RED')
            continue
        selected = categories[idx]
        if selected == "Валюта":
            currency_menu()
        else:
            category_menu(selected)

if __name__ == "__main__":
    main_menu()