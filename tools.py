#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys
import subprocess

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

TOOLS = [
    ("Блокнот (заметки)", "notes"),
    ("Менеджер проектов", "projects"),
    ("Конвертер величин", "convert"),
    ("Калькулятор расходов", "expenses"),
]

def cprint(text, color=None, style=None, end='\n'):
    if COLORAMA and color:
        color_code = getattr(Fore, color.upper(), '')
        style_code = getattr(Style, style.upper(), '') if style else ''
        print(f"{style_code}{color_code}{text}{Style.RESET_ALL}", end=end)
    else:
        print(text, end=end)

def show_menu():
    cprint("\n=== Единый лаунчер инструментов ===", color='BLUE', style='BRIGHT')
    for i, (name, _) in enumerate(TOOLS, 1):
        print(f"{i}. {name}")
    print("0. Выход")
    choice = input("Выберите инструмент: ").strip()
    if choice == '0':
        return None
    if choice.isdigit() and 1 <= int(choice) <= len(TOOLS):
        return int(choice) - 1
    else:
        cprint("Неверный выбор.", color='RED')
        return -1

def run_tool(cmd, args=None):
    full_cmd = [cmd]
    if args:
        full_cmd.extend(args)
    try:
        subprocess.run(full_cmd)
    except FileNotFoundError:
        cprint(f"Ошибка: команда '{cmd}' не найдена. Убедитесь, что она установлена и доступна в PATH.", color='RED')
    except Exception as e:
        cprint(f"Ошибка запуска: {e}", color='RED')

def main():
    if len(sys.argv) > 1:
        tool_arg = sys.argv[1].lower()
        for name, cmd in TOOLS:
            if tool_arg == cmd or tool_arg == name.split()[0].lower():
                run_tool(cmd, sys.argv[2:])
                return
        cprint(f"Неизвестный инструмент: {tool_arg}", color='RED')
        print("Доступные инструменты:")
        for name, cmd in TOOLS:
            print(f"  {cmd} - {name}")
        sys.exit(1)

    while True:
        idx = show_menu()
        if idx is None:
            cprint("Выход.", color='GREEN')
            break
        elif idx == -1:
            continue
        else:
            cmd = TOOLS[idx][1]
            run_tool(cmd)
            input("\nНажмите Enter, чтобы продолжить...")

if __name__ == "__main__":
    main()