#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys
import json
import glob
import datetime
import re
from collections import Counter

try:
    from colorama import init, Fore, Style
    init(autoreset=True)
    COLORAMA_AVAILABLE = True
except ImportError:
    COLORAMA_AVAILABLE = False
    class Fore:
        RED = GREEN = YELLOW = BLUE = MAGENTA = CYAN = WHITE = RESET = ''
    class Style:
        BRIGHT = DIM = NORMAL = RESET_ALL = ''

CONFIG_PATH = os.path.expanduser("~/.notes/config.json")
DEFAULT_CONFIG = {
    "notes_dir": os.path.expanduser("~/.notes"),
    "use_colors": True,
    "editor": os.environ.get("EDITOR", "nano")
}

def load_config():
    if os.path.exists(CONFIG_PATH):
        with open(CONFIG_PATH, 'r', encoding='utf-8') as f:
            config = json.load(f)
    else:
        config = DEFAULT_CONFIG.copy()
        save_config(config)
    config["notes_dir"] = os.path.expanduser(config["notes_dir"])
    return config

def save_config(config):
    os.makedirs(os.path.dirname(CONFIG_PATH), exist_ok=True)
    with open(CONFIG_PATH, 'w', encoding='utf-8') as f:
        json.dump(config, f, indent=4, ensure_ascii=False)

config = load_config()
NOTES_DIR = config["notes_dir"]
USE_COLORS = config["use_colors"] and COLORAMA_AVAILABLE

def cprint(text, color=None, style=None, end='\n'):
    if USE_COLORS and color:
        color_code = getattr(Fore, color.upper(), '')
        style_code = getattr(Style, style.upper(), '') if style else ''
        print(f"{style_code}{color_code}{text}{Style.RESET_ALL}", end=end)
    else:
        print(text, end=end)

def get_notes_list():
    pattern = os.path.join(NOTES_DIR, "note_*.txt")
    files = sorted(glob.glob(pattern))
    return files

def read_note(filepath):
    with open(filepath, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    if len(lines) < 2:
        title = "Без названия"
        tags = ""
        content = ""
    else:
        title = lines[0].strip()
        tags = lines[1].strip()
        content = ''.join(lines[2:])
    return title, tags, content

def write_note(filepath, title, tags, content):
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(title + '\n')
        f.write(tags + '\n')
        f.write(content)

def slugify(title):
    trans_dict = {
        'а': 'a', 'б': 'b', 'в': 'v', 'г': 'g', 'д': 'd', 'е': 'e', 'ё': 'yo',
        'ж': 'zh', 'з': 'z', 'и': 'i', 'й': 'y', 'к': 'k', 'л': 'l', 'м': 'm',
        'н': 'n', 'о': 'o', 'п': 'p', 'р': 'r', 'с': 's', 'т': 't', 'у': 'u',
        'ф': 'f', 'х': 'kh', 'ц': 'ts', 'ч': 'ch', 'ш': 'sh', 'щ': 'sch',
        'ъ': '', 'ы': 'y', 'ь': '', 'э': 'e', 'ю': 'yu', 'я': 'ya',
        'А': 'A', 'Б': 'B', 'В': 'V', 'Г': 'G', 'Д': 'D', 'Е': 'E', 'Ё': 'Yo',
        'Ж': 'Zh', 'З': 'Z', 'И': 'I', 'Й': 'Y', 'К': 'K', 'Л': 'L', 'М': 'M',
        'Н': 'N', 'О': 'O', 'П': 'P', 'Р': 'R', 'С': 'S', 'Т': 'T', 'У': 'U',
        'Ф': 'F', 'Х': 'Kh', 'Ц': 'Ts', 'Ч': 'Ch', 'Ш': 'Sh', 'Щ': 'Sch',
        'Ъ': '', 'Ы': 'Y', 'Ь': '', 'Э': 'E', 'Ю': 'Yu', 'Я': 'Ya',
        ' ': '_', '-': '_', ',': '', '.': '', "'": '', '"': '', '!': '', '?': ''
    }
    result = []
    for ch in title:
        if ch in trans_dict:
            result.append(trans_dict[ch])
        elif ch.isalnum() or ch in ('-', '_'):
            result.append(ch)
        else:
            result.append('_')
    slug = ''.join(result).strip('_')
    slug = re.sub(r'_+', '_', slug)
    if len(slug) > 50:
        slug = slug[:50]
    return slug if slug else "note"

def generate_filename(title):
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    slug = slugify(title)
    return f"note_{timestamp}_{slug}.txt"

def search_notes(query, search_title=True, search_tags=True, search_content=True):
    results = []
    for filepath in get_notes_list():
        title, tags, content = read_note(filepath)
        found = False
        if search_title and query.lower() in title.lower():
            found = True
        if not found and search_tags and query.lower() in tags.lower():
            found = True
        if not found and search_content and query.lower() in content.lower():
            found = True
        if found:
            results.append((filepath, title, tags, content))
    return results

def filter_by_tag(tag):
    tag = tag.strip().lower()
    results = []
    for filepath in get_notes_list():
        title, tags_str, content = read_note(filepath)
        tags_list = [t.strip().lower() for t in tags_str.split(',') if t.strip()]
        if tag in tags_list:
            results.append((filepath, title, tags_str, content))
    return results

def get_statistics():
    files = get_notes_list()
    total_notes = len(files)
    tag_counter = Counter()
    total_chars = 0
    total_words = 0
    for filepath in files:
        title, tags_str, content = read_note(filepath)
        total_chars += len(content)
        total_words += len(content.split())
        tags_list = [t.strip().lower() for t in tags_str.split(',') if t.strip()]
        tag_counter.update(tags_list)
    return {
        "total_notes": total_notes,
        "tag_frequency": dict(tag_counter.most_common()),
        "total_chars": total_chars,
        "total_words": total_words
    }

def create_note():
    title = input("Заголовок: ").strip()
    if not title:
        title = "Без заголовка"
    tags = input("Теги (через запятую): ").strip()
    cprint("Введите текст заметки (пустая строка — конец ввода):", color='CYAN')
    lines = []
    while True:
        line = input()
        if line == "":
            break
        lines.append(line)
    content = '\n'.join(lines) + ('\n' if lines else '')
    filename = generate_filename(title)
    filepath = os.path.join(NOTES_DIR, filename)
    counter = 1
    while os.path.exists(filepath):
        name, ext = os.path.splitext(filename)
        filepath = os.path.join(NOTES_DIR, f"{name}_{counter}{ext}")
        counter += 1
    write_note(filepath, title, tags, content)
    cprint(f"Заметка сохранена: {filepath}", color='GREEN')

def list_notes(files=None):
    if files is None:
        files = get_notes_list()
    if not files:
        cprint("Заметок нет.", color='YELLOW')
        return []
    cprint("\nСписок заметок:", color='BLUE', style='BRIGHT')
    for idx, filepath in enumerate(files, start=1):
        title, tags, _ = read_note(filepath)
        if tags:
            cprint(f"{idx}. {title} ", color='WHITE', end='')
            cprint(f"[{tags}]", color='MAGENTA')
        else:
            cprint(f"{idx}. {title}", color='WHITE')
    return files

def view_note():
    files = list_notes()
    if not files:
        return
    try:
        choice = int(input("Введите номер заметки для просмотра: "))
        if 1 <= choice <= len(files):
            filepath = files[choice-1]
            title, tags, content = read_note(filepath)
            cprint(f"\nЗаголовок: {title}", color='GREEN', style='BRIGHT')
            cprint(f"Теги: {tags}", color='MAGENTA')
            cprint("Содержимое:", color='CYAN')
            print(content)
        else:
            cprint("Неверный номер.", color='RED')
    except ValueError:
        cprint("Ошибка ввода (нужно ввести число).", color='RED')

def edit_note():
    files = list_notes()
    if not files:
        return
    try:
        choice = int(input("Введите номер заметки для редактирования: "))
        if 1 <= choice <= len(files):
            filepath = files[choice-1]
            title, tags, content = read_note(filepath)
            cprint(f"Текущий заголовок: {title}", color='YELLOW')
            new_title = input("Новый заголовок (Enter — оставить): ").strip()
            if new_title:
                title = new_title
            cprint(f"Текущие теги: {tags}", color='YELLOW')
            new_tags = input("Новые теги (Enter — оставить): ").strip()
            if new_tags:
                tags = new_tags
            cprint("Текущий текст:", color='YELLOW')
            print(content)
            change_content = input("Изменить текст? (y/n): ").strip().lower()
            if change_content == 'y':
                cprint("Введите новый текст заметки (пустая строка — конец ввода):", color='CYAN')
                lines = []
                while True:
                    line = input()
                    if line == "":
                        break
                    lines.append(line)
                content = '\n'.join(lines) + ('\n' if lines else '')
            write_note(filepath, title, tags, content)
            cprint("Заметка обновлена.", color='GREEN')
        else:
            cprint("Неверный номер.", color='RED')
    except ValueError:
        cprint("Ошибка ввода (нужно ввести число).", color='RED')

def delete_note():
    files = list_notes()
    if not files:
        return
    try:
        choice = int(input("Введите номер заметки для удаления: "))
        if 1 <= choice <= len(files):
            filepath = files[choice-1]
            title, _, _ = read_note(filepath)
            confirm = input(f"Удалить заметку '{title}'? (y/n): ").strip().lower()
            if confirm == 'y':
                os.remove(filepath)
                cprint("Заметка удалена.", color='GREEN')
            else:
                cprint("Удаление отменено.", color='YELLOW')
        else:
            cprint("Неверный номер.", color='RED')
    except ValueError:
        cprint("Ошибка ввода (нужно ввести число).", color='RED')

def search_menu():
    query = input("Введите текст для поиска: ").strip()
    if not query:
        cprint("Пустой запрос.", color='YELLOW')
        return
    cprint("Искать в:", color='CYAN')
    print("1. Заголовках")
    print("2. Тегах")
    print("3. Содержимом")
    print("4. Во всём")
    choice = input("Выберите вариант (1-4): ").strip()
    search_title = search_tags = search_content = False
    if choice == '1':
        search_title = True
    elif choice == '2':
        search_tags = True
    elif choice == '3':
        search_content = True
    elif choice == '4':
        search_title = search_tags = search_content = True
    else:
        cprint("Неверный выбор.", color='RED')
        return
    results = search_notes(query, search_title, search_tags, search_content)
    if not results:
        cprint("Ничего не найдено.", color='YELLOW')
    else:
        cprint(f"Найдено заметок: {len(results)}", color='GREEN')
        for idx, (filepath, title, tags, _) in enumerate(results, start=1):
            if tags:
                cprint(f"{idx}. {title} ", color='WHITE', end='')
                cprint(f"[{tags}]", color='MAGENTA')
            else:
                cprint(f"{idx}. {title}", color='WHITE')
        view_choice = input("Введите номер для просмотра (или Enter для возврата): ").strip()
        if view_choice.isdigit():
            v = int(view_choice)
            if 1 <= v <= len(results):
                filepath, title, tags, content = results[v-1]
                cprint(f"\nЗаголовок: {title}", color='GREEN', style='BRIGHT')
                cprint(f"Теги: {tags}", color='MAGENTA')
                cprint("Содержимое:", color='CYAN')
                print(content)

def filter_by_tag_menu():
    tag = input("Введите тег для фильтрации: ").strip()
    if not tag:
        cprint("Пустой тег.", color='YELLOW')
        return
    results = filter_by_tag(tag)
    if not results:
        cprint(f"Заметок с тегом '{tag}' не найдено.", color='YELLOW')
    else:
        cprint(f"Заметки с тегом '{tag}':", color='BLUE', style='BRIGHT')
        for idx, (filepath, title, tags, _) in enumerate(results, start=1):
            cprint(f"{idx}. {title} [{tags}]", color='WHITE')
        view_choice = input("Введите номер для просмотра (или Enter для возврата): ").strip()
        if view_choice.isdigit():
            v = int(view_choice)
            if 1 <= v <= len(results):
                filepath, title, tags, content = results[v-1]
                cprint(f"\nЗаголовок: {title}", color='GREEN', style='BRIGHT')
                cprint(f"Теги: {tags}", color='MAGENTA')
                cprint("Содержимое:", color='CYAN')
                print(content)

def stats_menu():
    stats = get_statistics()
    cprint("\n=== Статистика ===", color='BLUE', style='BRIGHT')
    cprint(f"Всего заметок: {stats['total_notes']}", color='GREEN')
    cprint(f"Всего символов в тексте: {stats['total_chars']}", color='GREEN')
    cprint(f"Всего слов: {stats['total_words']}", color='GREEN')
    if stats['tag_frequency']:
        cprint("Частота тегов:", color='MAGENTA')
        for tag, count in stats['tag_frequency'].items():
            print(f"  {tag}: {count}")
    else:
        cprint("Нет тегов.", color='YELLOW')

def main():
    if not os.path.exists(NOTES_DIR):
        os.makedirs(NOTES_DIR)
        cprint(f"Создана папка для заметок: {NOTES_DIR}", color='GREEN')
    while True:
        cprint("\n=== Блокнот ===", color='BLUE', style='BRIGHT')
        print("1. Создать заметку")
        print("2. Просмотреть список заметок")
        print("3. Просмотреть содержимое заметки")
        print("4. Редактировать заметку")
        print("5. Удалить заметку")
        print("6. Найти заметку")
        print("7. Фильтр по тегу")
        print("8. Статистика")
        print("9. Выход")
        choice = input("Выберите действие: ").strip()
        if choice == '1':
            create_note()
        elif choice == '2':
            list_notes()
        elif choice == '3':
            view_note()
        elif choice == '4':
            edit_note()
        elif choice == '5':
            delete_note()
        elif choice == '6':
            search_menu()
        elif choice == '7':
            filter_by_tag_menu()
        elif choice == '8':
            stats_menu()
        elif choice == '9':
            cprint("Выход.", color='GREEN')
            break
        else:
            cprint("Неверный выбор, попробуйте снова.", color='RED')

if __name__ == "__main__":
    main()