[app]
title = Tetris Geopolitics
package.name = tetrisgeo
package.domain = org.tetris
source.dir = .
source.include_exts = py,png,jpg,kv,atlas
version = 0.1

# Зависимости
requirements = python3,kivy

orientation = portrait
fullscreen = 1

# Настройки Android SDK / NDK
android.api = 33
android.minapi = 21
android.ndk = 26b
android.accept_sdk_license = True
android.archs = arm64-v8a

[buildozer]
log_level = 2
warn_on_root = 1
