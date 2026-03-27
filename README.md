# HimeraTools
Кратко говоря, небольшой сборник утилит, но предупрежу сразу: утилиты сырые и писались на линуксе. Буду рад если вы зайдёте в мой телеграмм-канал: https://t.me/HimPerehodnik
1) Если что, tools.py - это лаунчер, который работает через команды. Требуется создать локальные команды с названиями файлов. Как?
1.1) **ВНИМАНИЕ, ЭТО ДЛЯ ЛИНУКСА, с FISH** -- делаем файлы исполнимыми. chmod +x ~/Prog/notes.py ~/Prog/project_manager.py ~/Prog/convert.py ~/Prog/expenses.py ~/Prog/tools.py
1.2) **УБЕДИТЕСЬ, ЧТО У ВАС ЕСТЬ ~/local/bin В PATH** командами: echo $PATH | tr ' ' '\n' | grep -F '/.local/bin'
1.3) **ЕСЛИ У ВАС НЕТУ ~/.local/bin в патче**, то команда: fish_add_path ~/.local/bin 
1.3) Дальше, создаём симлинки
  ln -s ~/Дирректория/К/notes.py ~/.local/bin/notes
  ln -s ~/Директория/К/project_manager.py ~/.local/bin/projects
  ln -s ~/Директория/К/convert.py ~/.local/bin/convert
  ln -s ~/Директория/К/expenses.py ~/.local/bin/expenses
  ln -s ~/Директория/К/tools.py ~/.local/bin/tools
