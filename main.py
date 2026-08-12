
import os
from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.relativelayout import RelativeLayout
from kivy.uix.widget import Widget
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.popup import Popup
from kivy.uix.scrollview import ScrollView
from kivy.graphics import Color, Rectangle, Ellipse, Triangle, RoundedRectangle, Line
from kivy.clock import Clock
from kivy.core.window import Window
from kivy.metrics import dp
from kivy.storage.jsonstore import JsonStore

GRID_WIDTH = 10
GRID_HEIGHT = 20

SHAPES = [
    [[1, 1, 1, 1]],  # I
    [[1, 1], [1, 1]],  # O
    [[1, 1, 1], [0, 1, 0]],  # T
    [[1, 1, 0], [0, 1, 1]],  # Z
    [[0, 1, 1], [1, 1, 0]],  # S
    [[1, 1, 1], [1, 0, 0]],  # J
    [[1, 1, 1], [0, 0, 1]]   # L
]

COLORS = [
    (0, 1, 1), (1, 1, 0), (0.5, 0, 0.5),
    (1, 0, 0), (0, 1, 0), (0, 0, 1), (1, 0.5, 0)
]

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
        'instruction_title': 'КАК ИГРАТЬ:',
        'instructions': (
            "• Свайп Влево / Вправо — передвижение фигуры\n"
            "• Свайп Вверх — повернуть фигуру\n"
            "• Свайп Вниз — быстро сбросить вниз\n\n"
            "ОСОБЕННОСТЬ (ВОР И ФЛАГ):\n"
            "Иногда на поле прибегает воришка, чтобы утащить ценную фигуру!\n\n"
            "КАК ЗАЩИТИТЬСЯ:\n"
            "Как только появляется воришка, снизу вылетает КНОПКА-ФЛАГ.\n"
            "Жми на нее быстро, чтобы спасти свою фигуру!"
        )
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
        'instruction_title': 'HOW TO PLAY:',
        'instructions': (
            "• Swipe Left / Right — move piece\n"
            "• Swipe Up — rotate piece\n"
            "• Swipe Down — hard drop\n\n"
            "SPECIAL FEATURE (THIEF & FLAG):\n"
            "Sometimes a thief runs in to steal a valuable piece!\n\n"
            "HOW TO DEFEND:\n"
            "As soon as the thief appears, a FLAG BUTTON appears below.\n"
            "Tap it quickly to save your piece!"
        )
    }
}


class StylishMenuButton(Button):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.background_color = (0, 0, 0, 0)
        self.text = ''
        self.bind(pos=self.update_canvas, size=self.update_canvas, state=self.update_canvas)

    def update_canvas(self, *args):
        self.canvas.before.clear()
        self.canvas.after.clear()
        
        with self.canvas.before:
            Color(0, 0, 0, 0.35)
            RoundedRectangle(pos=(self.x + dp(2), self.y - dp(2)), size=self.size, radius=[dp(12)])
            
            if self.state == 'down':
                Color(0.2, 0.5, 0.9, 0.95)
            else:
                Color(0.12, 0.12, 0.16, 0.85)
            RoundedRectangle(pos=self.pos, size=self.size, radius=[dp(12)])
            
            Color(0.3, 0.5, 0.9, 0.5)
            Line(rounded_rectangle=(self.x, self.y, self.width, self.height, dp(12)), width=dp(1.2))

        with self.canvas.after:
            Color(1, 1, 1, 0.9)
            pad_x = self.width * 0.28
            start_x = self.x + pad_x
            end_x = self.x + self.width - pad_x
            
            h = self.height
            line_w = dp(2)
            
            Line(points=[start_x, self.y + h * 0.68, end_x, self.y + h * 0.68], width=line_w)
            Line(points=[start_x, self.y + h * 0.50, end_x, self.y + h * 0.50], width=line_w)
            Line(points=[start_x, self.y + h * 0.32, end_x, self.y + h * 0.32], width=line_w)


class RussianFlagButton(Button):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.background_color = (0, 0, 0, 0)
        self.text = ''
        self.bind(pos=self.update_canvas, size=self.update_canvas, state=self.update_canvas)

    def update_canvas(self, *args):
        self.canvas.before.clear()
        if self.width <= 0 or self.height <= 0:
            return

        with self.canvas.before:
            Color(0, 0, 0, 0.4)
            RoundedRectangle(pos=(self.x + dp(3), self.y - dp(3)), size=self.size, radius=[dp(16)])

            stripe_h = self.height / 3.0
            r = dp(16)
            alpha_mod = 0.7 if self.state == 'down' else 1.0

            Color(0.95 * alpha_mod, 0.95 * alpha_mod, 0.95 * alpha_mod, 0.95)
            RoundedRectangle(pos=(self.x, self.y + stripe_h * 2), size=(self.width, stripe_h), radius=[(r, r), (r, r), (0, 0), (0, 0)])

            Color(0.0 * alpha_mod, 0.22 * alpha_mod, 0.66 * alpha_mod, 0.95)
            Rectangle(pos=(self.x, self.y + stripe_h), size=(self.width, stripe_h))

            Color(0.85 * alpha_mod, 0.1 * alpha_mod, 0.1 * alpha_mod, 0.95)
            RoundedRectangle(pos=(self.x, self.y), size=(self.width, stripe_h), radius=[(0, 0), (0, 0), (r, r), (r, r)])

            Color(1, 1, 1, 0.8)
            Line(rounded_rectangle=(self.x, self.y, self.width, self.height, r), width=dp(2))


class TetrisBoard(Widget):
    def __init__(self, game_ref, **kwargs):
        super().__init__(**kwargs)
        self.game = game_ref
        self.touch_start_pos = None
        self.bind(size=self.draw_board, pos=self.draw_board)

    def draw_board(self, *args):
        self.canvas.clear()
        if self.width <= 0 or self.height <= 0 or self.game.state not in ['playing', 'paused']:
            return
        
        available_height = self.height - dp(180)
        self.block_size = min(self.width / GRID_WIDTH, available_height / GRID_HEIGHT)
        self.board_w = self.block_size * GRID_WIDTH
        self.board_h = self.block_size * GRID_HEIGHT
        
        self.ox = self.x + (self.width - self.board_w) / 2
        self.oy = self.y + (available_height - self.board_h) / 2 + dp(80)

        if self.game.btn_putin:
            btn_w = int(self.board_w * 0.45)
            btn_h = int(btn_w * 0.6)
            self.game.btn_putin.size = (btn_w, btn_h)
            self.game.btn_putin.pos = (self.ox + self.board_w - btn_w, dp(15))

        if self.game.btn_menu_dots:
            menu_size = int(dp(46))
            self.game.btn_menu_dots.size = (menu_size, menu_size)
            self.game.btn_menu_dots.pos = (self.ox, dp(15))

        # Обновление текста статистики с подсветкой зелёным при превышении рекорда
        if self.game.lbl_stats:
            t = LANGUAGES[self.game.lang]
            
            # Проверяем, побит ли рекорд текущей сессии
            is_new_record = (self.game.score > self.game.initial_highscore) and (self.game.score > 0)
            
            if is_new_record:
                score_str = f"[color=33FF33]{self.game.score}[/color]"
                highscore_str = f"[color=33FF33]{self.game.highscore}[/color]"
            else:
                score_str = f"{self.game.score}"
                highscore_str = f"{self.game.highscore}"

            self.game.lbl_stats.text = (
                f"{t['score']}: {score_str}  |  "
                f"{t['highscore']}: {highscore_str}\n"
                f"{t['coins']}: {self.game.coins}"
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
                        Rectangle(pos=(self.ox + x * self.block_size + 1, self.oy + y * self.block_size + 1), 
                                  size=(self.block_size - 2, self.block_size - 2))
                    else:
                        Color(0.13, 0.13, 0.13, 1)
                        Rectangle(pos=(self.ox + x * self.block_size + 1, self.oy + y * self.block_size + 1), 
                                  size=(self.block_size - 2, self.block_size - 2))
            
            if self.game.current_shape:
                Color(*self.game.current_color)
                for r, row in enumerate(self.game.current_shape):
                    for c, val in enumerate(row):
                        if val:
                            Rectangle(pos=(self.ox + (self.game.piece_x + c) * self.block_size + 1, 
                                           self.oy + (self.game.piece_y + r) * self.block_size + 1), 
                                      size=(self.block_size - 2, self.block_size - 2))

            px = self.ox + self.board_w - (self.block_size * 3) - dp(5)
            py = self.oy + self.board_h - (self.block_size * 3) - dp(5)
            Color(0.2, 0.2, 0.2, 0.7)
            Rectangle(pos=(px, py), size=(self.block_size * 3, self.block_size * 3))
            
            if self.game.next_shape:
                Color(*self.game.next_color)
                for r, row in enumerate(self.game.next_shape):
                    for c, val in enumerate(row):
                        if val:
                            Rectangle(pos=(px + (c + 0.3) * (self.block_size * 0.7), 
                                           py + (r + 0.3) * (self.block_size * 0.7)), 
                                      size=((self.block_size * 0.7) - 2, (self.block_size * 0.7) - 2))
            
            if self.game.trump_active:
                tw = self.block_size * 4  
                tx = self.game.trump_x
                ty = self.oy + self.board_h / 2
                
                Color(1, 0.85, 0, 1)
                Ellipse(pos=(tx - 10, ty + (tw * 0.1 if self.game.trump_state == 'knockout' else tw * 0.3)), size=(tw + 20, tw * 0.8))
                Color(1, 0.7, 0.5, 1)
                Ellipse(pos=(tx, ty), size=(tw, tw))
                Color(1, 0.85, 0, 1)
                Triangle(points=[tx, ty + tw*0.9, tx + tw*1.2, ty + tw*1.1, tx + tw*0.4, ty + tw*0.6])
                
                if self.game.trump_state == 'knockout':
                    Color(0, 0, 0, 1)
                    Rectangle(pos=(tx + tw*0.2, ty + tw*0.6), size=(tw*0.1, tw*0.03))
                    Rectangle(pos=(tx + tw*0.6, ty + tw*0.6), size=(tw*0.1, tw*0.03))
                else:
                    Color(1, 1, 1, 1)
                    Rectangle(pos=(tx + tw*0.2, ty + tw*0.6), size=(tw*0.2, tw*0.08))
                    Rectangle(pos=(tx + tw*0.6, ty + tw*0.6), size=(tw*0.2, tw*0.08))
                Color(0.7, 0.1, 0.1, 1)
                Ellipse(pos=(tx + tw*0.35, ty + tw*0.2), size=(tw*0.3, tw*0.15))

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
                    Triangle(points=[sx, sy + s_size, sx - s_size*0.4, sy - s_size*0.5, sx + s_size*0.5, sy - s_size*0.2])
                    Triangle(points=[sx, sy - s_size*0.8, sx - s_size*0.5, sy + s_size*0.3, sx + s_size*0.5, sy + s_size*0.3])
            
            if self.game.state == 'paused':
                Color(0, 0, 0, 0.6)
                Rectangle(pos=(self.ox, self.oy), size=(self.board_w, self.board_h))

    def on_touch_down(self, touch):
        if self.game.state == 'playing':
            if self.game.btn_putin and self.game.btn_putin.parent and self.game.btn_putin.collide_point(*touch.pos):
                return False
            if self.game.btn_menu_dots and self.game.btn_menu_dots.collide_point(*touch.pos):
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
        self.grid = [[None for _ in range(GRID_WIDTH)] for _ in range(GRID_HEIGHT)]
        
        # Подключаем JsonStore для сохранений
        self.store = JsonStore('tetris_save.json')
        self.load_data()
        
        self.score = 0 
        self.initial_highscore = 0  # Стартовый рекорд перед матчем
        
        self.trump_active = False
        self.trump_x = -500
        self.trump_speed = 18
        self.punch_active = False
        
        self.current_shape = None
        self.next_shape = None
        self.btn_putin = None
        self.btn_menu_dots = None
        self.lbl_stats = None
        self.show_menu()

    def load_data(self):
        """Загрузка рекорда и монет из файла"""
        if self.store.exists('game_data'):
            data = self.store.get('game_data')
            self.highscore = data.get('highscore', 0)
            self.coins = data.get('coins', 0)
        else:
            self.highscore = 0
            self.coins = 0
            self.save_data()

    def save_data(self):
        """Сохранение рекорда и монет в файл"""
        self.store.put('game_data', highscore=self.highscore, coins=self.coins)

    def show_menu(self):
        self.clear_widgets()
        t = LANGUAGES[self.lang]
        menu_layout = BoxLayout(orientation='vertical', padding=dp(20), spacing=dp(15))
        
        menu_info = f"{t['title']}\n\n{t['highscore']}: {self.highscore}\n{t['coins']}: {self.coins}"
        self.logo = Label(text=menu_info, font_size='24sp', halign='center', bold=True, size_hint=(1, 0.4))
        
        self.btn_start = Button(text=t['play'], font_size='26sp', bold=True, size_hint=(1, 0.2), background_color=(0.2, 0.8, 0.2, 1))
        self.btn_start.bind(on_press=self.start_game)

        self.btn_settings = Button(text=t['settings'], font_size='22sp', bold=True, size_hint=(1, 0.2), background_color=(0.2, 0.6, 1, 1))
        self.btn_settings.bind(on_press=self.open_settings_popup)
        
        self.btn_close = Button(text=t['close_app'], font_size='20sp', bold=True, size_hint=(1, 0.2), background_color=(0.8, 0.2, 0.2, 1))
        self.btn_close.bind(on_press=self.close_app)

        menu_layout.add_widget(self.logo)
        menu_layout.add_widget(self.btn_start)
        menu_layout.add_widget(self.btn_settings)
        menu_layout.add_widget(self.btn_close)
        self.add_widget(menu_layout)

    def open_settings_popup(self, instance):
        t = LANGUAGES[self.lang]
        content = BoxLayout(orientation='vertical', padding=dp(15), spacing=dp(10))

        lang_label = Label(text="LANGUAGE / ЯЗЫК", font_size='14sp', bold=True, size_hint=(1, None), height=dp(25), color=(0.8, 0.8, 0.8, 1))
        lang_bar = BoxLayout(orientation='horizontal', size_hint=(1, None), height=dp(42), spacing=dp(8))
        
        btn_ru = Button(text='RU', font_size='15sp', bold=True, background_color=(0.2, 0.6, 1, 1) if self.lang == 'RU' else (0.3, 0.3, 0.3, 1))
        btn_en = Button(text='EN', font_size='15sp', bold=True, background_color=(0.2, 0.6, 1, 1) if self.lang == 'EN' else (0.3, 0.3, 0.3, 1))
        
        lang_bar.add_widget(btn_ru)
        lang_bar.add_widget(btn_en)

        instr_title = Label(text=t['instruction_title'], font_size='16sp', bold=True, size_hint=(1, None), height=dp(30), color=(1, 0.8, 0.2, 1))
        
        scroll = ScrollView(size_hint=(1, 1), do_scroll_x=False)
        instr_text = Label(
            text=t['instructions'], 
            font_size='13sp', 
            halign='left', 
            valign='top', 
            size_hint_y=None,
            color=(0.9, 0.9, 0.9, 1)
        )
        instr_text.bind(width=lambda*x: setattr(instr_text, 'text_size', (instr_text.width, None)))
        instr_text.bind(texture_size=lambda*x: setattr(instr_text, 'height', instr_text.texture_size[1]))
        scroll.add_widget(instr_text)

        btn_close_popup = Button(text=t['close'], font_size='16sp', bold=True, size_hint=(1, None), height=dp(45), background_color=(0.8, 0.2, 0.2, 1))

        popup = Popup(
            title=t['settings_title'], 
            content=content,
            size_hint=(0.92, 0.78), 
            auto_dismiss=True
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
        content.add_widget(instr_title)
        content.add_widget(scroll)
        content.add_widget(btn_close_popup)

        popup.open()

    def close_app(self, instance):
        App.get_running_app().stop()

    def start_game(self, instance):
        self.clear_widgets()
        self.state = 'playing'
        self.grid = [[None for _ in range(GRID_WIDTH)] for _ in range(GRID_HEIGHT)]
        self.trump_active = False
        self.punch_active = False
        self.score = 0
        
        self.load_data()
        self.initial_highscore = self.highscore  # Запоминаем стартовый рекорд
        
        self.game_container = RelativeLayout(size_hint=(1, 1))
        
        self.board = TetrisBoard(self, size_hint=(1, 1))
        self.game_container.add_widget(self.board)
        
        # Разрешаем Kivy Markup для подсветки цифр цветом
        self.lbl_stats = Label(
            text="", 
            font_size='16sp', 
            bold=True, 
            color=(1, 1, 1, 1), 
            size_hint=(None, None), 
            halign='center',
            markup=True
        )
        self.game_container.add_widget(self.lbl_stats)
        
        self.btn_menu_dots = StylishMenuButton(size_hint=(None, None))
        self.btn_menu_dots.bind(on_press=self.open_pause_popup)
        self.game_container.add_widget(self.btn_menu_dots)

        self.btn_putin = RussianFlagButton(size_hint=(None, None))
        self.btn_putin.bind(on_press=self.putin_punch)
        
        self.add_widget(self.game_container)
        Window.bind(on_key_down=self.on_key_down)

        self.next_shape = random.choice(SHAPES)
        self.next_color = random.choice(COLORS)
        self.spawn_piece()
        
        Clock.schedule_interval(self.update, 0.03)
        self.fall_buffer = 0

    def open_pause_popup(self, instance):
        if self.state == 'playing':
            self.state = 'paused'
            self.board.draw_board()

        t = LANGUAGES[self.lang]
        content = BoxLayout(orientation='vertical', padding=dp(10), spacing=dp(10))
        
        btn_resume = Button(text=t['resume'], font_size='18sp', bold=True, background_color=(0.2, 0.6, 1, 1))
        btn_restart = Button(text=t['restart'], font_size='18sp', bold=True, background_color=(0.8, 0.6, 0.2, 1))
        btn_exit = Button(text=t['exit'], font_size='18sp', bold=True, background_color=(0.8, 0.2, 0.2, 1))

        popup = Popup(
            title=t['menu_title'], content=content,
            size_hint=(0.8, 0.4), auto_dismiss=False
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
            self.exit_to_menu(None)

        if not self.trump_active and self.current_shape in [SHAPES[0], SHAPES[1]]:
            if random.random() < 0.6:  
                self.trump_active = True
                self.trump_x = -300  
                self.trump_state = 'entering'
                if not self.btn_putin.parent:
                    self.game_container.add_widget(self.btn_putin)

    def putin_punch(self, instance):
        if self.trump_active and self.trump_state == 'entering':
            self.punch_active = True
            self.trump_state = 'knockout'
            self.trump_speed = 25 
            if self.btn_putin.parent:
                self.game_container.remove_widget(self.btn_putin)
            Clock.schedule_once(self.disable_punch, 0.2)

    def disable_punch(self, dt):
        self.punch_active = False

    def update(self, dt):
        if self.state != 'playing':
            return True
        
        if self.trump_active:
            if self.trump_state == 'entering':
                self.trump_x += self.trump_speed
                if self.trump_x >= self.board.ox + dp(20):
                    self.trump_state = 'stealing'
            elif self.trump_state == 'stealing':
                self.current_shape = random.choice(SHAPES[2:])
                self.current_color = random.choice(COLORS[2:])
                self.piece_x = GRID_WIDTH // 2 - len(self.current_shape[0]) // 2
                self.trump_state = 'leaving'
                if self.btn_putin.parent:
                    self.game_container.remove_widget(self.btn_putin)
            elif self.trump_state == 'leaving' or self.trump_state == 'knockout':
                self.trump_x -= self.trump_speed
                if self.trump_x <= -500:
                    self.trump_active = False

        self.fall_buffer += 1
        if self.fall_buffer >= 15:
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

    def lock_piece(self):
        for r, row in enumerate(self.current_shape):
            for c, val in enumerate(row):
                if val:
                    self.grid[self.piece_y + r][self.piece_x + c] = self.current_color
        self.clear_rows()
        self.spawn_piece()

    def clear_rows(self):
        cleared_rows = [row for row in self.grid if any(x is None for x in row)]
        lines_count = GRID_HEIGHT - len(cleared_rows)
        
        if lines_count > 0:
            score_rewards = {1: 100, 2: 300, 3: 700, 4: 1500}
            self.score += score_rewards.get(lines_count, 1500)
            
            # Обновляем рекорд
            if self.score > self.highscore:
                self.highscore = self.score
            
            self.coins += lines_count * 10
            self.save_data()
            
            self.grid = cleared_rows
            while len(self.grid) < GRID_HEIGHT:
                self.grid.append([None for _ in range(GRID_WIDTH)])

    def move_left(self, instance):
        if self.state == 'playing' and not self.check_collision(-1, 0): self.piece_x -= 1
        self.board.draw_board()

    def move_right(self, instance):
        if self.state == 'playing' and not self.check_collision(1, 0): self.piece_x += 1
        self.board.draw_board()

    def move_down(self, instance):
        if self.state == 'playing':
            if not self.check_collision(0, -1):
                self.piece_y -= 1
            else:
                self.lock_piece()
            self.board.draw_board()

    def drop_hard(self):
        if self.state == 'playing':
            while not self.check_collision(0, -1):
                self.piece_y -= 1
            self.lock_piece()
            self.board.draw_board()

    def rotate_piece(self, instance=None):
        if self.state == 'playing':
            rotated = list(zip(*self.current_shape[::-1]))
            if not self.check_collision(0, 0, rotated):
                self.current_shape = rotated
            self.board.draw_board()

    def on_key_down(self, window, key, scancode, codepoint, modifiers):
        if self.state == 'playing':
            if key == 276: self.move_left(None)
            elif key == 275: self.move_right(None)
            elif key == 274: self.drop_hard()
            elif key == 273: self.rotate_piece(None)


class TetrisApp(App):
    def build(self):
        return TetrisGame()


if __name__ == '__main__':
    TetrisApp().run()
