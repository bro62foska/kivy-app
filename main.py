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

  All tones are synthesized with sine-wave harmonics (instead of hard
  square waves) plus smooth attack/decay envelopes, so they sound like
  soft synth/bell tones rather than harsh 8-bit buzzes.
  """

  def __init__(self, sound_dir='sounds'):
    self.sound_dir = sound_dir
    self.sounds = {}
    self.enabled = True
    self.ensure_sounds_exist()
    self.load_sounds()

  def ensure_sounds_exist(self):
    if not os.path.exists(self.sound_dir):
      os.makedirs(self.sound_dir)

    self._gen_wave('move', self._synth_move)
    self._gen_wave('rotate', self._synth_rotate)
    self._gen_wave('drop', self._synth_drop)
    self._gen_wave('clear', self._synth_clear)
    self._gen_wave('punch', self._synth_punch)
    self._gen_wave('gameover', self._synth_gameover)
    self._gen_wave('laugh', self._synth_laugh)
    self._gen_wave('levelup', self._synth_levelup)
    self._gen_wave('bribe_bg', lambda p: self._synth_bribe_music(p, tempo=1.0))
    self._gen_wave(
        'bribe_bg_fast', lambda p: self._synth_bribe_music(p, tempo=1.5)
    )

  def _gen_wave(self, name, generator_func):
    filepath = os.path.join(self.sound_dir, f'{name}.wav')
    if not os.path.exists(filepath):
      generator_func(filepath)

  def _write_wav(self, filepath, samples, sample_rate=22050):
    with wave.open(filepath, 'w') as wf:
      wf.setnchannels(1)
      wf.setsampwidth(2)
      wf.setframerate(sample_rate)
      for s in samples:
        val = max(-32768, min(32767, int(s)))
        wf.writeframes(struct.pack('<h', val))

  # ---- Natural-sound synthesis helpers -----------------------------------

  def _tone_samples(
      self,
      freq_func,
      n_samples,
      sr,
      amplitude,
      harmonics=(1.0, 0.45, 0.18),
      attack=0.006,
      release_curve=3.0,
      noise_amt=0.0,
      vibrato_hz=0.0,
      vibrato_depth=0.0,
  ):
    """Builds one natural-sounding tone as a list of PCM sample values.

    Uses real sine waves (not square waves) with a handful of decaying
    harmonic overtones for warmth, a short linear attack to avoid clicks,
    and a smooth exponential decay instead of a hard linear ramp.
    """
    samples = []
    attack_samples = max(1, int(sr * attack))
    harmonic_sum = sum(harmonics) or 1.0
    for i in range(n_samples):
      t = i / sr
      freq = freq_func(i, n_samples)
      if vibrato_hz > 0 and vibrato_depth > 0:
        freq += math.sin(2 * math.pi * vibrato_hz * t) * vibrato_depth

      val = 0.0
      for h_index, h_amp in enumerate(harmonics, start=1):
        val += math.sin(2 * math.pi * freq * h_index * t) * h_amp
      val /= harmonic_sum

      if i < attack_samples:
        env = i / attack_samples
      else:
        progress = (i - attack_samples) / max(1, (n_samples - attack_samples))
        env = math.exp(-release_curve * progress)

      if noise_amt > 0:
        val = val * (1 - noise_amt) + (random.random() * 2 - 1) * noise_amt

      samples.append(val * amplitude * env)
    return samples

  def _synth_move(self, path):
    sr, dur = 22050, 0.05
    n = int(sr * dur)
    samples = self._tone_samples(
        freq_func=lambda i, n_: 300 - 40 * (i / n_),
        n_samples=n,
        sr=sr,
        amplitude=9000,
        harmonics=(1.0, 0.3),
        attack=0.003,
        release_curve=5.0,
    )
    self._write_wav(path, samples, sr)

  def _synth_rotate(self, path):
    sr, dur = 22050, 0.09
    n = int(sr * dur)
    samples = self._tone_samples(
        freq_func=lambda i, n_: 480 + 220 * (i / n_),
        n_samples=n,
        sr=sr,
        amplitude=10000,
        harmonics=(1.0, 0.4, 0.15),
        attack=0.004,
        release_curve=4.0,
    )
    self._write_wav(path, samples, sr)

  def _synth_drop(self, path):
    sr, dur = 22050, 0.16
    n = int(sr * dur)
    samples = self._tone_samples(
        freq_func=lambda i, n_: 260 - 160 * (i / n_),
        n_samples=n,
        sr=sr,
        amplitude=13000,
        harmonics=(1.0, 0.5, 0.2),
        attack=0.004,
        release_curve=2.5,
        noise_amt=0.08,
    )
    self._write_wav(path, samples, sr)

  def _synth_clear(self, path):
    sr = 22050
    notes = [523.25, 659.25, 783.99, 1046.50]
    note_dur = 0.11
    gap_dur = 0.015
    samples = []
    for freq in notes:
      n = int(sr * note_dur)
      samples.extend(
          self._tone_samples(
              freq_func=lambda i, n_, f=freq: f,
              n_samples=n,
              sr=sr,
              amplitude=11000,
              harmonics=(1.0, 0.5, 0.25, 0.1),
              attack=0.008,
              release_curve=3.5,
          )
      )
      samples.extend([0] * int(sr * gap_dur))
    self._write_wav(path, samples, sr)

  def _synth_punch(self, path):
    sr, dur = 22050, 0.14
    n = int(sr * dur)
    samples = self._tone_samples(
        freq_func=lambda i, n_: 130 - 70 * (i / n_),
        n_samples=n,
        sr=sr,
        amplitude=17000,
        harmonics=(1.0, 0.6),
        attack=0.002,
        release_curve=6.0,
        noise_amt=0.22,
    )
    self._write_wav(path, samples, sr)

  def _synth_gameover(self, path):
    sr = 22050
    notes = [400, 340, 280, 200]
    note_dur = 0.22
    gap_dur = 0.02
    samples = []
    for freq in notes:
      n = int(sr * note_dur)
      samples.extend(
          self._tone_samples(
              freq_func=lambda i, n_, f=freq: f,
              n_samples=n,
              sr=sr,
              amplitude=12000,
              harmonics=(1.0, 0.45, 0.2),
              attack=0.01,
              release_curve=2.2,
          )
      )
      samples.extend([0] * int(sr * gap_dur))
    self._write_wav(path, samples, sr)

  def _synth_laugh(self, path):
    sr = 22050
    bursts = [
        (550, 400, 0.08),
        (650, 450, 0.08),
        (750, 500, 0.08),
        (950, 300, 0.18),
    ]
    samples = []
    for start_freq, end_freq, dur in bursts:
      n = int(sr * dur)
      burst = self._tone_samples(
          freq_func=lambda i, n_, sf=start_freq, ef=end_freq: (
              sf + (ef - sf) * (i / n_)
          ),
          n_samples=n,
          sr=sr,
          amplitude=13000,
          harmonics=(1.0, 0.5, 0.2),
          attack=0.015,
          release_curve=1.5,
      )
      # Мягкая "колокольная" огибающая (нарастание-спад) вместо резкого среза,
      # чтобы смешок звучал более естественно, не как писк.
      for idx in range(len(burst)):
        shape = math.sin(math.pi * (idx / len(burst)))
        burst[idx] *= shape
      samples.extend(burst)
      samples.extend([0] * int(sr * 0.03))
    self._write_wav(path, samples, sr)

  def _synth_levelup(self, path):
    # Бодрый восходящий арпеджио-аккорд для перехода на новый уровень.
    sr = 22050
    notes = [523.25, 659.25, 783.99, 1046.50, 1318.51]
    note_dur = 0.09
    samples = []
    for freq in notes:
      n = int(sr * note_dur)
      samples.extend(
          self._tone_samples(
              freq_func=lambda i, n_, f=freq: f,
              n_samples=n,
              sr=sr,
              amplitude=12000,
              harmonics=(1.0, 0.5, 0.25, 0.1),
              attack=0.005,
              release_curve=3.0,
          )
      )
    self._write_wav(path, samples, sr)

  def _synth_bribe_music(self, path, tempo=1.0):
    sr = 22050
    notes = [
        (392.00, 0.12),
        (523.25, 0.12),
        (659.25, 0.12),
        (523.25, 0.22),
        (392.00, 0.12),
        (523.25, 0.12),
        (659.25, 0.12),
        (523.25, 0.22),
        (440.00, 0.12),
        (493.88, 0.12),
        (523.25, 0.12),
        (587.33, 0.12),
        (659.25, 0.24),
        (392.00, 0.12),
        (523.25, 0.12),
        (659.25, 0.12),
        (523.25, 0.22),
        (392.00, 0.12),
        (523.25, 0.12),
        (659.25, 0.12),
        (523.25, 0.22),
        (698.46, 0.12),
        (659.25, 0.12),
        (587.33, 0.12),
        (523.25, 0.12),
        (493.88, 0.12),
        (587.33, 0.12),
        (523.25, 0.35),
    ]
    samples = []
    for freq, dur in notes:
      actual_dur = dur / tempo
      n = int(sr * actual_dur)
      note = self._tone_samples(
          freq_func=lambda i, n_, f=freq: f,
          n_samples=n,
          sr=sr,
          # Амплитуда снижена для мягкого и очень тихого фонового звучания
          amplitude=1400,
          harmonics=(1.0, 0.5, 0.2, 0.08),
          attack=0.012,
          release_curve=1.8,
          vibrato_hz=5.0,
          vibrato_depth=1.5,
      )
      samples.extend(note)
    self._write_wav(path, samples, sr)

  def load_sounds(self):
    for name in [
        'move',
        'rotate',
        'drop',
        'clear',
        'punch',
        'gameover',
        'laugh',
        'levelup',
        'bribe_bg',
        'bribe_bg_fast',
    ]:
      filepath = os.path.join(self.sound_dir, f'{name}.wav')
      snd = SoundLoader.load(filepath)
      if snd:
        self.sounds[name] = snd

  def play(self, sound_name, loop=False):
    if not self.enabled:
      return
    snd = self.sounds.get(sound_name)
    if snd:
      if snd.state == 'play':
        snd.stop()
      snd.loop = loop
      # Настройка громкости (для музыки подкупа установлена тихая громкость 15%)
      if 'bribe' in sound_name:
        snd.volume = 0.15
      else:
        snd.volume = 1.0
      snd.play()

  def stop(self, sound_name):
    snd = self.sounds.get(sound_name)
    if snd and snd.state == 'play':
      snd.stop()

  def stop_all(self):
    for snd in self.sounds.values():
      if snd.state == 'play':
        snd.stop()


class GradientBG(Widget):
  """Simple dark vertical-gradient background used behind the main menu."""

  def __init__(self, top_color=(0.06, 0.09, 0.18, 1),
               bottom_color=(0.01, 0.01, 0.03, 1), **kwargs):
    super().__init__(**kwargs)
    self.top_color = top_color
    self.bottom_color = bottom_color
    self.bind(pos=self.redraw, size=self.redraw)

  def redraw(self, *args):
    self.canvas.clear()
    if self.width <= 0 or self.height <= 0:
      return
    strips = 48
    strip_h = self.height / strips
    tr, tg, tb, ta = self.top_color
    br, bg, bb, ba = self.bottom_color
    with self.canvas:
      for i in range(strips):
        frac = i / max(1, strips - 1)
        r = tr + (br - tr) * frac
        g = tg + (bg - tg) * frac
        b = tb + (bb - tb) * frac
        a = ta + (ba - ta) * frac
        Color(r, g, b, a)
        Rectangle(
            pos=(self.x, self.y + self.height - (i + 1) * strip_h),
            size=(self.width, strip_h + 1),
        )


class FallingBlocksBG(Widget):
  """Animated decorative tetromino-block rain for the main menu splash."""

  def __init__(self, block_count=16, **kwargs):
    super().__init__(**kwargs)
    self.block_count = block_count
    self.blocks = []
    self._event = None
    self._initialized = False
    self.bind(pos=self.redraw, size=self.on_size_change)

  def on_size_change(self, *args):
    if self.width > 0 and self.height > 0 and not self._initialized:
      self._init_blocks()
      self._initialized = True
    self.redraw()

  def start(self):
    if not self._event:
      self._event = Clock.schedule_interval(self.update, 1 / 30)

  def stop(self):
    if self._event:
      self._event.cancel()
      self._event = None

  def _make_block(self, spawn_from_top=True):
    size = random.uniform(dp(14), dp(30))
    x = random.uniform(0, max(1.0, self.width - size))
    if spawn_from_top:
      y = self.height + size
    else:
      y = random.uniform(0, self.height)
    color = random.choice(COLORS)
    return {
        'x': x,
        'y': y,
        'size': size,
        'color': (color[0], color[1], color[2], random.uniform(0.10, 0.26)),
        'speed': random.uniform(dp(18), dp(50)),
    }

  def _init_blocks(self):
    self.blocks = [
        self._make_block(spawn_from_top=False) for _ in range(self.block_count)
    ]

  def update(self, dt):
    if self.height <= 0 or not self.blocks:
      return
    for b in self.blocks:
      b['y'] -= b['speed'] * dt
      if b['y'] < -b['size']:
        b.update(self._make_block(spawn_from_top=True))
    self.redraw()

  def redraw(self, *args):
    self.canvas.clear()
    if self.width <= 0 or self.height <= 0 or not self.blocks:
      return
    with self.canvas:
      for b in self.blocks:
        Color(*b['color'])
        Rectangle(
            pos=(self.x + b['x'], self.y + b['y']),
            size=(b['size'], b['size']),
        )


class ModernButton(Button):
  """Flat, rounded, glowing-border button used for the redesigned menu."""

  def __init__(self, base_color=(0.2, 0.6, 1, 1), **kwargs):
    super().__init__(**kwargs)
    self.base_color = base_color
    self.background_color = (0, 0, 0, 0)
    self.color = (1, 1, 1, 1)
    self.bold = True
    self.bind(
        pos=self.update_canvas,
        size=self.update_canvas,
        state=self.update_canvas,
    )

  def update_canvas(self, *args):
    self.canvas.before.clear()
    if self.width <= 0 or self.height <= 0:
      return

    r, g, b, a = self.base_color
    with self.canvas.before:
      Color(0, 0, 0, 0.35)
      RoundedRectangle(
          pos=(self.x + dp(2), self.y - dp(2)),
          size=self.size,
          radius=[dp(14)],
      )

      if self.state == 'down':
        Color(r * 0.75, g * 0.75, b * 0.75, a)
      else:
        Color(r, g, b, a)
      RoundedRectangle(pos=self.pos, size=self.size, radius=[dp(14)])

      Color(1, 1, 1, 0.3)
      Line(
          rounded_rectangle=(self.x, self.y, self.width, self.height, dp(14)),
          width=dp(1.2),
      )


class StylishMenuButton(Button):

  def __init__(self, **kwargs):
    super().__init__(**kwargs)
    self.background_color = (0, 0, 0, 0)
    self.text = ''
    self.bind(
        pos=self.update_canvas,
        size=self.update_canvas,
        state=self.update_canvas,
    )

  def update_canvas(self, *args):
    self.canvas.before.clear()
    self.canvas.after.clear()
    if self.width <= 0 or self.height <= 0:
      return

    with self.canvas.before:
      Color(0, 0, 0, 0.35)
      RoundedRectangle(
          pos=(self.x + dp(2), self.y - dp(2)),
          size=self.size,
          radius=[dp(12)],
      )

      if self.state == 'down':
        Color(0.2, 0.5, 0.9, 0.95)
      else:
        Color(0.12, 0.12, 0.16, 0.85)
      RoundedRectangle(pos=self.pos, size=self.size, radius=[dp(12)])

      Color(0.3, 0.5, 0.9, 0.5)
      Line(
          rounded_rectangle=(self.x, self.y, self.width, self.height, dp(12)),
          width=dp(1.2),
      )

    with self.canvas.after:
      Color(1, 1, 1, 0.9)
      pad_x = self.width * 0.28
      start_x = self.x + pad_x
      end_x = self.x + self.width - pad_x

      h = self.height
      line_w = dp(2)

      Line(
          points=[start_x, self.y + h * 0.68, end_x, self.y + h * 0.68],
          width=line_w,
      )
      Line(
          points=[start_x, self.y + h * 0.50, end_x, self.y + h * 0.50],
          width=line_w,
      )
      Line(
          points=[start_x, self.y + h * 0.32, end_x, self.y + h * 0.32],
          width=line_w,
      )


class DollarButton(Button):

  def __init__(self, **kwargs):
    super().__init__(**kwargs)
    self.background_color = (0, 0, 0, 0)
    self.font_size = '20sp'
    self.bold = True
    self.usable = False
    self.text = '$'
    self.bind(
        pos=self.update_canvas,
        size=self.update_canvas,
        state=self.update_canvas,
    )

  def set_state_info(self, usable, text_val='$'):
    self.usable = usable
    self.text = text_val
    self.update_canvas()

  def update_canvas(self, *args):
    self.canvas.before.clear()
    if self.width <= 0 or self.height <= 0:
      return

    with self.canvas.before:
      Color(0, 0, 0, 0.35)
      RoundedRectangle(
          pos=(self.x + dp(2), self.y - dp(2)),
          size=self.size,
          radius=[dp(12)],
      )

      if self.usable:
        if self.state == 'down':
          Color(1, 0.7, 0, 0.95)
        else:
          Color(1, 0.84, 0, 0.95)
        self.color = (0.1, 0.1, 0.1, 1)
      else:
        Color(0.22, 0.22, 0.26, 0.85)
        self.color = (0.6, 0.6, 0.6, 1)

      RoundedRectangle(pos=self.pos, size=self.size, radius=[dp(12)])

      line_color = (
          (1, 1, 0.5, 0.8) if self.usable else (0.4, 0.4, 0.4, 0.5)
      )
      Color(*line_color)
      Line(
          rounded_rectangle=(self.x, self.y, self.width, self.height, dp(12)),
          width=dp(1.2),
      )


class FistButton(Button):

  def __init__(self, **kwargs):
    super().__init__(**kwargs)
    self.background_color = (0, 0, 0, 0)
    self.font_size = '22sp'
    self.bold = True
    self.color = (1, 1, 1, 1)
    self.bind(
        pos=self.update_canvas,
        size=self.update_canvas,
        state=self.update_canvas,
    )

  def update_canvas(self, *args):
    self.canvas.before.clear()
    if self.width <= 0 or self.height <= 0:
      return

    with self.canvas.before:
      Color(0, 0, 0, 0.4)
      RoundedRectangle(
          pos=(self.x + dp(3), self.y - dp(3)),
          size=self.size,
          radius=[dp(16)],
      )

      if self.state == 'down':
        Color(0.75, 0.15, 0.1, 0.95)
      else:
        Color(0.9, 0.25, 0.15, 0.95)
      RoundedRectangle(pos=self.pos, size=self.size, radius=[dp(16)])

      Color(1, 0.8, 0.2, 0.9)
      Line(
          rounded_rectangle=(self.x, self.y, self.width, self.height, dp(16)),
          width=dp(2),
      )


class TetrisBoard(Widget):

  def __init__(self, game_ref, **kwargs):
    super().__init__(**kwargs)
    self.game = game_ref
    self.touch_start_pos = None
    self.block_size = dp(1)
    self.board_w = 0
    self.board_h = 0
    self.ox = 0
    self.oy = 0
    self.bind(size=self.draw_board, pos=self.draw_board)

  def draw_board(self, *args):
    self.canvas.clear()
    if (
        self.width <= 0
        or self.height <= 0
        or self.game.state not in ['playing', 'paused']
    ):
      return

    available_height = max(dp(50), self.height - dp(180))
    self.block_size = max(
        dp(4), min(self.width / GRID_WIDTH, available_height / GRID_HEIGHT)
    )
    self.board_w = self.block_size * GRID_WIDTH
    self.board_h = self.block_size * GRID_HEIGHT

    self.ox = self.x + (self.width - self.board_w) / 2
    self.oy = self.y + (available_height - self.board_h) / 2 + dp(80)

    if self.game.btn_fist:
      btn_w = int(self.board_w * 0.45)
      btn_h = int(btn_w * 0.5)
      self.game.btn_fist.size = (btn_w, btn_h)
      self.game.btn_fist.pos = (self.ox + self.board_w - btn_w, dp(15))

    if self.game.btn_menu_dots:
      menu_size = int(dp(46))
      self.game.btn_menu_dots.size = (menu_size, menu_size)
      self.game.btn_menu_dots.pos = (self.ox, dp(15))

    if self.game.btn_dollar:
      menu_size = int(dp(46))
      self.game.btn_dollar.size = (menu_size, menu_size)
      self.game.btn_dollar.pos = (self.ox + menu_size + dp(10), dp(15))

      bribe_cost = 200 if self.game.difficulty == 1 else 500
      is_usable = (self.game.coins >= bribe_cost) and (
          not self.game.bribe_active
      )

      if self.game.bribe_active:
        self.game.btn_dollar.set_state_info(
            False, f'${self.game.bribe_time_left}s'
        )
      else:
        self.game.btn_dollar.set_state_info(is_usable, '$')

    if self.game.lbl_stats:
      t = LANGUAGES[self.game.lang]
      is_new_record = (
          self.game.score > self.game.initial_highscore
      ) and (self.game.score > 0)

      if is_new_record:
        score_str = f'[color=33FF33]{self.game.score}[/color]'
        highscore_str = f'[color=33FF33]{self.game.highscore}[/color]'
      else:
        score_str = f'{self.game.score}'
        highscore_str = f'{self.game.highscore}'

      self.game.lbl_stats.text = (
          f"{t['score']}: {score_str}  |  "
          f"{t['highscore']}: {highscore_str}\n"
          f"{t['coins']}: {self.game.coins}  |  "
          f"{t['level']}: {self.game.level}"
      )
      self.game.lbl_stats.pos = (self.ox, self.oy + self.board_h + dp(10))
      self.game.lbl_stats.size = (self.board_w, dp(50))

    with self.canvas:
      Color(0.08, 0.08, 0.08, 1)
      Rectangle(pos=(self.ox, self.oy), size=(self.board_w, self.board_h))

      for y in range(GRID_HEIGHT):
        for x in range(GRID_WIDTH):
          if self.game.grid[y][x]:
            Color(*self.game.grid[y][x])
            Rectangle(
                pos=(
                    self.ox + x * self.block_size + 1,
                    self.oy + y * self.block_size + 1,
                ),
                size=(self.block_size - 2, self.block_size - 2),
            )
          else:
            Color(0.13, 0.13, 0.13, 1)
            Rectangle(
                pos=(
                    self.ox + x * self.block_size + 1,
                    self.oy + y * self.block_size + 1,
                ),
                size=(self.block_size - 2, self.block_size - 2),
            )

      # Тень (ghost piece): показывает, куда упадёт текущая фигура.
      if self.game.current_shape:
        ghost_y = self.game.get_ghost_y()
        if ghost_y != self.game.piece_y:
          gr, gg, gb = self.game.current_color
          Color(gr, gg, gb, 0.28)
          for r, row in enumerate(self.game.current_shape):
            for c, val in enumerate(row):
              if val:
                Rectangle(
                    pos=(
                        self.ox + (self.game.piece_x + c) * self.block_size
                        + 1,
                        self.oy + (ghost_y + r) * self.block_size + 1,
                    ),
                    size=(self.block_size - 2, self.block_size - 2),
                )

      if self.game.current_shape:
        Color(*self.game.current_color)
        for r, row in enumerate(self.game.current_shape):
          for c, val in enumerate(row):
            if val:
              Rectangle(
                  pos=(
                      self.ox
                      + (self.game.piece_x + c) * self.block_size
                      + 1,
                      self.oy
                      + (self.game.piece_y + r) * self.block_size
                      + 1,
                  ),
                  size=(self.block_size - 2, self.block_size - 2),
              )

      px = self.ox + self.board_w - (self.block_size * 3) - dp(5)
      py = self.oy + self.board_h - (self.block_size * 3) - dp(5)
      Color(0.2, 0.2, 0.2, 0.7)
      Rectangle(
          pos=(px, py), size=(self.block_size * 3, self.block_size * 3)
      )

      if self.game.next_shape:
        Color(*self.game.next_color)
        for r, row in enumerate(self.game.next_shape):
          for c, val in enumerate(row):
            if val:
              Rectangle(
                  pos=(
                      px + (c + 0.3) * (self.block_size * 0.7),
                      py + (r + 0.3) * (self.block_size * 0.7),
                  ),
                  size=(
                      (self.block_size * 0.7) - 2,
                      (self.block_size * 0.7) - 2,
                  ),
              )

      if self.game.trump_active:
        tw = self.block_size * 4
        tx = self.game.trump_x
        ty = self.oy + self.board_h / 2

        Color(1, 0.85, 0, 1)
        Ellipse(
            pos=(
                tx - 10,
                ty
                + (
                    tw * 0.1
                    if self.game.trump_state == 'knockout'
                    else tw * 0.3
                ),
            ),
            size=(tw + 20, tw * 0.8),
        )
        Color(1, 0.7, 0.5, 1)
        Ellipse(pos=(tx, ty), size=(tw, tw))
        Color(1, 0.85, 0, 1)
        Triangle(points=[
            tx,
            ty + tw * 0.9,
            tx + tw * 1.2,
            ty + tw * 1.1,
            tx + tw * 0.4,
            ty + tw * 0.6,
        ])

        if self.game.trump_state == 'knockout':
          Color(0, 0, 0, 1)
          Rectangle(
              pos=(tx + tw * 0.2, ty + tw * 0.6), size=(tw * 0.1, tw * 0.03)
          )
          Rectangle(
              pos=(tx + tw * 0.6, ty + tw * 0.6), size=(tw * 0.1, tw * 0.03)
          )
        else:
          Color(1, 1, 1, 1)
          Rectangle(
              pos=(tx + tw * 0.2, ty + tw * 0.6), size=(tw * 0.2, tw * 0.08)
          )
          Rectangle(
              pos=(tx + tw * 0.6, ty + tw * 0.6), size=(tw * 0.2, tw * 0.08)
          )
        Color(0.7, 0.1, 0.1, 1)
        Ellipse(
            pos=(tx + tw * 0.35, ty + tw * 0.2), size=(tw * 0.3, tw * 0.15)
        )

        if self.game.punch_active:
          Color(0.85, 0.65, 0.45, 1)
          f_size = tw * 0.9
          fx = tx + tw - 30
          fy = ty + tw * 0.2
          Ellipse(pos=(fx, fy), size=(f_size, f_size))

          Color(0.95, 0.1, 0.1, 1)
          sx = fx + f_size / 2
          sy = fy + f_size / 2
          s_size = f_size * 0.45
          Triangle(points=[
              sx,
              sy + s_size,
              sx - s_size * 0.4,
              sy - s_size * 0.5,
              sx + s_size * 0.5,
              sy - s_size * 0.2,
          ])
          Triangle(points=[
              sx,
              sy - s_size * 0.8,
              sx - s_size * 0.5,
              sy + s_size * 0.3,
              sx + s_size * 0.3,
              sy + s_size * 0.3,
          ])

      if self.game.state == 'paused':
        Color(0, 0, 0, 0.6)
        Rectangle(pos=(self.ox, self.oy), size=(self.board_w, self.board_h))

  def on_touch_down(self, touch):
    if self.game.state == 'playing':
      if (
          self.game.btn_fist
          and self.game.btn_fist.parent
          and self.game.btn_fist.collide_point(*touch.pos)
      ):
        return False
      if self.game.btn_menu_dots and self.game.btn_menu_dots.collide_point(
          *touch.pos
      ):
        return False
      if self.game.btn_dollar and self.game.btn_dollar.collide_point(
          *touch.pos
      ):
        return False
      self.touch_start_pos = touch.pos
      return True
    return super().on_touch_down(touch)

  def on_touch_up(self, touch):
    if self.game.state == 'playing' and self.touch_start_pos:
      dx = touch.x - self.touch_start_pos[0]
      dy = touch.y - self.touch_start_pos[1]
      self.touch_start_pos = None

      swipe_threshold = dp(30)

      if abs(dx) > abs(dy):
        if dx > swipe_threshold:
          self.game.move_right(None)
        elif dx < -swipe_threshold:
          self.game.move_left(None)
      else:
        if dy > swipe_threshold:
          self.game.rotate_piece(None)
        elif dy < -swipe_threshold:
          self.game.drop_hard()
      return True
    return super().on_touch_up(touch)


class TetrisGame(BoxLayout):

  def __init__(self, **kwargs):
    super().__init__(**kwargs)
    self.orientation = 'vertical'
    self.state = 'menu'
    self.lang = 'RU'
    self.difficulty = 1
    self.grid = [[None for _ in range(GRID_WIDTH)] for _ in range(GRID_HEIGHT)]

    self.store = JsonStore('tetris_save.json')
    self.sound_mgr = SoundManager()
    self.load_data()

    self.score = 0
    self.initial_highscore = 0

    self.level = 1
    self.lines_cleared_total = 0
    self.fall_speed_frames = BASE_FALL_FRAMES

    self.trump_active = False
    self.trump_mode = 'falling'
    self.trump_x = -500
    self.trump_speed = 18
    self.trump_state = 'entering'
    self.punch_active = False

    self.bribe_active = False
    self.bribe_fast_playing = False
    self.bribe_time_left = 0
    self.bribe_timer_event = None

    self.current_shape = None
    self.next_shape = None
    self.piece_x = 0
    self.piece_y = 0
    self.btn_fist = None
    self.btn_menu_dots = None
    self.btn_dollar = None
    self.lbl_stats = None
    self.menu_bg = None
    self._key_bound = False
    self.show_menu()

  def load_data(self):
    try:
      if self.store.exists('game_data'):
        data = self.store.get('game_data')
        self.highscore = data.get('highscore', 0)
        self.coins = data.get('coins', 0)
        self.sound_mgr.enabled = data.get('sound_enabled', True)
        self.difficulty = data.get('difficulty', 1)
      else:
        self.highscore = 0
        self.coins = 0
        self.sound_mgr.enabled = True
        self.difficulty = 1
        self.save_data()
    except (OSError, ValueError, KeyError):
      # Повреждённый файл сохранения — начинаем с чистого состояния,
      # не позволяя игре упасть при старте.
      self.highscore = 0
      self.coins = 0
      self.sound_mgr.enabled = True
      self.difficulty = 1

  def save_data(self):
    try:
      self.store.put(
          'game_data',
          highscore=self.highscore,
          coins=self.coins,
          sound_enabled=self.sound_mgr.enabled,
          difficulty=self.difficulty,
      )
    except OSError:
      pass

  def show_menu(self):
    if self.menu_bg:
      self.menu_bg.stop()
      self.menu_bg = None

    self.clear_widgets()
    self.state = 'menu'
    t = LANGUAGES[self.lang]

    root = RelativeLayout(size_hint=(1, 1))

    gradient = GradientBG(size_hint=(1, 1))
    root.add_widget(gradient)

    self.menu_bg = FallingBlocksBG(size_hint=(1, 1))
    root.add_widget(self.menu_bg)
    self.menu_bg.start()

    menu_layout = BoxLayout(
        orientation='vertical', padding=dp(25), spacing=dp(15),
        size_hint=(1, 1),
    )

    menu_info = (
        f"{t['title']}\n\n{t['highscore']}: {self.highscore}\n{t['coins']}:"
        f' {self.coins}'
    )
    self.logo = Label(
        text=menu_info,
        font_size='24sp',
        halign='center',
        bold=True,
        color=(1, 1, 1, 1),
        size_hint=(1, 0.4),
    )

    self.btn_start = ModernButton(
        base_color=(0.15, 0.75, 0.35, 0.95),
        text=t['play'],
        font_size='22sp',
        size_hint=(1, 0.2),
    )
    self.btn_start.bind(on_press=self.start_game)

    self.btn_settings = ModernButton(
        base_color=(0.2, 0.55, 0.95, 0.95),
        text=t['settings'],
        font_size='20sp',
        size_hint=(1, 0.2),
    )
    self.btn_settings.bind(on_press=self.open_settings_popup)

    self.btn_close = ModernButton(
        base_color=(0.85, 0.25, 0.25, 0.95),
        text=t['close_app'],
        font_size='18sp',
        size_hint=(1, 0.18),
    )
    self.btn_close.bind(on_press=self.close_app)

    menu_layout.add_widget(self.logo)
    menu_layout.add_widget(self.btn_start)
    menu_layout.add_widget(self.btn_settings)
    menu_layout.add_widget(self.btn_close)

    root.add_widget(menu_layout)
    self.add_widget(root)

  def open_settings_popup(self, instance):
    t = LANGUAGES[self.lang]
    content = BoxLayout(
        orientation='vertical', padding=dp(15), spacing=dp(10)
    )

    lang_label = Label(
        text='LANGUAGE / ЯЗЫК',
        font_size='14sp',
        bold=True,
        size_hint=(1, None),
        height=dp(22),
        color=(0.8, 0.8, 0.8, 1),
    )
    lang_bar = BoxLayout(
        orientation='horizontal',
        size_hint=(1, None),
        height=dp(40),
        spacing=dp(8),
    )

    btn_ru = Button(
        text='RU',
        font_size='15sp',
        bold=True,
        background_color=(0.2, 0.6, 1, 1)
        if self.lang == 'RU'
        else (0.3, 0.3, 0.3, 1),
    )
    btn_en = Button(
        text='EN',
        font_size='15sp',
        bold=True,
        background_color=(0.2, 0.6, 1, 1)
        if self.lang == 'EN'
        else (0.3, 0.3, 0.3, 1),
    )

    lang_bar.add_widget(btn_ru)
    lang_bar.add_widget(btn_en)

    sound_txt = t['sound_on'] if self.sound_mgr.enabled else t['sound_off']
    btn_sound = Button(
        text=sound_txt,
        font_size='15sp',
        bold=True,
        size_hint=(1, None),
        height=dp(40),
        background_color=(0.3, 0.8, 0.3, 1)
        if self.sound_mgr.enabled
        else (0.5, 0.5, 0.5, 1),
    )

    def toggle_sound(inst):
      self.sound_mgr.enabled = not self.sound_mgr.enabled
      self.save_data()
      btn_sound.text = (
          t['sound_on'] if self.sound_mgr.enabled else t['sound_off']
      )
      btn_sound.background_color = (
          (0.3, 0.8, 0.3, 1)
          if self.sound_mgr.enabled
          else (0.5, 0.5, 0.5, 1)
      )

    btn_sound.bind(on_press=toggle_sound)

    diff_label = Label(
        text=t['diff_title'],
        font_size='14sp',
        bold=True,
        size_hint=(1, None),
        height=dp(22),
        color=(0.8, 0.8, 0.8, 1),
    )

    diff_text = t['diff_1'] if self.difficulty == 1 else t['diff_2']
    diff_bg = (
        (0.2, 0.7, 0.3, 1) if self.difficulty == 1 else (0.9, 0.3, 0.2, 1)
    )

    btn_diff = Button(
        text=diff_text,
        font_size='15sp',
        bold=True,
        size_hint=(1, None),
        height=dp(40),
        background_color=diff_bg,
    )

    def toggle_diff(inst):
      self.difficulty = 2 if self.difficulty == 1 else 1
      self.save_data()
      btn_diff.text = t['diff_1'] if self.difficulty == 1 else t['diff_2']
      btn_diff.background_color = (
          (0.2, 0.7, 0.3, 1) if self.difficulty == 1 else (0.9, 0.3, 0.2, 1)
      )

    btn_diff.bind(on_press=toggle_diff)

    instr_title = Label(
        text=t['instruction_title'],
        font_size='15sp',
        bold=True,
        size_hint=(1, None),
        height=dp(25),
        color=(1, 0.8, 0.2, 1),
    )

    scroll = ScrollView(size_hint=(1, 1), do_scroll_x=False)
    instr_text = Label(
        text=t['instructions'],
        font_size='13sp',
        halign='left',
        valign='top',
        size_hint_y=None,
        color=(0.9, 0.9, 0.9, 1),
    )
    instr_text.bind(
        width=lambda *x: setattr(
            instr_text, 'text_size', (instr_text.width, None)
        )
    )
    instr_text.bind(
        texture_size=lambda *x: setattr(
            instr_text, 'height', instr_text.texture_size[1]
        )
    )
    scroll.add_widget(instr_text)

    btn_close_popup = Button(
        text=t['close'],
        font_size='16sp',
        bold=True,
        size_hint=(1, None),
        height=dp(42),
        background_color=(0.8, 0.2, 0.2, 1),
    )

    popup = Popup(
        title=t['settings_title'],
        content=content,
        size_hint=(0.92, 0.85),
        auto_dismiss=True,
    )

    def switch_lang(new_lang):
      self.lang = new_lang
      popup.dismiss()
      self.show_menu()
      self.open_settings_popup(None)

    btn_ru.bind(on_press=lambda inst: switch_lang('RU'))
    btn_en.bind(on_press=lambda inst: switch_lang('EN'))
    btn_close_popup.bind(on_press=popup.dismiss)

    content.add_widget(lang_label)
    content.add_widget(lang_bar)
    content.add_widget(btn_sound)
    content.add_widget(diff_label)
    content.add_widget(btn_diff)
    content.add_widget(instr_title)
    content.add_widget(scroll)
    content.add_widget(btn_close_popup)

    popup.open()

  def close_app(self, instance):
    if self.menu_bg:
      self.menu_bg.stop()
    self.sound_mgr.stop_all()
    App.get_running_app().stop()

  def start_game(self, instance):
    # Снимаем предыдущий игровой цикл, обработчик клавиатуры и анимацию
    # меню перед стартом — иначе при рестарте они накапливаются.
    Clock.unschedule(self.update)
    if self._key_bound:
      Window.unbind(on_key_down=self.on_key_down)
      self._key_bound = False
    if self.menu_bg:
      self.menu_bg.stop()
      self.menu_bg = None

    self.clear_widgets()
    self.state = 'playing'
    self.grid = [[None for _ in range(GRID_WIDTH)] for _ in range(GRID_HEIGHT)]
    self.trump_active = False
    self.punch_active = False

    self.stop_bribe()

    self.score = 0
    self.level = 1
    self.lines_cleared_total = 0
    self.fall_speed_frames = BASE_FALL_FRAMES
    self.load_data()
    self.initial_highscore = self.highscore

    self.game_container = RelativeLayout(size_hint=(1, 1))

    self.board = TetrisBoard(self, size_hint=(1, 1))
    self.game_container.add_widget(self.board)

    self.lbl_stats = Label(
        text='',
        font_size='16sp',
        bold=True,
        color=(1, 1, 1, 1),
        size_hint=(None, None),
        halign='center',
        markup=True,
    )
    self.game_container.add_widget(self.lbl_stats)

    self.btn_menu_dots = StylishMenuButton(size_hint=(None, None))
    self.btn_menu_dots.bind(on_press=self.open_pause_popup)
    self.game_container.add_widget(self.btn_menu_dots)

    self.btn_dollar = DollarButton(size_hint=(None, None))
    self.btn_dollar.bind(on_press=self.buy_bribe)
    self.game_container.add_widget(self.btn_dollar)

    self.btn_fist = FistButton(size_hint=(None, None))
    self.btn_fist.text = 'УДАР!' if self.lang == 'RU' else 'PUNCH!'
    self.btn_fist.bind(on_press=self.do_punch)

    self.add_widget(self.game_container)
    Window.bind(on_key_down=self.on_key_down)
    self._key_bound = True

    self.next_shape = random.choice(SHAPES)
    self.next_color = random.choice(COLORS)
    self.spawn_piece()

    Clock.schedule_interval(self.update, 0.03)
    self.fall_buffer = 0

  def buy_bribe(self, instance):
    bribe_cost = 200 if self.difficulty == 1 else 500

    if self.coins >= bribe_cost and not self.bribe_active:
      self.coins -= bribe_cost
      self.save_data()
      self.bribe_active = True

      self.bribe_time_left = 30 if self.difficulty == 1 else 15
      self.bribe_fast_playing = False

      self.sound_mgr.play('bribe_bg', loop=True)

      if self.trump_active:
        self.trump_state = 'leaving'
        if self.btn_fist and self.btn_fist.parent:
          self.game_container.remove_widget(self.btn_fist)

      self.bribe_timer_event = Clock.schedule_interval(
          self.update_bribe_timer, 1.0
      )
      self.board.draw_board()

  def update_bribe_timer(self, dt):
    if self.state == 'playing':
      self.bribe_time_left -= 1

      threshold = 10 if self.difficulty == 1 else 5
      if self.bribe_time_left <= threshold and not self.bribe_fast_playing:
        self.bribe_fast_playing = True
        self.sound_mgr.stop('bribe_bg')
        self.sound_mgr.play('bribe_bg_fast', loop=True)

      if self.bribe_time_left <= 0:
        self.stop_bribe()

      self.board.draw_board()

  def stop_bribe(self):
    self.bribe_active = False
    self.bribe_fast_playing = False
    self.sound_mgr.stop('bribe_bg')
    self.sound_mgr.stop('bribe_bg_fast')
    if self.bribe_timer_event:
      self.bribe_timer_event.cancel()
      self.bribe_timer_event = None

  def open_pause_popup(self, instance):
    if self.state == 'playing':
      self.state = 'paused'
      self.board.draw_board()

    t = LANGUAGES[self.lang]
    content = BoxLayout(orientation='vertical', padding=dp(10), spacing=dp(10))

    btn_resume = Button(
        text=t['resume'],
        font_size='18sp',
        bold=True,
        background_color=(0.2, 0.6, 1, 1),
    )
    btn_restart = Button(
        text=t['restart'],
        font_size='18sp',
        bold=True,
        background_color=(0.8, 0.6, 0.2, 1),
    )
    btn_exit = Button(
        text=t['exit'],
        font_size='18sp',
        bold=True,
        background_color=(0.8, 0.2, 0.2, 1),
    )

    popup = Popup(
        title=t['menu_title'],
        content=content,
        size_hint=(0.8, 0.4),
        auto_dismiss=False,
    )

    def resume_game(inst):
      popup.dismiss()
      self.state = 'playing'
      self.board.draw_board()

    def restart_game(inst):
      popup.dismiss()
      self.start_game(None)

    def exit_game(inst):
      popup.dismiss()
      self.exit_to_menu(None)

    btn_resume.bind(on_press=resume_game)
    btn_restart.bind(on_press=restart_game)
    btn_exit.bind(on_press=exit_game)

    content.add_widget(btn_resume)
    content.add_widget(btn_restart)
    content.add_widget(btn_exit)

    popup.open()

  def exit_to_menu(self, instance):
    Clock.unschedule(self.update)
    if self._key_bound:
      Window.unbind(on_key_down=self.on_key_down)
      self._key_bound = False
    self.stop_bribe()
    self.state = 'menu'
    self.save_data()
    self.show_menu()

  def spawn_piece(self):
    self.current_shape = self.next_shape
    self.current_color = self.next_color
    self.next_shape = random.choice(SHAPES)
    self.next_color = random.choice(COLORS)

    self.piece_x = GRID_WIDTH // 2 - len(self.current_shape[0]) // 2
    self.piece_y = GRID_HEIGHT - len(self.current_shape)

    if self.check_collision(0, 0):
      self.sound_mgr.play('gameover')
      self.exit_to_menu(None)
      return

    if (
        not self.trump_active
        and not self.bribe_active
        and self.current_shape in [SHAPES[0], SHAPES[1]]
    ):
      if random.random() < 0.5:
        self.trump_active = True
        self.trump_mode = 'falling'
        self.trump_x = -300
        self.trump_state = 'entering'
        if self.btn_fist and not self.btn_fist.parent:
          self.game_container.add_widget(self.btn_fist)

  def do_punch(self, instance):
    if self.trump_active and self.trump_state == 'entering':
      self.sound_mgr.play('punch')
      self.punch_active = True
      self.trump_state = 'knockout'
      self.trump_speed = 25
      if self.btn_fist.parent:
        self.game_container.remove_widget(self.btn_fist)
      Clock.schedule_once(self.disable_punch, 0.2)

  def disable_punch(self, dt):
    self.punch_active = False

  def steal_grid_blocks(self):
    target_colors = COLORS[3:7]
    matching_cells = [
        (y, x)
        for y in range(GRID_HEIGHT)
        for x in range(GRID_WIDTH)
        if self.grid[y][x] in target_colors
    ]

    if matching_cells:
      target_cell = random.choice(matching_cells)
      chosen_color = self.grid[target_cell[0]][target_cell[1]]

      same_color_cells = [
          (y, x)
          for (y, x) in matching_cells
          if self.grid[y][x] == chosen_color
      ]
      blocks_to_steal = same_color_cells[:4]

      for y, x in blocks_to_steal:
        self.grid[y][x] = None

  def update(self, dt):
    if self.state != 'playing':
      return True

    if self.trump_active:
      if self.trump_state == 'entering':
        self.trump_x += self.trump_speed
        if self.trump_x >= self.board.ox + dp(20):
          self.trump_state = 'stealing'
      elif self.trump_state == 'stealing':
        self.sound_mgr.play('laugh')

        if self.trump_mode == 'falling':
          self.current_shape = random.choice(SHAPES[2:])
          self.current_color = random.choice(COLORS[2:])
          self.piece_x = max(
              0,
              min(
                  GRID_WIDTH - len(self.current_shape[0]),
                  GRID_WIDTH // 2 - len(self.current_shape[0]) // 2,
              ),
          )
        elif self.trump_mode == 'grid':
          self.steal_grid_blocks()

        self.trump_state = 'leaving'
        if self.btn_fist.parent:
          self.game_container.remove_widget(self.btn_fist)
      elif self.trump_state in ['leaving', 'knockout']:
        self.trump_x -= self.trump_speed
        if self.trump_x <= -500:
          self.trump_active = False

    self.fall_buffer += 1
    if self.fall_buffer >= self.fall_speed_frames:
      self.fall_buffer = 0
      if not self.check_collision(0, -1):
        self.piece_y -= 1
      else:
        self.lock_piece()

    self.board.draw_board()

  def check_collision(self, dx, dy, shape=None):
    if shape is None:
      shape = self.current_shape
    for r, row in enumerate(shape):
      for c, val in enumerate(row):
        if val:
          nx, ny = self.piece_x + c + dx, self.piece_y + r + dy
          if nx < 0 or nx >= GRID_WIDTH or ny < 0:
            return True
          if ny < GRID_HEIGHT and self.grid[ny][nx]:
            return True
    return False

  def get_ghost_y(self):
    """Returns the y-coordinate the current piece would land at.

    Walks the piece down (without moving it) using the same collision
    rules as normal movement, stopping one step above the first
    collision — used to render the semi-transparent ghost/shadow piece.
    """
    if self.current_shape is None:
      return self.piece_y
    offset = 0
    while not self.check_collision(0, offset - 1):
      offset -= 1
    return self.piece_y + offset

  def lock_piece(self):
    for r, row in enumerate(self.current_shape):
      for c, val in enumerate(row):
        if val:
          py = self.piece_y + r
          px = self.piece_x + c
          if 0 <= py < GRID_HEIGHT and 0 <= px < GRID_WIDTH:
            self.grid[py][px] = self.current_color
    self.clear_rows()

    if (
        self.difficulty == 2
        and not self.trump_active
        and not self.bribe_active
        and random.random() < 0.35
    ):
      target_colors = COLORS[3:7]
      grid_has_targets = any(
          self.grid[y][x] in target_colors
          for y in range(GRID_HEIGHT)
          for x in range(GRID_WIDTH)
      )
      if grid_has_targets:
        self.trump_active = True
        self.trump_mode = 'grid'
        self.trump_x = -300
        self.trump_state = 'entering'
        if self.btn_fist and not self.btn_fist.parent:
          self.game_container.add_widget(self.btn_fist)

    self.spawn_piece()

  def clear_rows(self):
    cleared_rows = [row for row in self.grid if any(x is None for x in row)]
    lines_count = GRID_HEIGHT - len(cleared_rows)

    if lines_count > 0:
      self.sound_mgr.play('clear')
      score_rewards = {1: 100, 2: 300, 3: 700, 4: 1500}
      self.score += score_rewards.get(lines_count, 1500) * self.level

      self.lines_cleared_total += lines_count
      new_level = 1 + self.lines_cleared_total // LEVEL_LINES_PER_UP
      if new_level > self.level:
        self.level = new_level
        self.fall_speed_frames = max(
            MIN_FALL_FRAMES, BASE_FALL_FRAMES - (self.level - 1)
        )
        self.sound_mgr.play('levelup')

      if self.score > self.highscore:
        self.highscore = self.score

      self.coins += lines_count * 10
      self.save_data()

      self.grid = cleared_rows
      while len(self.grid) < GRID_HEIGHT:
        self.grid.append([None for _ in range(GRID_WIDTH)])

  def move_left(self, instance):
    if self.state == 'playing' and not self.check_collision(-1, 0):
      self.piece_x -= 1
      self.sound_mgr.play('move')
    self.board.draw_board()

  def move_right(self, instance):
    if self.state == 'playing' and not self.check_collision(1, 0):
      self.piece_x += 1
      self.sound_mgr.play('move')
    self.board.draw_board()

  def drop_hard(self):
    if self.state == 'playing':
      start_y = self.piece_y
      while not self.check_collision(0, -1):
        self.piece_y -= 1
      # Бонус за жёсткий сброс: 2 очка за каждую клетку пройденной высоты.
      dropped_cells = start_y - self.piece_y
      if dropped_cells > 0:
        self.score += dropped_cells * 2
      self.sound_mgr.play('drop')
      self.lock_piece()
      self.board.draw_board()

  def rotate_piece(self, instance=None):
    if self.state == 'playing':
      rotated = [list(r) for r in zip(*self.current_shape[::-1])]
      if not self.check_collision(0, 0, rotated):
        self.current_shape = rotated
        self.sound_mgr.play('rotate')
      self.board.draw_board()

  def on_key_down(self, window, key, scancode, codepoint, modifiers):
    if self.state == 'playing':
      if key == 276:
        self.move_left(None)
      elif key == 275:
        self.move_right(None)
      elif key == 274:
        self.drop_hard()
      elif key == 273:
        self.rotate_piece(None)


class TetrisApp(App):

  def build(self):
    return TetrisGame()


if __name__ == '__main__':
  TetrisApp().run()
