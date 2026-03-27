#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys
import json
import csv
import datetime
from collections import defaultdict

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
EXPENSES_FILE = os.path.join(TOOLS_DIR, "expenses.json")
CATEGORIES_FILE = os.path.join(TOOLS_DIR, "categories.json")
BUDGETS_FILE = os.path.join(TOOLS_DIR, "budgets.json")
RECURRING_FILE = os.path.join(TOOLS_DIR, "recurring.json")
DECIMALS = 2

def cprint(text, color=None, style=None, end='\n'):
    if COLORAMA and color:
        color_code = getattr(Fore, color.upper(), '')
        style_code = getattr(Style, style.upper(), '') if style else ''
        print(f"{style_code}{color_code}{text}{Style.RESET_ALL}", end=end)
    else:
        print(text, end=end)

def ensure_tools_dir():
    os.makedirs(TOOLS_DIR, exist_ok=True)

def load_json(file, default):
    ensure_tools_dir()
    if os.path.exists(file):
        with open(file, 'r', encoding='utf-8') as f:
            return json.load(f)
    return default

def save_json(file, data):
    ensure_tools_dir()
    with open(file, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=4, ensure_ascii=False)

def select_from_list(items, prompt="Выберите номер: ", allow_none=False):
    for i, item in enumerate(items, 1):
        print(f"{i}. {item}")
    while True:
        choice = input(prompt).strip()
        if not choice and allow_none:
            return None
        if choice.isdigit() and 1 <= int(choice) <= len(items):
            return int(choice) - 1
        cprint("Неверный номер.", color='RED')

def input_date(default=None):
    while True:
        d_str = input("Дата (ГГГГ-ММ-ДД, Enter - сегодня): ").strip()
        if not d_str:
            return datetime.date.today().isoformat()
        try:
            datetime.date.fromisoformat(d_str)
            return d_str
        except ValueError:
            cprint("Неверный формат. Используйте ГГГГ-ММ-ДД.", color='RED')

def input_float(prompt):
    while True:
        try:
            return float(input(prompt).strip().replace(',', '.'))
        except ValueError:
            cprint("Ошибка: введите число.", color='RED')

DEFAULT_CATEGORIES = [
    "Продукты",
    "Транспорт",
    "Развлечения",
    "Связь",
    "Жильё",
    "Здоровье",
    "Одежда",
    "Образование",
    "Подарки",
    "Прочее"
]

def load_categories():
    cats = load_json(CATEGORIES_FILE, DEFAULT_CATEGORIES)
    if not isinstance(cats, list):
        cats = DEFAULT_CATEGORIES
    return cats

def save_categories(cats):
    save_json(CATEGORIES_FILE, cats)

def manage_categories():
    cats = load_categories()
    while True:
        cprint("\n--- Управление категориями ---", color='BLUE')
        print("Текущие категории:")
        for i, cat in enumerate(cats, 1):
            print(f"{i}. {cat}")
        print("\n1. Добавить категорию")
        print("2. Удалить категорию")
        print("3. Переименовать категорию")
        print("4. Вернуться")
        choice = input("> ").strip()
        if choice == '1':
            new = input("Новая категория: ").strip()
            if new and new not in cats:
                cats.append(new)
                save_categories(cats)
                cprint("Категория добавлена.", color='GREEN')
        elif choice == '2':
            idx = select_from_list(cats, "Номер для удаления: ")
            if idx is not None:
                removed = cats.pop(idx)
                save_categories(cats)
                cprint(f"Категория '{removed}' удалена.", color='GREEN')
        elif choice == '3':
            idx = select_from_list(cats, "Номер для переименования: ")
            if idx is not None:
                new_name = input("Новое название: ").strip()
                if new_name:
                    cats[idx] = new_name
                    save_categories(cats)
                    cprint("Категория переименована.", color='GREEN')
        elif choice == '4':
            break

def load_expenses():
    return load_json(EXPENSES_FILE, [])

def save_expenses(expenses):
    save_json(EXPENSES_FILE, expenses)

def get_next_id(expenses):
    if not expenses:
        return 1
    return max(e['id'] for e in expenses) + 1

def add_transaction(trans_type="расход"):
    cprint(f"\n--- Добавление {trans_type}а ---", color='BLUE', style='BRIGHT')
    amount = input_float("Сумма: ")
    if amount <= 0:
        cprint("Сумма должна быть положительной.", color='RED')
        return
    cats = load_categories()
    cprint("Выберите категорию:", color='CYAN')
    cat_idx = select_from_list(cats, "Категория: ")
    if cat_idx is None:
        return
    category = cats[cat_idx]
    date = input_date()
    description = input("Описание: ").strip()
    expenses = load_expenses()
    new_id = get_next_id(expenses)
    transaction = {
        "id": new_id,
        "type": trans_type,
        "amount": amount,
        "category": category,
        "date": date,
        "description": description
    }
    expenses.append(transaction)
    save_expenses(expenses)
    cprint(f"{trans_type.capitalize()} добавлен.", color='GREEN')
    if trans_type == "расход":
        check_budget_for_category(category)

def list_transactions(expenses, title="Все операции"):
    if not expenses:
        cprint("Нет операций.", color='YELLOW')
        return
    sorted_exp = sorted(expenses, key=lambda x: x['date'], reverse=True)
    cprint(f"\n--- {title} ---", color='WHITE', style='BRIGHT')
    print(f"{'ID':<5} {'Дата':<12} {'Тип':<6} {'Сумма':<12} {'Категория':<15} {'Описание'}")
    for e in sorted_exp:
        color = Fore.GREEN if e['type'] == 'доход' else Fore.RED
        print(f"{e['id']:<5} {e['date']:<12} {e['type']:<6} {color}{e['amount']:<12.2f} {Fore.RESET}{e['category']:<15} {e['description']}")

def filter_transactions(expenses):
    filtered = expenses
    cprint("\n--- Фильтрация ---", color='BLUE')
    date_from = input("Дата с (ГГГГ-ММ-ДД, Enter пропустить): ").strip()
    date_to = input("Дата по (ГГГГ-ММ-ДД, Enter пропустить): ").strip()
    if date_from:
        filtered = [e for e in filtered if e['date'] >= date_from]
    if date_to:
        filtered = [e for e in filtered if e['date'] <= date_to]
    cat_filter = input("Категория (Enter пропустить): ").strip()
    if cat_filter:
        filtered = [e for e in filtered if cat_filter.lower() in e['category'].lower()]
    return filtered

def edit_transaction(expenses):
    list_transactions(expenses)
    try:
        eid = int(input("Введите ID операции для редактирования: "))
    except ValueError:
        cprint("Неверный ID.", color='RED')
        return
    for e in expenses:
        if e['id'] == eid:
            cprint(f"Редактирование операции ID {eid}. Оставьте поле пустым для сохранения.", color='CYAN')
            new_amount = input(f"Сумма ({e['amount']:.2f}): ").strip()
            if new_amount:
                try:
                    e['amount'] = float(new_amount.replace(',', '.'))
                except ValueError:
                    cprint("Неверная сумма, оставлено.", color='YELLOW')
            new_cat = input(f"Категория ({e['category']}): ").strip()
            if new_cat:
                e['category'] = new_cat
            new_date = input(f"Дата ({e['date']}): ").strip()
            if new_date:
                try:
                    datetime.date.fromisoformat(new_date)
                    e['date'] = new_date
                except ValueError:
                    cprint("Неверный формат даты, оставлено.", color='YELLOW')
            new_desc = input(f"Описание ({e['description']}): ").strip()
            if new_desc:
                e['description'] = new_desc
            save_expenses(expenses)
            cprint("Операция обновлена.", color='GREEN')
            return
    cprint("ID не найден.", color='RED')

def delete_transaction(expenses):
    list_transactions(expenses)
    try:
        eid = int(input("Введите ID операции для удаления: "))
    except ValueError:
        cprint("Неверный ID.", color='RED')
        return
    for i, e in enumerate(expenses):
        if e['id'] == eid:
            confirm = input(f"Удалить операцию '{e['description']}' на {e['amount']}? (y/n): ").strip().lower()
            if confirm == 'y':
                del expenses[i]
                save_expenses(expenses)
                cprint("Операция удалена.", color='GREEN')
            return
    cprint("ID не найден.", color='RED')

def load_budgets():
    return load_json(BUDGETS_FILE, {})

def save_budgets(budgets):
    save_json(BUDGETS_FILE, budgets)

def set_budget():
    cats = load_categories()
    cprint("\n--- Установка бюджета ---", color='BLUE')
    cat_idx = select_from_list(cats, "Выберите категорию: ")
    if cat_idx is None:
        return
    category = cats[cat_idx]
    month = input("Месяц (ГГГГ-ММ, Enter - текущий): ").strip()
    if not month:
        month = datetime.date.today().strftime("%Y-%m")
    try:
        datetime.datetime.strptime(month, "%Y-%m")
    except ValueError:
        cprint("Неверный формат месяца. Используйте ГГГГ-ММ.", color='RED')
        return
    amount = input_float("Сумма бюджета: ")
    if amount <= 0:
        cprint("Сумма должна быть положительной.", color='RED')
        return
    budgets = load_budgets()
    key = f"{category}_{month}"
    budgets[key] = amount
    save_budgets(budgets)
    cprint(f"Бюджет на {category} за {month} установлен: {amount:.2f}", color='GREEN')

def check_budget_for_category(category, month=None):
    if month is None:
        month = datetime.date.today().strftime("%Y-%m")
    budgets = load_budgets()
    key = f"{category}_{month}"
    if key not in budgets:
        return
    limit = budgets[key]
    expenses = load_expenses()
    total = sum(e['amount'] for e in expenses if e['type'] == 'расход' and e['category'] == category and e['date'].startswith(month))
    if total > limit:
        cprint(f"Внимание! Бюджет на категорию '{category}' за {month} превышен: {total:.2f} / {limit:.2f}", color='RED', style='BRIGHT')
    else:
        cprint(f"Бюджет по '{category}' за {month}: {total:.2f} / {limit:.2f}", color='GREEN')

def check_all_budgets():
    month = datetime.date.today().strftime("%Y-%m")
    budgets = load_budgets()
    if not budgets:
        cprint("Нет установленных бюджетов.", color='YELLOW')
        return
    expenses = load_expenses()
    spent = defaultdict(float)
    for e in expenses:
        if e['type'] == 'расход' and e['date'].startswith(month):
            spent[e['category']] += e['amount']
    cprint(f"\n--- Бюджеты за {month} ---", color='BLUE', style='BRIGHT')
    for key, limit in budgets.items():
        if key.endswith(month):
            category = key[:-8]
            total = spent.get(category, 0.0)
            if total > limit:
                cprint(f"{category}: {total:.2f} / {limit:.2f} (превышен)", color='RED')
            else:
                cprint(f"{category}: {total:.2f} / {limit:.2f}", color='GREEN')

def load_recurring():
    return load_json(RECURRING_FILE, [])

def save_recurring(recurring):
    save_json(RECURRING_FILE, recurring)

def add_recurring():
    cprint("\n--- Добавление периодического платежа ---", color='BLUE')
    amount = input_float("Сумма: ")
    if amount <= 0:
        cprint("Сумма должна быть положительной.", color='RED')
        return
    cats = load_categories()
    cat_idx = select_from_list(cats, "Категория: ")
    if cat_idx is None:
        return
    category = cats[cat_idx]
    description = input("Описание: ").strip()
    print("Периодичность:")
    print("1. Ежемесячно")
    print("2. Еженедельно")
    print("3. Ежегодно")
    period_choice = select_from_list(["Ежемесячно", "Еженедельно", "Ежегодно"], "Выберите: ")
    if period_choice is None:
        return
    period = ["monthly", "weekly", "yearly"][period_choice]
    if period == "monthly":
        day = input("День месяца (1-31, Enter - последний день?): ").strip()
        if day.isdigit():
            day = int(day)
        else:
            day = None
    elif period == "weekly":
        day = input("День недели (0-6, где 0 - понедельник, Enter - любой): ").strip()
        if day.isdigit():
            day = int(day)
        else:
            day = None
    else:
        month_day = input("Месяц и день (ММ-ДД, Enter - сегодня): ").strip()
        if month_day:
            try:
                datetime.datetime.strptime(month_day, "%m-%d")
            except:
                cprint("Неверный формат, будет использована сегодняшняя дата.", color='YELLOW')
                month_day = datetime.date.today().strftime("%m-%d")
        else:
            month_day = datetime.date.today().strftime("%m-%d")
        day = month_day
    start_date = input_date()
    recurring = load_recurring()
    new_id = 1
    if recurring:
        new_id = max(r['id'] for r in recurring) + 1
    item = {
        "id": new_id,
        "type": "расход",
        "amount": amount,
        "category": category,
        "description": description,
        "period": period,
        "day": day,
        "start_date": start_date,
        "last_applied": None
    }
    recurring.append(item)
    save_recurring(recurring)
    cprint("Периодический платеж добавлен.", color='GREEN')

def apply_recurring():
    recurring = load_recurring()
    if not recurring:
        cprint("Нет периодических платежей.", color='YELLOW')
        return
    today = datetime.date.today()
    expenses = load_expenses()
    changed = False
    for r in recurring:
        last = r.get("last_applied")
        if last:
            last_date = datetime.date.fromisoformat(last)
        else:
            last_date = datetime.date.fromisoformat(r["start_date"])
        if r["period"] == "monthly":
            next_date = next_month_date(last_date, r["day"])
            while next_date <= today:
                new_id = get_next_id(expenses)
                trans = {
                    "id": new_id,
                    "type": "расход",
                    "amount": r["amount"],
                    "category": r["category"],
                    "date": next_date.isoformat(),
                    "description": r["description"] + " (период.)"
                }
                expenses.append(trans)
                r["last_applied"] = next_date.isoformat()
                changed = True
                next_date = next_month_date(next_date, r["day"])
    if changed:
        save_expenses(expenses)
        save_recurring(recurring)
        cprint("Периодические платежи применены.", color='GREEN')
    else:
        cprint("Нет новых платежей для применения.", color='YELLOW')

def next_month_date(date, day):
    if date.month == 12:
        next_month = datetime.date(date.year+1, 1, 1)
    else:
        next_month = datetime.date(date.year, date.month+1, 1)
    if day is None:
        last_day = (datetime.date(next_month.year, next_month.month % 12 + 1, 1) - datetime.timedelta(days=1)).day
        return datetime.date(next_month.year, next_month.month, last_day)
    else:
        try:
            return datetime.date(next_month.year, next_month.month, day)
        except ValueError:
            last_day = (datetime.date(next_month.year, next_month.month % 12 + 1, 1) - datetime.timedelta(days=1)).day
            return datetime.date(next_month.year, next_month.month, last_day)

def stats_menu():
    expenses = load_expenses()
    if not expenses:
        cprint("Нет данных.", color='YELLOW')
        return
    while True:
        cprint("\n--- Статистика ---", color='BLUE', style='BRIGHT')
        print("1. За день")
        print("2. За неделю")
        print("3. За месяц")
        print("4. Распределение по категориям")
        print("5. Проверка бюджетов")
        print("6. Назад")
        choice = input("> ").strip()
        if choice == '1':
            day = input_date()
            stats_day(expenses, day)
        elif choice == '2':
            start = input("Дата начала недели (ГГГГ-ММ-ДД, Enter - текущая неделя): ").strip()
            if not start:
                today = datetime.date.today()
                start = (today - datetime.timedelta(days=today.weekday())).isoformat()
            stats_week(expenses, start)
        elif choice == '3':
            month = input("Месяц (ГГГГ-ММ, Enter - текущий): ").strip()
            if not month:
                month = datetime.date.today().strftime("%Y-%m")
            stats_month(expenses, month)
        elif choice == '4':
            month = input("Месяц (ГГГГ-ММ, Enter - текущий): ").strip()
            if not month:
                month = datetime.date.today().strftime("%Y-%m")
            distribution(expenses, month)
        elif choice == '5':
            check_all_budgets()
        elif choice == '6':
            break

def stats_day(expenses, day):
    day_exp = [e for e in expenses if e['date'] == day]
    income = sum(e['amount'] for e in day_exp if e['type'] == 'доход')
    expense = sum(e['amount'] for e in day_exp if e['type'] == 'расход')
    cprint(f"\nСтатистика за {day}:", color='WHITE', style='BRIGHT')
    print(f"Доходы: {income:.2f}")
    print(f"Расходы: {expense:.2f}")
    print(f"Баланс: {income - expense:.2f}")

def stats_week(expenses, start_date):
    start = datetime.date.fromisoformat(start_date)
    end = start + datetime.timedelta(days=6)
    week_exp = [e for e in expenses if start <= datetime.date.fromisoformat(e['date']) <= end]
    income = sum(e['amount'] for e in week_exp if e['type'] == 'доход')
    expense = sum(e['amount'] for e in week_exp if e['type'] == 'расход')
    cprint(f"\nСтатистика за неделю {start_date} — {end.isoformat()}:", color='WHITE', style='BRIGHT')
    print(f"Доходы: {income:.2f}")
    print(f"Расходы: {expense:.2f}")
    print(f"Баланс: {income - expense:.2f}")

def stats_month(expenses, month):
    month_exp = [e for e in expenses if e['date'].startswith(month)]
    income = sum(e['amount'] for e in month_exp if e['type'] == 'доход')
    expense = sum(e['amount'] for e in month_exp if e['type'] == 'расход')
    cprint(f"\nСтатистика за {month}:", color='WHITE', style='BRIGHT')
    print(f"Доходы: {income:.2f}")
    print(f"Расходы: {expense:.2f}")
    print(f"Баланс: {income - expense:.2f}")

def distribution(expenses, month):
    month_exp = [e for e in expenses if e['type'] == 'расход' and e['date'].startswith(month)]
    if not month_exp:
        cprint("Нет расходов за этот месяц.", color='YELLOW')
        return
    cats = defaultdict(float)
    for e in month_exp:
        cats[e['category']] += e['amount']
    total = sum(cats.values())
    cprint(f"\nРаспределение расходов за {month} (всего: {total:.2f}):", color='WHITE', style='BRIGHT')
    max_len = 30
    sorted_items = sorted(cats.items(), key=lambda x: x[1], reverse=True)
    for cat, amt in sorted_items:
        percent = amt / total * 100
        bar_len = int((amt / total) * max_len)
        bar = '█' * bar_len
        print(f"{cat:<15} {amt:>8.2f} ({percent:5.1f}%) {bar}")

def export_csv():
    expenses = load_expenses()
    if not expenses:
        cprint("Нет данных для экспорта.", color='YELLOW')
        return
    filename = input("Имя файла для экспорта (по умолчанию expenses.csv): ").strip()
    if not filename:
        filename = "expenses.csv"
    if not filename.endswith('.csv'):
        filename += '.csv'
    try:
        with open(filename, 'w', encoding='utf-8', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(["ID", "Тип", "Сумма", "Категория", "Дата", "Описание"])
            for e in expenses:
                writer.writerow([e['id'], e['type'], e['amount'], e['category'], e['date'], e['description']])
        cprint(f"Экспорт завершён: {filename}", color='GREEN')
    except Exception as e:
        cprint(f"Ошибка экспорта: {e}", color='RED')

def import_csv():
    filename = input("Имя файла для импорта: ").strip()
    if not os.path.exists(filename):
        cprint("Файл не найден.", color='RED')
        return
    try:
        with open(filename, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            expenses = load_expenses()
            max_id = max((e['id'] for e in expenses), default=0)
            new_id = max_id + 1
            count = 0
            for row in reader:
                if not all(k in row for k in ["Тип", "Сумма", "Категория", "Дата"]):
                    cprint("Неверный формат CSV, пропускаем.", color='RED')
                    return
                try:
                    amount = float(row["Сумма"])
                    datetime.date.fromisoformat(row["Дата"])
                except:
                    cprint(f"Ошибка в строке {row}, пропущена.", color='YELLOW')
                    continue
                transaction = {
                    "id": new_id,
                    "type": row["Тип"],
                    "amount": amount,
                    "category": row["Категория"],
                    "date": row["Дата"],
                    "description": row.get("Описание", "")
                }
                expenses.append(transaction)
                new_id += 1
                count += 1
            save_expenses(expenses)
            cprint(f"Импортировано {count} записей.", color='GREEN')
    except Exception as e:
        cprint(f"Ошибка импорта: {e}", color='RED')

def main_menu():
    while True:
        cprint("\n=== Калькулятор расходов ===", color='BLUE', style='BRIGHT')
        print("1. Добавить расход")
        print("2. Добавить доход")
        print("3. Просмотреть все операции")
        print("4. Фильтровать операции")
        print("5. Редактировать операцию")
        print("6. Удалить операцию")
        print("7. Статистика")
        print("8. Управление категориями")
        print("9. Бюджеты")
        print("10. Периодические платежи")
        print("11. Импорт/Экспорт CSV")
        print("0. Выход")
        choice = input("> ").strip()
        expenses = load_expenses()
        if choice == '1':
            add_transaction("расход")
        elif choice == '2':
            add_transaction("доход")
        elif choice == '3':
            list_transactions(expenses)
        elif choice == '4':
            filtered = filter_transactions(expenses)
            list_transactions(filtered, "Отфильтрованные операции")
        elif choice == '5':
            edit_transaction(expenses)
        elif choice == '6':
            delete_transaction(expenses)
        elif choice == '7':
            stats_menu()
        elif choice == '8':
            manage_categories()
        elif choice == '9':
            while True:
                cprint("\n--- Бюджеты ---", color='BLUE')
                print("1. Установить бюджет")
                print("2. Проверить все бюджеты")
                print("3. Назад")
                sub = input("> ").strip()
                if sub == '1':
                    set_budget()
                elif sub == '2':
                    check_all_budgets()
                elif sub == '3':
                    break
        elif choice == '10':
            while True:
                cprint("\n--- Периодические платежи ---", color='BLUE')
                print("1. Добавить шаблон")
                print("2. Применить платежи")
                print("3. Назад")
                sub = input("> ").strip()
                if sub == '1':
                    add_recurring()
                elif sub == '2':
                    apply_recurring()
                elif sub == '3':
                    break
        elif choice == '11':
            while True:
                cprint("\n--- Импорт/Экспорт ---", color='BLUE')
                print("1. Экспорт в CSV")
                print("2. Импорт из CSV")
                print("3. Назад")
                sub = input("> ").strip()
                if sub == '1':
                    export_csv()
                elif sub == '2':
                    import_csv()
                elif sub == '3':
                    break
        elif choice == '0':
            cprint("Выход.", color='GREEN')
            break
        else:
            cprint("Неверный выбор.", color='RED')

if __name__ == "__main__":
    main_menu()