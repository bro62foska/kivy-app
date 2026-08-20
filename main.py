import math
import os
import random
import struct
import wave

from kivy.app import App
from kivy.clock import Clock
from kivy.core.audio import SoundLoader
from kivy.core.window import Window
from kivy.graphics import (
    Color,
    Ellipse,
    Line,
    Rectangle,
    RoundedRectangle,
    Triangle,
)
from kivy.metrics import dp
from kivy.storage.jsonstore import JsonStore
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.popup import Popup
from kivy.uix.relativelayout import RelativeLayout
from kivy.uix.scrollview import ScrollView
from kivy.uix.widget import Widget

GRID_WIDTH = 10
GRID_HEIGHT = 20

SHAPES = [
    [[1, 1, 1, 1]],  # I
    [[1, 1], [1, 1]],  # O
    [[1, 1, 1], [0, 1, 0]],  # T
    [[1, 1, 0], [0, 1, 1]],  # Z (Молния)
    [[0, 1, 1], [1, 1, 0]],  # S (Молния)
    [[1, 1, 1], [1, 0, 0]],  # J (Г-образная)
    [[1, 1, 1], [0, 0, 1]],  # L (Г-образная)
]

COLORS = [
    (0, 1, 1),  # 0: I - Циан
    (1, 1, 0),  # 1: O - Желтый
    (0.5, 0, 0.5),  # 2: T - Фиолетовый
    (1, 0, 0),  # 3: Z - Красный (Молния)
    (0, 1, 0),  # 4: S - Зеленый (Молния)
    (0, 0, 1),  # 5: J - Синий (Г)
    (1, 0.5, 0),  # 6: L - Оранжевый (Г)
]

LEVEL_LINES_PER_UP = 10
MIN_FALL_FRAMES = 4
BASE_FALL_FRAMES = 15

LANGUAGES = {
    'RU': {
        'title': 'ТЕТРИС\n+ ГЕОПОЛИТИКА',
        'play': 'ИГРАТЬ',
        'settings': 'НАСТРОЙКИ',
        'resume': 'ПРОДОЛЖИТЬ',
        'restart': 'ЗАНОВО',
        'exit': 'ВЫХОД В МЕНЮ',
        'close_app': 'ВЫЙТИ ИЗ ИГРЫ',
        'menu_title': 'ПАУЗА',
        'settings_title': 'НАСТРОЙКИ',
        'close': 'ЗАКРЫТЬ',
        'score': 'СЧЁТ',
        'highscore': 'РЕКОРД',
        'coins': 'МОНЕТЫ',
        'level': 'УРОВЕНЬ',
        'sound_on': 'ЗВУК: ВКЛ',
        'sound_off': 'ЗВУК: ВЫКЛ',
        'diff_title': 'СЛОЖНОСТЬ / DIFFICULTY',
        'diff_1': 'УРОВЕНЬ 1: ЛЕГКИЙ',
        'diff_2': 'УРОВЕНЬ 2: ХАРДКОР',
        'instruction_title': 'КАК ИГРАТЬ:',
        'instructions': (
            '• Свайп Влево / Вправо — передвижение фигуры\n'
            '• Свайп Вверх — повернуть фигуру\n'
            '• Свайп Вниз — быстро сбросить вниз\n\n'
            'УРОВНИ СЛОЖНОСТИ:\n'
            '• Уровень 1: Воришка подменяет только падающую фигуру.\n'
            '• Уровень 2: Воришка подменяет фигуры И крадет "Молнии" / "Г" прямо'
            ' с поля!\n\n'
            'ЗАЩИТА И ПОДКУП:\n'
            '• Нажимай кнопку УДАР!, когда появляется воришка, чтобы выбить'
            ' его!\n'
            '• Кнопка "$" (200 монет на 1 ур. / 500 монет на 2 ур.) — подкуп'
            ' воришки (защита на 30 сек на 1 ур. / 15 сек на 2 ур.)!\n\n'
            'НОВОЕ:\n'
            '• Полупрозрачная тень показывает, куда упадёт фигура.\n'
            f'• Каждые {LEVEL_LINES_PER_UP} линий — новый уровень и рост'
            ' скорости падения!\n'
            '• Быстрый сброс (свайп вниз) даёт бонусные очки за высоту'
            ' падения.'
        ),
    },
    'EN': {
        'title': 'TETRIS\n+ POLITICS',
        'play': 'PLAY',
        'settings': 'SETTINGS',
        'resume': 'RESUME',
        'restart': 'RESTART',
        'exit': 'MAIN MENU',
        'close_app': 'EXIT GAME',
        'menu_title': 'PAUSE',
        'settings_title': 'SETTINGS',
        'close': 'CLOSE',
        'score': 'SCORE',
        'highscore': 'HI-SCORE',
        'coins': 'COINS',
        'level': 'LEVEL',
        'sound_on': 'SOUND: ON',
        'sound_off': 'SOUND: OFF',
        'diff_title': 'DIFFICULTY',
        'diff_1': 'LEVEL 1: EASY',
        'diff_2': 'LEVEL 2: HARDCORE',
        'instruction_title': 'HOW TO PLAY:',
        'instructions': (
            '• Swipe Left / Right — move piece\n'
            '• Swipe Up — rotate piece\n'
            '• Swipe Down — hard drop\n\n'
            'DIFFICULTY LEVELS:\n'
            '• Level 1: Thief only steals falling pieces.\n'
            '• Level 2: Thief steals falling pieces AND pulls "Lightning" / "L"'
            ' blocks from grid!\n\n'
            'DEFENSE & BRIBERY:\n'
            '• Tap PUNCH! button when thief appears to knock him out!\n'
            '• Tap "$" button (200 coins on Lvl 1 / 500 on Lvl 2) to bribe thief'
            ' (30s protection on Lvl 1 / 15s on Lvl 2)!\n\n'
            'NEW:\n'
            '• A translucent ghost shows where the piece will land.\n'
            f'• Every {LEVEL_LINES_PER_UP} lines clears a new level and speeds'
            ' up the drop!\n'
            '• Hard drop (swipe down) now grants bonus points for the'
            ' distance dropped.'
        ),
    },
}


class SoundManager:
  """Generates and plays all game sound effects and background stingers.

  All tones are syn
