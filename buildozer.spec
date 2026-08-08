[app]

# Название вашего приложения
title = My Kivy App

# Имя пакета (без пробелов, латиницей)
package.name = mykivyapp

# Домен пакета
package.domain = org.test

# Список файлов исходного кода (через запятую)
source.include_exts = py,png,jpg,kv,atlas

# Главный файл приложения
source.main = main.py

# Версия приложения
version = 0.1

# Требования к приложениям (укажите kivy, а также сторонние библиотеки, если они есть, например, requests)
requirements = python3,kivy

# Поддерживаемая ориентация экрана
orientation = portrait

# Разрешения для Android (если нужно интернет-соединение, раскомментируйте строку ниже)
# android.permissions = INTERNET

[buildozer]
log_level = 2
warn_on_root = 1
