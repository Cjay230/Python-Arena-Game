
import os
import sys
import json
import subprocess
import runpy
import builtins
import pygame

pygame.init()

FPS = 60
TITLE = "The Lebanese Arena - Choose Snake"
ASSET_BG = "lobbybackground.png"

DISPLAY_INFO = pygame.display.Info()
WIDTH = max(1100, int(DISPLAY_INFO.current_w * 0.90))
HEIGHT = max(700, int(DISPLAY_INFO.current_h * 0.86))
SCREEN = pygame.display.set_mode((WIDTH, HEIGHT), pygame.RESIZABLE)
pygame.display.set_caption(TITLE)
CLOCK = pygame.time.Clock()

# =========================
# BACKGROUND MUSIC
# =========================
def start_background_music():
    try:
        if not pygame.mixer.get_init():
            pygame.mixer.init()
        music_path = os.path.join("music", "music.mp3")
        if not os.path.exists(music_path):
            music_path = os.path.join("music", "game_music.mp3")
        if os.path.exists(music_path):
            pygame.mixer.music.load(music_path)
            pygame.mixer.music.set_volume(0.25)
            pygame.mixer.music.play(-1)
    except Exception:
        pass


WHITE = (250, 240, 214)
SOFT_WHITE = (244, 232, 200)
TEXT_MAIN = (106, 81, 58)
TEXT_SOFT = (125, 98, 72)
TITLE_SHADOW = (155, 124, 96)
PANEL = (248, 242, 233)
PANEL_BORDER = (218, 186, 132)
CARD_FILL = (245, 239, 229)
CARD_FILL_SELECTED = (247, 241, 232)
CARD_BORDER = (216, 190, 145)
CARD_SELECTED_TINT = (236, 215, 178, 70)
GREEN = (126, 152, 80)
GREEN_DARK = (89, 111, 56)
GREEN_LIGHT = (160, 184, 112)
BROWN = (116, 63, 36)
BROWN_DARK = (82, 42, 23)
BROWN_LIGHT = (141, 85, 52)
OVERLAY_TOP = (255, 247, 220, 60)
OVERLAY_BOTTOM = (60, 42, 25, 45)
INPUT_FILL = (241, 233, 219)
INPUT_BORDER = (214, 188, 145)
INPUT_ACTIVE = (180, 142, 92)
ERROR_RED = (140, 50, 44)
SUCCESS_GREEN = (82, 112, 59)

SETUP_FILE = "player_setup.json"
ARENA_FILE = "selected_arena.txt"
ARENA_SETUP_FILE = "arena_setup.py"
GAME_FILE = "game.py"

SNAKE_COLORS = {
    "Cedar Green": {"head": [94, 132, 74], "body": [132, 168, 103]},
    "Mediterranean Blue": {"head": [72, 114, 152], "body": [105, 150, 191]},
    "Sunset Gold": {"head": [171, 121, 51], "body": [208, 158, 88]},
    "Berry Rose": {"head": [150, 83, 94], "body": [190, 120, 131]},
}


def load_image(path, size=None, alpha=True):
    if not os.path.exists(path):
        raise FileNotFoundError(f"Missing asset: {path}")
    img = pygame.image.load(path)
    img = img.convert_alpha() if alpha else img.convert()
    if size:
        img = pygame.transform.smoothscale(img, size)
    return img


def scale_image_to_cover(img, target_size, vertical_focus=0.3):
    target_w, target_h = target_size
    src_w, src_h = img.get_size()
    scale = max(target_w / src_w, target_h / src_h)
    new_w = int(src_w * scale)
    new_h = int(src_h * scale)
    scaled = pygame.transform.smoothscale(img, (new_w, new_h))
    max_x = max(0, new_w - target_w)
    max_y = max(0, new_h - target_h)
    x = max_x // 2
    y = int(max_y * vertical_focus)
    y = max(0, min(y, max_y))
    return scaled.subsurface((x, y, target_w, target_h)).copy()


def get_font(size, bold=False, italic=False, path=None):
    if path and os.path.exists(path):
        return pygame.font.Font(path, size)
    preferred = ["Georgia", "Times New Roman", "Garamond", "Palatino Linotype"]
    for name in preferred:
        font = pygame.font.SysFont(name, size, bold=bold, italic=italic)
        if font:
            return font
    return pygame.font.SysFont("serif", size, bold=bold, italic=italic)


def draw_text(surface, text, font, color, pos, center=False,
              shadow=True, shadow_offset=(0, 4), shadow_alpha=100, shadow_color=(35, 23, 14)):
    text_surf = font.render(text, True, color)
    rect = text_surf.get_rect()
    if center:
        rect.center = pos
    else:
        rect.topleft = pos

    if shadow:
        shadow_surf = font.render(text, True, shadow_color)
        shadow_surf.set_alpha(shadow_alpha)
        shadow_rect = shadow_surf.get_rect()
        if center:
            shadow_rect.center = (rect.centerx + shadow_offset[0], rect.centery + shadow_offset[1])
        else:
            shadow_rect.topleft = (rect.x + shadow_offset[0], rect.y + shadow_offset[1])
        surface.blit(shadow_surf, shadow_rect)

    surface.blit(text_surf, rect)
    return rect


def rounded_panel(size, fill, border, radius=24, border_width=3, alpha=200):
    surf = pygame.Surface(size, pygame.SRCALPHA)
    rect = pygame.Rect(0, 0, *size)
    pygame.draw.rect(surf, (*fill, alpha), rect, border_radius=radius)
    pygame.draw.rect(surf, border, rect, width=border_width, border_radius=radius)
    return surf


def draw_soft_shadow(surface, rect, radius=26, alpha=45, offset=(0, 12)):
    shadow_surf = pygame.Surface((rect.width + radius * 2, rect.height + radius * 2), pygame.SRCALPHA)
    shadow_rect = pygame.Rect(radius, radius, rect.width, rect.height)
    pygame.draw.rect(shadow_surf, (0, 0, 0, alpha), shadow_rect, border_radius=24)
    surface.blit(shadow_surf, (rect.x - radius + offset[0], rect.y - radius + offset[1]))


def draw_vertical_overlay(surface, top_rgba, bottom_rgba):
    width, height = surface.get_size()
    overlay = pygame.Surface((width, height), pygame.SRCALPHA)
    for y in range(height):
        t = y / max(height - 1, 1)
        r = int(top_rgba[0] * (1 - t) + bottom_rgba[0] * t)
        g = int(top_rgba[1] * (1 - t) + bottom_rgba[1] * t)
        b = int(top_rgba[2] * (1 - t) + bottom_rgba[2] * t)
        a = int(top_rgba[3] * (1 - t) + bottom_rgba[3] * t)
        pygame.draw.line(overlay, (r, g, b, a), (0, y), (width, y))
    surface.blit(overlay, (0, 0))


def create_button_surface(size, base, dark, light, border=(215, 192, 152), pressed=False):
    surf = pygame.Surface(size, pygame.SRCALPHA)
    rect = pygame.Rect(0, 0, *size)
    pygame.draw.rect(surf, dark, rect, border_radius=12)
    inner = rect.inflate(-4, -4)
    pygame.draw.rect(surf, base, inner, border_radius=10)
    gloss_h = max(10, inner.height // 3)
    gloss = pygame.Rect(inner.x + 6, inner.y + 5, inner.width - 12, gloss_h)
    gloss_layer = pygame.Surface(size, pygame.SRCALPHA)
    pygame.draw.rect(gloss_layer, (*light, 40 if not pressed else 18), gloss, border_radius=8)
    surf.blit(gloss_layer, (0, 0))
    pygame.draw.rect(surf, border, inner, width=2, border_radius=10)
    return surf


def launch_file(filename, *args):
    target_path = os.path.join(os.path.dirname(__file__), filename)
    sys.argv = [target_path] + [str(arg) for arg in args]
    runpy.run_path(target_path, run_name="__main__")
    sys.exit()


def read_selected_arena():
    if os.path.exists(ARENA_FILE):
        with open(ARENA_FILE, "r", encoding="utf-8") as f:
            value = f.read().strip()
            if value:
                return value
    return "Beirut"


def to_key_label(key_code):
    name = pygame.key.name(key_code)
    return name.upper() if len(name) == 1 else name.replace("_", " ").title()


def is_valid_custom_key(key_code):
    invalid = {
        pygame.K_ESCAPE,
        pygame.K_TAB,
        pygame.K_RETURN,
        pygame.K_KP_ENTER,
        pygame.K_BACKSPACE,
    }
    return key_code not in invalid


class Button:
    def __init__(self, rect, text, style="green"):
        self.rect = pygame.Rect(rect)
        self.text = text
        self.hovered = False
        self.pressed = False
        self.font = get_font(22, bold=True)
        self.style = style

    def handle_event(self, event):
        if event.type == pygame.MOUSEMOTION:
            self.hovered = self.rect.collidepoint(event.pos)
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.rect.collidepoint(event.pos):
                self.pressed = True
        elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:
            was_pressed = self.pressed and self.rect.collidepoint(event.pos)
            self.pressed = False
            if was_pressed:
                return True
        return False

    def draw(self, surface):
        draw_soft_shadow(surface, self.rect, radius=16, alpha=35, offset=(0, 8))
        if self.style == "green":
            base, dark, light = GREEN, GREEN_DARK, GREEN_LIGHT
        else:
            base, dark, light = BROWN, BROWN_DARK, BROWN_LIGHT
        if self.hovered or self.pressed:
            # darker feedback so selected/hovered buttons are obvious on all pages
            base = tuple(max(0, c - 18) for c in base)
            dark = tuple(max(0, c - 24) for c in dark)
        btn = create_button_surface(self.rect.size, base, dark, light, pressed=self.pressed)
        surface.blit(btn, self.rect.topleft)
        draw_text(surface, self.text, self.font, SOFT_WHITE, self.rect.center,
                  center=True, shadow=True, shadow_offset=(0, 2), shadow_alpha=120)


class ColorCard:
    def __init__(self, name, colors):
        self.name = name
        self.colors = colors
        self.rect = pygame.Rect(0, 0, 100, 100)
        self.hovered = False

    def set_rect(self, rect):
        self.rect = pygame.Rect(rect)

    def handle_event(self, event):
        if event.type == pygame.MOUSEMOTION:
            self.hovered = self.rect.collidepoint(event.pos)
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1 and self.rect.collidepoint(event.pos):
            return True
        return False
    def draw_snake_preview(self, surface):
        preview_rect = pygame.Rect(
            self.rect.x + 18,
            self.rect.y + max(38, int(self.rect.height * 0.47)),
            self.rect.width - 36,
            max(24, int(self.rect.height * 0.34)),
        )
        pygame.draw.rect(surface, INPUT_FILL, preview_rect, border_radius=14)
        pygame.draw.rect(surface, INPUT_BORDER, preview_rect, width=2, border_radius=14)

        body = self.colors["body"]
        head = self.colors["head"]
        edge = (255, 248, 239)

        segments = 5
        spacing = max(18, min(28, preview_rect.width // 6))
        radius = max(7, min(11, preview_rect.height // 3))
        total_w = (segments - 1) * spacing
        start_x = preview_rect.centerx - total_w // 2
        mid_y = preview_rect.centery
        pts = [(start_x + i * spacing, mid_y + (2 if i % 2 else -2)) for i in range(segments)]

        for a, b in zip(pts[:-1], pts[1:]):
            pygame.draw.line(surface, body, a, b, radius * 2 - 2)
        for i, (x, y) in enumerate(reversed(pts)):
            color = head if i == 0 else body
            pygame.draw.circle(surface, color, (x, y), radius)
            pygame.draw.circle(surface, edge, (x, y), radius, 2)
            pygame.draw.circle(surface, tuple(min(255, c + 22) for c in color),
                               (x - max(2, radius // 3), y - max(2, radius // 3)), max(2, radius // 3))

        hx, hy = pts[-1]
        pygame.draw.circle(surface, (38, 28, 22), (hx + 3, hy - 3), max(2, radius // 5))
        pygame.draw.circle(surface, (38, 28, 22), (hx + 3, hy + 3), max(2, radius // 5))


    def draw(self, surface, selected=False):
        draw_soft_shadow(surface, self.rect, radius=16, alpha=28, offset=(0, 8))
        fill = CARD_FILL_SELECTED if selected else CARD_FILL
        if self.hovered and not selected:
            fill = (235, 222, 201)
        card_surface = pygame.Surface(self.rect.size, pygame.SRCALPHA)
        pygame.draw.rect(card_surface, (*fill, 230), card_surface.get_rect(), border_radius=18)
        border_width = 4 if selected else 2
        border_color = (142, 111, 68) if (selected or self.hovered) else CARD_BORDER
        pygame.draw.rect(card_surface, border_color, card_surface.get_rect(), width=border_width, border_radius=18)
        if selected:
            tint = pygame.Surface(self.rect.size, pygame.SRCALPHA)
            pygame.draw.rect(tint, (176, 135, 80, 82), tint.get_rect(), border_radius=18)
            card_surface.blit(tint, (0, 0))
        surface.blit(card_surface, self.rect.topleft)
        name_size = 18 if self.rect.height < 74 else 20
        draw_text(surface, self.name, get_font(name_size, bold=True), TEXT_MAIN,
                  (self.rect.centerx, self.rect.y + 20), center=True, shadow=False)
        self.draw_snake_preview(surface)


class KeyInputBox:
    def __init__(self, label, key_name):
        self.label = label
        self.key_name = key_name
        self.rect = pygame.Rect(0, 0, 100, 56)
        self.active = False

    def set_rect(self, rect):
        self.rect = pygame.Rect(rect)

    def handle_mouse(self, pos):
        self.active = self.rect.collidepoint(pos)

    def capture_key(self, key_code):
        if self.active and is_valid_custom_key(key_code):
            self.key_name = pygame.key.name(key_code)
            self.active = False
            return True
        return False

    def draw(self, surface):
        label_font = get_font(21, bold=True)
        value_font = get_font(22, bold=True)
        label_y = self.rect.y - 26
        draw_text(surface, self.label, label_font, TEXT_MAIN, (self.rect.x, label_y), shadow=False)

        draw_soft_shadow(surface, self.rect, radius=12, alpha=18, offset=(0, 4))
        fill = INPUT_FILL if not self.active else (247, 239, 224)
        border = INPUT_ACTIVE if self.active else INPUT_BORDER
        pygame.draw.rect(surface, fill, self.rect, border_radius=14)
        pygame.draw.rect(surface, border, self.rect, width=2, border_radius=14)

        shown = "Press a key..." if self.active else self.key_name.upper()
        color = TEXT_MAIN if not self.active else TEXT_SOFT
        draw_text(surface, shown, value_font, color, self.rect.center, center=True, shadow=False)


class SnakeSetupPage:
    def __init__(self, arena_arg=None, username=None, opponent=None, server_ip=None, port=None, player_id="1", speed="medium"):
        self.username = username or "Player 1"
        self.opponent = opponent or "Player 2"
        self.server_ip = server_ip or "127.0.0.1"
        self.port = str(port or "5050")
        self.player_id = str(player_id or "1")
        self.speed = str(speed or "medium")
        self.bg_original = load_image(ASSET_BG, alpha=False)
        self.bg = scale_image_to_cover(self.bg_original, (WIDTH, HEIGHT))
        self.last_bg_size = (WIDTH, HEIGHT)

        self.title_font = get_font(88, path=os.path.join("fonts", "Birthstone", "Birthstone-Regular.ttf"))
        self.heading_font = get_font(26, bold=True)
        self.small_font = get_font(18)
        self.panel_rect = pygame.Rect(0, 0, int(WIDTH * 0.78), int(HEIGHT * 0.88))

        self.arena_name = arena_arg or read_selected_arena()
        self.color_cards = [ColorCard(name, colors) for name, colors in SNAKE_COLORS.items()]
        self.selected_color = self.color_cards[0].name

        defaults = {"Up": "w", "Down": "s", "Left": "a", "Right": "d"}
        self.key_boxes = [KeyInputBox(label, key_name) for label, key_name in defaults.items()]
        self.error_message = ""

        self.content_rect = pygame.Rect(0, 0, 100, 100)
        self.color_panel = pygame.Rect(0, 0, 100, 100)
        self.input_panel = pygame.Rect(0, 0, 100, 100)

        self.continue_btn = Button((0, 0, 220, 50), "CONTINUE", "green")
        self.back_btn = Button((0, 0, 220, 50), "BACK", "brown")
        self.sync_layout()

    def sync_layout(self):
        panel_w = min(max(1060, int(WIDTH * 0.78)), WIDTH - 90)
        panel_h = min(max(740, int(HEIGHT * 0.84)), HEIGHT - 48)
        self.panel_rect.size = (panel_w, panel_h)
        self.panel_rect.center = (WIDTH // 2, HEIGHT // 2 + 4)

        top_margin = 150
        side_margin = 38
        bottom_reserved = 128
        split_gap = 26

        self.content_rect = pygame.Rect(
            self.panel_rect.x + side_margin,
            self.panel_rect.y + top_margin,
            self.panel_rect.width - side_margin * 2,
            self.panel_rect.height - top_margin - bottom_reserved,
        )

        left_w = (self.content_rect.width - split_gap) // 2
        right_w = self.content_rect.width - left_w - split_gap
        box_h = self.content_rect.height

        self.color_panel = pygame.Rect(self.content_rect.x, self.content_rect.y, left_w, box_h)
        self.input_panel = pygame.Rect(self.color_panel.right + split_gap, self.content_rect.y, right_w, box_h)

        inner_margin_x = 16
        inner_top = 68
        card_gap_y = 7
        num_cards = len(self.color_cards)
        available_h = self.color_panel.height - inner_top - 14 - card_gap_y * (num_cards - 1)
        card_h = max(58, min(70, available_h // max(1, num_cards)))
        card_w = self.color_panel.width - inner_margin_x * 2
        for i, card in enumerate(self.color_cards):
            x = self.color_panel.x + inner_margin_x
            y = self.color_panel.y + inner_top + i * (card_h + card_gap_y)
            card.set_rect((x, y, card_w, card_h))

        field_w = self.input_panel.width - 52
        field_h = 56
        start_x = self.input_panel.x + 26
        start_y = self.input_panel.y + 86
        spacing = 80
        for i, box in enumerate(self.key_boxes):
            box.set_rect((start_x, start_y + i * spacing, field_w, field_h))

        btn_y = self.panel_rect.bottom - 58
        button_gap = 95
        button_w = 210
        button_h = 48
        total_btn_w = button_w * 2 + button_gap
        start_x = self.panel_rect.centerx - total_btn_w // 2
        self.continue_btn.rect = pygame.Rect(start_x, btn_y, button_w, button_h)
        self.back_btn.rect = pygame.Rect(start_x + button_w + button_gap, btn_y, button_w, button_h)

    def on_resize(self, new_width, new_height):
        global WIDTH, HEIGHT
        WIDTH, HEIGHT = new_width, new_height
        self.sync_layout()

    def get_background(self, surface):
        current_size = surface.get_size()
        if self.last_bg_size != current_size:
            self.bg = scale_image_to_cover(self.bg_original, current_size)
            self.last_bg_size = current_size
        return self.bg

    def validate_key_bindings(self):
        keys = [box.key_name.lower() for box in self.key_boxes]
        if len(set(keys)) != 4:
            return "All 4 control keys must be different."
        return ""

    def save_setup(self):
        payload = {
            "arena": self.arena_name,
            "snake_color_name": self.selected_color,
            "snake_colors": SNAKE_COLORS[self.selected_color],
            "controls": {box.label.lower(): box.key_name.lower() for box in self.key_boxes},
        }
        with open(SETUP_FILE, "w", encoding="utf-8") as f:
            json.dump(payload, f, indent=2)

    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            for box in self.key_boxes:
                box.handle_mouse(event.pos)

        if event.type == pygame.KEYDOWN:
            for box in self.key_boxes:
                if box.active:
                    if event.key == pygame.K_ESCAPE:
                        box.active = False
                        return None
                    if box.capture_key(event.key):
                        self.error_message = self.validate_key_bindings()
                        return None

        for card in self.color_cards:
            if card.handle_event(event):
                self.selected_color = card.name
                return None

        if self.continue_btn.handle_event(event):
            self.error_message = self.validate_key_bindings()
            if self.error_message:
                return None

            self.save_setup()
            target_path = os.path.join(os.path.dirname(__file__), GAME_FILE)
            sys.argv = [target_path, self.arena_name, self.username, self.server_ip, self.port, self.player_id, self.opponent, self.speed]
            runpy.run_path(target_path, run_name="__main__")
            sys.exit()

        if self.back_btn.handle_event(event):
            launch_file(ARENA_SETUP_FILE) if self.player_id == "1" else launch_file("lobby.py")
            return "quit"

        return None

    def draw_title(self, surface):
        width, _ = surface.get_size()
        title_text = "The Lebanese Arena"
        title_surface = self.title_font.render(title_text, True, TEXT_MAIN)
        title_shadow = self.title_font.render(title_text, True, TITLE_SHADOW)
        title_shadow.set_alpha(120)
        title_rect = title_surface.get_rect(center=(width // 2, self.panel_rect.y + 52))
        surface.blit(title_shadow, (title_rect.x + 2, title_rect.y + 2))
        surface.blit(title_surface, title_rect)
        surface.blit(title_surface, (title_rect.x + 1, title_rect.y))
        draw_text(surface, "CHOOSE YOUR SNAKE & CONTROLS", self.heading_font, TEXT_MAIN,
                  (width // 2, self.panel_rect.y + 122), center=True, shadow=False)

    def draw_color_panel(self, surface):
        draw_soft_shadow(surface, self.color_panel, radius=18, alpha=24, offset=(0, 8))
        pygame.draw.rect(surface, (*CARD_FILL, 235), self.color_panel, border_radius=18)
        pygame.draw.rect(surface, CARD_BORDER, self.color_panel, width=2, border_radius=18)

        draw_text(surface, "Snake Colors", get_font(24, bold=True), TEXT_MAIN,
                  (self.color_panel.centerx, self.color_panel.y + 26), center=True, shadow=False)
        draw_text(surface, "Choose one color style for your snake.", get_font(16, italic=True), TEXT_SOFT,
                  (self.color_panel.centerx, self.color_panel.y + 52), center=True, shadow=False)

        for card in self.color_cards:
            card.draw(surface, selected=(card.name == self.selected_color))

    def draw_key_panel(self, surface):
        draw_soft_shadow(surface, self.input_panel, radius=18, alpha=24, offset=(0, 8))
        pygame.draw.rect(surface, (*CARD_FILL, 235), self.input_panel, border_radius=18)
        pygame.draw.rect(surface, CARD_BORDER, self.input_panel, width=2, border_radius=18)

        draw_text(surface, "Set Your 4 Control Keys", get_font(24, bold=True), TEXT_MAIN,
                  (self.input_panel.centerx, self.input_panel.y + 26), center=True, shadow=False)

        helper = f"Arena selected: {self.arena_name}"
        draw_text(surface, helper, self.small_font, TEXT_SOFT,
                  (self.input_panel.centerx, self.input_panel.y + 54), center=True, shadow=False)

        for box in self.key_boxes:
            box.draw(surface)

        help_text = "Click a box, then press the key you want for that move."
        draw_text(surface, help_text, get_font(16, italic=True), TEXT_SOFT,
                  (self.input_panel.centerx, self.input_panel.bottom - 54), center=True, shadow=False)

        status_y = self.panel_rect.bottom - 82
        if self.error_message:
            draw_text(surface, self.error_message, get_font(18, bold=True), ERROR_RED,
                      (self.panel_rect.centerx, status_y), center=True, shadow=False)
       
    def draw(self, surface):
        surface.blit(self.get_background(surface), (0, 0))
        draw_vertical_overlay(surface, OVERLAY_TOP, OVERLAY_BOTTOM)
        draw_soft_shadow(surface, self.panel_rect, radius=30, alpha=50, offset=(0, 16))
        panel = rounded_panel(self.panel_rect.size, PANEL, PANEL_BORDER, radius=24, border_width=3, alpha=200)
        surface.blit(panel, self.panel_rect.topleft)

        self.draw_title(surface)
        self.draw_color_panel(surface)
        self.draw_key_panel(surface)
        self.continue_btn.draw(surface)
        self.back_btn.draw(surface)


def main():
    start_background_music()
    global SCREEN, WIDTH, HEIGHT
    arena_arg = sys.argv[1] if len(sys.argv) > 1 else None
    username = sys.argv[2] if len(sys.argv) > 2 else "Player 1"
    opponent = sys.argv[3] if len(sys.argv) > 3 else "Player 2"
    server_ip = sys.argv[4] if len(sys.argv) > 4 else "127.0.0.1"
    port = sys.argv[5] if len(sys.argv) > 5 else "5050"
    player_id = sys.argv[6] if len(sys.argv) > 6 else "1"
    speed = sys.argv[7] if len(sys.argv) > 7 else "medium"
    page = SnakeSetupPage(arena_arg, username, opponent, server_ip, port, player_id, speed)
    running = True
    while running:
        CLOCK.tick(FPS)
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
                break
            if event.type == pygame.VIDEORESIZE:
                WIDTH, HEIGHT = max(1100, event.w), max(700, event.h)
                SCREEN = pygame.display.set_mode((WIDTH, HEIGHT), pygame.RESIZABLE)
                page.on_resize(WIDTH, HEIGHT)
                continue
            result = page.handle_event(event)
            if result == "quit":
                running = False

        page.draw(SCREEN)
        pygame.display.flip()

    pygame.quit()
    sys.exit()


if __name__ == "__main__":
    main()
