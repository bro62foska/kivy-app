[app]

# Основная информация
title = Tetris Geo
package.name = tetrisgeo
package.domain = org.tetris

# Исходный код
source.dir = .
source.include_exts = py,png,jpg,kv,atlas,wav,ogg,json

# Иконка приложения
icon.filename = %(source.dir)s/icon.png

# Заставка (экран загрузки) приложения
presplash.filename = %(source.dir)s/icon.png


version = 0.1

# Зависимости (не указывайте точную версию python3, чтобы p4a выбрал совместимую)
requirements = python3,kivy==2.3.0

# Ориентация
orientation = portrait
fullscreen = 0

# Разрешения
android.permissions = INTERNET

# Настройки SDK и NDK
android.api = 33
android.minapi = 21
android.ndk = 25b
android.archs = arm64-v8a
android.accept_sdk_license = True

# Принудительная фиксация стабильного ветки p4a во избежание сбоев с новыми версиями Python
p4a.branch = v2024.01.21

[buildozer]
log_level = 2
warn_on_root = 1
