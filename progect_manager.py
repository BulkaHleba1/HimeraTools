#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys
import json
import glob
import subprocess
from datetime import datetime
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
PROJECTS_FILE = os.path.join(TOOLS_DIR, "projects.json")
DEFAULT_CATEGORIES = ["работа", "личное", "открытый код", "закрытый код"]
DEFAULT_STATUSES = ["active", "completed", "archived"]

def cprint(text, color=None, style=None, end='\n'):
    if COLORAMA and color:
        color_code = getattr(Fore, color.upper(), '')
        style_code = getattr(Style, style.upper(), '') if style else ''
        print(f"{style_code}{color_code}{text}{Style.RESET_ALL}", end=end)
    else:
        print(text, end=end)

def ensure_tools_dir():
    os.makedirs(TOOLS_DIR, exist_ok=True)

def load_projects():
    ensure_tools_dir()
    if os.path.exists(PROJECTS_FILE):
        with open(PROJECTS_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return []

def save_projects(projects):
    ensure_tools_dir()
    with open(PROJECTS_FILE, 'w', encoding='utf-8') as f:
        json.dump(projects, f, indent=4, ensure_ascii=False)

def get_next_id(projects):
    if not projects:
        return 1
    return max(p['id'] for p in projects) + 1

def select_from_list(items, prompt="Выберите номер: ", multiple=False):
    for i, item in enumerate(items, 1):
        print(f"{i}. {item}")
    while True:
        choice = input(prompt).strip()
        if not choice:
            return None if not multiple else []
        if multiple:
            parts = choice.split()
            indices = []
            valid = True
            for p in parts:
                if p.isdigit() and 1 <= int(p) <= len(items):
                    indices.append(int(p)-1)
                else:
                    valid = False
                    break
            if valid and indices:
                return indices
            else:
                cprint("Неверный ввод. Введите номера через пробел.", color='RED')
        else:
            if choice.isdigit() and 1 <= int(choice) <= len(items):
                return int(choice)-1
            else:
                cprint("Неверный номер.", color='RED')

def input_with_default(prompt, default=""):
    val = input(f"{prompt} [{default}]: ").strip()
    return val if val else default

def choose_directory_manual():
    path = input("Введите путь к папке проекта: ").strip()
    if not path:
        return None
    expanded = os.path.expanduser(path)
    if os.path.isdir(expanded):
        return expanded
    else:
        cprint("Папка не существует.", color='RED')
        return None

def choose_directory_fzf():
    try:
        result = subprocess.run(
            ["fzf", "--directory"],
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            text=True
        )
        if result.returncode == 0:
            return result.stdout.strip()
        else:
            return None
    except FileNotFoundError:
        return None

def choose_directory():
    fzf_path = choose_directory_fzf()
    if fzf_path:
        return fzf_path
    else:
        cprint("fzf не найден, используйте ручной ввод.", color='YELLOW')
        return choose_directory_manual()

def add_project(projects):
    cprint("\n--- Добавление проекта ---", color='BLUE', style='BRIGHT')
    path = choose_directory()
    if not path:
        return
    default_name = os.path.basename(path)
    name = input_with_default("Название проекта", default_name)
    description = input("Краткое описание: ").strip()
    tech_input = input("Технологии (через запятую): ").strip()
    technologies = [t.strip() for t in tech_input.split(',') if t.strip()]
    cprint("Выберите статус:", color='CYAN')
    status_idx = select_from_list(DEFAULT_STATUSES, "Статус (номер): ")
    if status_idx is None:
        status = "active"
    else:
        status = DEFAULT_STATUSES[status_idx]
    cprint("Выберите категории (можно несколько номеров через пробел):", color='CYAN')
    cat_indices = select_from_list(DEFAULT_CATEGORIES, "Категории: ", multiple=True)
    if cat_indices is None:
        categories = []
    else:
        categories = [DEFAULT_CATEGORIES[i] for i in cat_indices]
    new_id = get_next_id(projects)
    project = {
        "id": new_id,
        "name": name,
        "path": path,
        "description": description,
        "technologies": technologies,
        "status": status,
        "categories": categories,
        "last_opened": None,
        "created": datetime.now().isoformat()
    }
    projects.append(project)
    save_projects(projects)
    cprint(f"Проект '{name}' добавлен с ID {new_id}.", color='GREEN')

def list_projects(projects, show_filter_hint=True):
    if not projects:
        cprint("Нет проектов.", color='YELLOW')
        return []
    cprint("\n{:<4} {:<30} {:<10} {:<20} {:<20} {}".format(
        "ID", "Название", "Статус", "Технологии", "Категории", "Путь"),
        color='WHITE', style='BRIGHT')
    for p in projects:
        tech = ", ".join(p['technologies'])[:18] + ("..." if len(p['technologies'])>3 else "")
        cats = ", ".join(p['categories'])[:18]
        path_short = p['path'] if len(p['path']) < 30 else "..." + p['path'][-27:]
        print("{:<4} {:<30} {:<10} {:<20} {:<20} {}".format(
            p['id'], p['name'][:28], p['status'], tech, cats, path_short))
    if show_filter_hint:
        print("\nДля фильтрации используйте пункт меню 'Фильтровать'.")
    return projects

def filter_projects(projects):
    cprint("\n--- Фильтрация ---", color='BLUE')
    filter_status = input("Статус (оставьте пустым для всех): ").strip().lower()
    filter_tech = input("Технология (подстрока): ").strip().lower()
    filtered = []
    for p in projects:
        if filter_status and p['status'].lower() != filter_status:
            continue
        if filter_tech:
            if not any(filter_tech in t.lower() for t in p['technologies']):
                continue
        filtered.append(p)
    if not filtered:
        cprint("Нет проектов, удовлетворяющих фильтру.", color='YELLOW')
    return filtered

def go_to_project(projects):
    filtered = list_projects(projects, show_filter_hint=False)
    if not filtered:
        return
    try:
        choice = int(input("Введите ID проекта для перехода: "))
        proj = next((p for p in filtered if p['id'] == choice), None)
        if proj:
            cprint(f"\nЧтобы перейти в папку, выполните:\n  cd {proj['path']}", color='GREEN')
        else:
            cprint("Проект с таким ID не найден.", color='RED')
    except ValueError:
        cprint("Ошибка ввода.", color='RED')

def delete_project(projects):
    filtered = list_projects(projects, show_filter_hint=False)
    if not filtered:
        return
    try:
        choice = int(input("Введите ID проекта для удаления: "))
        proj = next((p for p in filtered if p['id'] == choice), None)
        if not proj:
            cprint("ID не найден.", color='RED')
            return
        cprint(f"Проект: {proj['name']} ({proj['path']})", color='YELLOW')
        confirm = input("Удалить проект из списка? (y/n): ").strip().lower()
        if confirm == 'y':
            projects[:] = [p for p in projects if p['id'] != choice]
            save_projects(projects)
            cprint("Проект удалён из списка.", color='GREEN')
            del_files = input("Удалить физическую папку проекта? (y/n): ").strip().lower()
            if del_files == 'y':
                import shutil
                try:
                    shutil.rmtree(proj['path'])
                    cprint("Папка удалена.", color='GREEN')
                except Exception as e:
                    cprint(f"Ошибка удаления папки: {e}", color='RED')
    except ValueError:
        cprint("Ошибка ввода.", color='RED')

def edit_project(projects):
    filtered = list_projects(projects, show_filter_hint=False)
    if not filtered:
        return
    try:
        choice = int(input("Введите ID проекта для редактирования: "))
        proj = next((p for p in filtered if p['id'] == choice), None)
        if not proj:
            cprint("ID не найден.", color='RED')
            return
        cprint(f"Редактирование проекта '{proj['name']}'. Оставьте поле пустым для сохранения текущего значения.", color='CYAN')
        new_name = input_with_default("Название", proj['name'])
        proj['name'] = new_name
        new_path = input_with_default("Путь", proj['path'])
        if new_path and os.path.isdir(os.path.expanduser(new_path)):
            proj['path'] = os.path.expanduser(new_path)
        else:
            cprint("Путь не изменён (некорректный или не существует).", color='YELLOW')
        new_desc = input_with_default("Описание", proj['description'])
        proj['description'] = new_desc
        new_tech = input_with_default("Технологии (через запятую)", ", ".join(proj['technologies']))
        proj['technologies'] = [t.strip() for t in new_tech.split(',') if t.strip()]
        cprint("Текущий статус: " + proj['status'], color='YELLOW')
        status_idx = select_from_list(DEFAULT_STATUSES, "Новый статус (номер или Enter для пропуска): ")
        if status_idx is not None:
            proj['status'] = DEFAULT_STATUSES[status_idx]
        cprint("Текущие категории: " + ", ".join(proj['categories']), color='YELLOW')
        cprint("Выберите новые категории (номера через пробел, Enter для пропуска):")
        cat_indices = select_from_list(DEFAULT_CATEGORIES, "Категории: ", multiple=True)
        if cat_indices is not None:
            proj['categories'] = [DEFAULT_CATEGORIES[i] for i in cat_indices]
        save_projects(projects)
        cprint("Проект обновлён.", color='GREEN')
    except ValueError:
        cprint("Ошибка ввода.", color='RED')

def scan_directories(projects):
    cprint("\n--- Сканирование директорий ---", color='BLUE')
    root_dirs_input = input("Введите корневые папки для поиска (через пробел): ").strip()
    if not root_dirs_input:
        return
    root_dirs = [os.path.expanduser(d) for d in root_dirs_input.split()]
    found = []
    for root in root_dirs:
        if not os.path.isdir(root):
            cprint(f"Папка {root} не существует, пропускаем.", color='YELLOW')
            continue
        for item in os.listdir(root):
            path = os.path.join(root, item)
            if os.path.isdir(path):
                if any(p['path'] == path for p in projects):
                    continue
                found.append(path)
            else:
                subpath = os.path.join(root, item)
                if os.path.isdir(subpath):
                    if any(p['path'] == subpath for p in projects):
                        continue
                    found.append(subpath)
    if not found:
        cprint("Новых проектов не найдено.", color='YELLOW')
        return
    cprint("Найдены папки, которые можно добавить как проекты:", color='GREEN')
    for i, path in enumerate(found, 1):
        print(f"{i}. {path}")
    to_add = input("Введите номера для добавления (через пробел) или Enter для пропуска: ").strip()
    if not to_add:
        return
    indices = []
    for part in to_add.split():
        if part.isdigit():
            idx = int(part)-1
            if 0 <= idx < len(found):
                indices.append(idx)
    for idx in indices:
        path = found[idx]
        default_name = os.path.basename(path)
        name = input_with_default(f"Название для {path}", default_name)
        description = input("Краткое описание: ").strip()
        tech_input = input("Технологии (через запятую): ").strip()
        technologies = [t.strip() for t in tech_input.split(',') if t.strip()]
        cprint("Выберите статус:", color='CYAN')
        status_idx = select_from_list(DEFAULT_STATUSES, "Статус (номер): ")
        status = DEFAULT_STATUSES[status_idx] if status_idx is not None else "active"
        cprint("Выберите категории (номера через пробел):", color='CYAN')
        cat_indices = select_from_list(DEFAULT_CATEGORIES, "Категории: ", multiple=True)
        categories = [DEFAULT_CATEGORIES[i] for i in cat_indices] if cat_indices else []
        new_id = get_next_id(projects)
        project = {
            "id": new_id,
            "name": name,
            "path": path,
            "description": description,
            "technologies": technologies,
            "status": status,
            "categories": categories,
            "last_opened": None,
            "created": datetime.now().isoformat()
        }
        projects.append(project)
        cprint(f"Проект '{name}' добавлен.", color='GREEN')
    save_projects(projects)

def main_menu():
    projects = load_projects()
    while True:
        cprint("\n=== Менеджер проектов ===", color='BLUE', style='BRIGHT')
        print("1. Добавить проект")
        print("2. Список всех проектов")
        print("3. Фильтровать проекты")
        print("4. Перейти в папку проекта")
        print("5. Удалить проект")
        print("6. Редактировать проект")
        print("7. Сканировать директории для добавления")
        print("8. Выход")
        choice = input("Выберите действие: ").strip()
        if choice == '1':
            add_project(projects)
        elif choice == '2':
            list_projects(projects)
        elif choice == '3':
            filtered = filter_projects(projects)
            if filtered:
                list_projects(filtered, show_filter_hint=False)
        elif choice == '4':
            go_to_project(projects)
        elif choice == '5':
            delete_project(projects)
        elif choice == '6':
            edit_project(projects)
        elif choice == '7':
            scan_directories(projects)
        elif choice == '8':
            cprint("Выход.", color='GREEN')
            break
        else:
            cprint("Неверный выбор.", color='RED')

if __name__ == "__main__":
    main_menu()