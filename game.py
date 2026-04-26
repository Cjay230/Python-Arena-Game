import os
import sys
import math
import json
import time
import subprocess
import runpy
import builtins
import pygame

pygame.init()
try:
    pygame.mixer.init()
except Exception:
    pass

MUSIC_DIR = "music"
BG_MUSIC_FILE = os.path.join(MUSIC_DIR, "music.mp3")
if not os.path.exists(BG_MUSIC_FILE):
    BG_MUSIC_FILE = os.path.join(MUSIC_DIR, "game_music.mp3")
PUNCH_SOUND_FILE = os.path.join(MUSIC_DIR, "punch.mp3")
WINNER_SOUND_FILE = os.path.join(MUSIC_DIR, "winner.mp3")
LOSER_SOUND_FILE = os.path.join(MUSIC_DIR, "loser.mp3")

def safe_load_sound(path):
    try:
        if os.path.exists(path) and pygame.mixer.get_init():
            return pygame.mixer.Sound(path)
    except Exception:
        pass
    return None

def play_background_music():
    try:
        if os.path.exists(BG_MUSIC_FILE) and pygame.mixer.get_init():
            pygame.mixer.music.load(BG_MUSIC_FILE)
            pygame.mixer.music.set_volume(0.28)
            pygame.mixer.music.play(-1)
    except Exception:
        pass

def stop_background_music():
    try:
        if pygame.mixer.get_init():
            pygame.mixer.music.stop()
    except Exception:
        pass


# =========================================================
# WINDOW / APP
# =========================================================
FPS = 60
WINDOW_TITLE = "The Lebanese Arena - Game"
MIN_WIDTH = 1100
MIN_HEIGHT = 700

display_info = pygame.display.Info()
DEFAULT_WIDTH = max(MIN_WIDTH, int(display_info.current_w * 0.90))
DEFAULT_HEIGHT = max(MIN_HEIGHT, int(display_info.current_h * 0.86))

SCREEN = pygame.display.set_mode((DEFAULT_WIDTH, DEFAULT_HEIGHT), pygame.RESIZABLE)
pygame.display.set_caption(WINDOW_TITLE)
CLOCK = pygame.time.Clock()


# =========================================================
# OPTIONAL LIVE CLIENT HOOK
# =========================================================
try:
    from client import GameClient  # type: ignore
except Exception:
    GameClient = None


# =========================================================
# ASSETS
# =========================================================
PLAYER_SETUP_FILE = "player_setup.json"
ASSET_ROCK = "rock.png"
ASSET_GRID = "grid.png"
ASSET_ARROW = "arrow.png"
ASSET_GAME_OVER_BG = "game_over_bg.png"

ARENA_BACKGROUNDS = {
    "Beirut": "beirut.png",
    "Baalbek": "baalbek.png",
    "Sidon": "sidon.png",
    "Byblos": "byblos.png",
}

ARENA_PIES = {
    "Beirut": "aub.png",
    "Baalbek": "sfiha.png",
    "Sidon": "soap.png",
    "Byblos": "fan.png",
}

TITLE_FONT_CANDIDATES = [
    os.path.join("fonts", "Birthstone", "Birthstone-Regular.ttf"),
    os.path.join("fonts", "Birthstone-Regular.ttf"),
]

GRID_COLS = 25
GRID_ROWS = 22

SPRITE_CELL_SCALE = 1.05
ROCK_CELL_SCALE = 0.88
SNAKE_RADIUS_SCALE = 0.45
GRID_BORDER_WIDTH = 3

DEFAULT_P1_COLORS = {"head": [94, 132, 74], "body": [132, 168, 103]}
DEFAULT_P2_COLORS = {"head": [72, 114, 152], "body": [105, 150, 191]}


# =========================================================
# COLORS
# =========================================================
BG_FALLBACK = (225, 213, 192)
PANEL_FILL = (247, 241, 231)
PANEL_BORDER = (219, 192, 145)
PANEL_DIVIDER = (227, 205, 168)

TEXT_MAIN = (108, 80, 56)
TEXT_SOFT = (132, 104, 77)
TEXT_FAINT = (170, 144, 114)
TITLE_SHADOW = (155, 124, 58)

BLUE_TEXT = (103, 137, 178)
RED_TEXT = (205, 93, 74)
BLUE_SNAKE = (103, 137, 178)
BLUE_SNAKE_DARK = (71, 101, 143)
BLUE_SNAKE_LIGHT = (146, 176, 214)
RED_SNAKE = (196, 116, 94)
RED_SNAKE_DARK = (151, 84, 65)
RED_SNAKE_LIGHT = (224, 157, 138)

BOARD_FALLBACK = (239, 225, 195)
BOARD_LINE = (223, 204, 174)
BOARD_BORDER = (211, 181, 137)

TIMER_FILL = (248, 239, 219)
TIMER_BORDER = (212, 182, 136)
INPUT_FILL = (245, 236, 218)
INPUT_BORDER = (214, 186, 141)
SEND_FILL = (184, 146, 92)
SEND_BORDER = (218, 191, 150)
FOOTER_FILL = (248, 240, 220)
FOOTER_BORDER = (215, 187, 140)

OVERLAY_TOP = (255, 253, 249, 24)
OVERLAY_BOTTOM = (200, 186, 166, 2)

SOFT_WHITE = (244, 232, 200)

GREEN = (126, 152, 80)
GREEN_DARK = (89, 111, 56)
GREEN_LIGHT = (160, 184, 112)

BROWN = (116, 63, 36)
BROWN_DARK = (82, 42, 23)
BROWN_LIGHT = (141, 85, 52)

# =========================================================
# HELPERS
# =========================================================
def clamp(value, low, high):
    return max(low, min(high, value))


def load_image(path, alpha=True):
    if not os.path.exists(path):
        return None
    img = pygame.image.load(path)
    return img.convert_alpha() if alpha else img.convert()


def scale_image_to_cover(img, target_size):
    tw, th = target_size
    sw, sh = img.get_size()
    scale = max(tw / max(sw, 1), th / max(sh, 1))
    nw, nh = max(1, int(sw * scale)), max(1, int(sh * scale))
    scaled = pygame.transform.smoothscale(img, (nw, nh))
    x = max(0, (nw - tw) // 2)
    y = max(0, (nh - th) // 2)
    return scaled.subsurface((x, y, tw, th)).copy()


def get_font(size, bold=False, italic=False, path=None):
    if path and os.path.exists(path):
        return pygame.font.Font(path, size)
    preferred = ["Georgia", "Times New Roman", "Garamond", "Palatino Linotype"]
    for name in preferred:
        font = pygame.font.SysFont(name, size, bold=bold, italic=italic)
        if font:
            return font
    return pygame.font.SysFont("serif", size, bold=bold, italic=italic)


def get_title_font(size):
    for path in TITLE_FONT_CANDIDATES:
        if os.path.exists(path):
            return pygame.font.Font(path, size)
    return pygame.font.SysFont("georgia", size, italic=True)


def draw_text(surface, text, font, color, pos, center=False,
              shadow=False, shadow_offset=(0, 3), shadow_alpha=100,
              shadow_color=(35, 23, 14)):
    surf = font.render(text, True, color)
    rect = surf.get_rect()
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

    surface.blit(surf, rect)
    return rect


def draw_wrapped_text(surface, text, font, color, rect, center=False, line_spacing=4):
    words = text.split()
    if not words:
        return

    lines = []
    current = words[0]
    for word in words[1:]:
        trial = current + " " + word
        if font.size(trial)[0] <= rect.width:
            current = trial
        else:
            lines.append(current)
            current = word
    lines.append(current)

    total_h = len(lines) * font.get_height() + max(0, len(lines) - 1) * line_spacing
    y = rect.centery - total_h // 2 if center else rect.y

    for line in lines:
        line_surf = font.render(line, True, color)
        line_rect = line_surf.get_rect()
        if center:
            line_rect.center = (rect.centerx, y + font.get_height() // 2)
        else:
            line_rect.topleft = (rect.x, y)
        surface.blit(line_surf, line_rect)
        y += font.get_height() + line_spacing


def rounded_panel(size, fill, border, radius=22, border_width=3, alpha=230):
    surf = pygame.Surface(size, pygame.SRCALPHA)
    body = pygame.Rect(0, 0, *size)
    pygame.draw.rect(surf, (*fill, alpha), body, border_radius=radius)
    pygame.draw.rect(surf, border, body, width=border_width, border_radius=radius)
    return surf


def draw_soft_shadow(surface, rect, radius=24, alpha=36, offset=(0, 8)):
    shadow_surf = pygame.Surface((rect.width + radius * 2, rect.height + radius * 2), pygame.SRCALPHA)
    shadow_rect = pygame.Rect(radius, radius, rect.width, rect.height)
    pygame.draw.rect(shadow_surf, (0, 0, 0, alpha), shadow_rect, border_radius=24)
    surface.blit(shadow_surf, (rect.x - radius + offset[0], rect.y - radius + offset[1]))


def draw_vertical_overlay(surface, top_rgba, bottom_rgba):
    w, h = surface.get_size()
    overlay = pygame.Surface((w, h), pygame.SRCALPHA)
    for y in range(h):
        t = y / max(h - 1, 1)
        r = int(top_rgba[0] * (1 - t) + bottom_rgba[0] * t)
        g = int(top_rgba[1] * (1 - t) + bottom_rgba[1] * t)
        b = int(top_rgba[2] * (1 - t) + bottom_rgba[2] * t)
        a = int(top_rgba[3] * (1 - t) + bottom_rgba[3] * t)
        pygame.draw.line(overlay, (r, g, b, a), (0, y), (w, y))
    surface.blit(overlay, (0, 0))


def soften_background(surface):
    draw_vertical_overlay(surface, OVERLAY_TOP, OVERLAY_BOTTOM)


def draw_clock_icon(surface, center, radius=10, color=TEXT_MAIN):
    cx, cy = center
    pygame.draw.circle(surface, color, (cx, cy), radius, 2)
    pygame.draw.line(surface, color, (cx, cy), (cx, cy - 4), 2)
    pygame.draw.line(surface, color, (cx, cy), (cx + 4, cy), 2)


def draw_send_icon(surface, rect, color=(248, 241, 228)):
    cx, cy = rect.center
    tip = (cx + 5, cy)
    top_back = (cx - 4, cy - 5)
    mid_cut = (cx - 1, cy)
    bottom_back = (cx - 4, cy + 5)
    pygame.draw.polygon(surface, color, [top_back, tip, bottom_back, mid_cut])


def draw_direction_icon(surface, rect, direction, color=TEXT_MAIN):
    cx, cy = rect.center
    if direction == "UP":
        pygame.draw.line(surface, color, (cx, rect.bottom - 8), (cx, rect.y + 8), 2)
        pygame.draw.line(surface, color, (cx, rect.y + 8), (cx - 5, rect.y + 13), 2)
        pygame.draw.line(surface, color, (cx, rect.y + 8), (cx + 5, rect.y + 13), 2)
    elif direction == "DOWN":
        pygame.draw.line(surface, color, (cx, rect.y + 8), (cx, rect.bottom - 8), 2)
        pygame.draw.line(surface, color, (cx, rect.bottom - 8), (cx - 5, rect.bottom - 13), 2)
        pygame.draw.line(surface, color, (cx, rect.bottom - 8), (cx + 5, rect.bottom - 13), 2)
    elif direction == "LEFT":
        pygame.draw.line(surface, color, (rect.right - 8, cy), (rect.x + 8, cy), 2)
        pygame.draw.line(surface, color, (rect.x + 8, cy), (rect.x + 13, cy - 5), 2)
        pygame.draw.line(surface, color, (rect.x + 8, cy), (rect.x + 13, cy + 5), 2)
    elif direction == "RIGHT":
        pygame.draw.line(surface, color, (rect.x + 8, cy), (rect.right - 8, cy), 2)
        pygame.draw.line(surface, color, (rect.right - 8, cy), (rect.right - 13, cy - 5), 2)
        pygame.draw.line(surface, color, (rect.right - 8, cy), (rect.right - 13, cy + 5), 2)


def cleanup_transparency(surface):
    if surface is None:
        return None

    surf = surface.copy().convert_alpha()
    w, h = surf.get_size()

    for x in range(w):
        for y in range(h):
            r, g, b, a = surf.get_at((x, y))
            if a == 0:
                continue
            near_white = r >= 245 and g >= 245 and b >= 245
            checker_gray = abs(r - g) <= 4 and abs(g - b) <= 4 and 220 <= r <= 242
            pale_bg = r >= 238 and g >= 236 and b >= 232
            if near_white or checker_gray or pale_bg:
                surf.set_at((x, y), (255, 255, 255, 0))

    bound = surf.get_bounding_rect(min_alpha=3)
    if bound.width > 0 and bound.height > 0:
        surf = surf.subsurface(bound).copy()
    return surf


def crop_to_alpha_bounds(surface, min_alpha=3):
    if surface is None:
        return None
    bound = surface.get_bounding_rect(min_alpha=min_alpha)
    if bound.width > 0 and bound.height > 0:
        return surface.subsurface(bound).copy()
    return surface


def prepare_sprite(path, clean=True, crop_alpha=True):
    image = load_image(path, alpha=True)
    if image is None:
        return None
    if clean:
        image = cleanup_transparency(image)
    if crop_alpha:
        image = crop_to_alpha_bounds(image)
    return image

def load_player_setup():
    if not os.path.exists(PLAYER_SETUP_FILE):
        return {}
    try:
        with open(PLAYER_SETUP_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
        return data if isinstance(data, dict) else {}
    except Exception:
        return {}


def format_key_label(key_name):
    if not key_name:
        return "-"
    key_name = str(key_name).strip()
    if not key_name:
        return "-"
    if len(key_name) == 1:
        return key_name.upper()
    return key_name.replace('_', ' ').title()


def key_name_to_code(key_name):
    try:
        return pygame.key.key_code(str(key_name))
    except Exception:
        return None
    
def resolve_arena_name(explicit_arena=None):
    if explicit_arena in ARENA_BACKGROUNDS:
        return explicit_arena

    setup = load_player_setup()
    setup_arena = setup.get("arena")
    if setup_arena in ARENA_BACKGROUNDS:
        return setup_arena

    return "Beirut"


def get_arena_background_path(arena_name):
    return ARENA_BACKGROUNDS.get(arena_name, ARENA_BACKGROUNDS["Beirut"])


def get_arena_pie_path(arena_name):
    return ARENA_PIES.get(arena_name, ARENA_PIES["Beirut"])


def launch_file(filename, *args):
    target_path = os.path.join(os.path.dirname(__file__), filename)
    sys.argv = [target_path] + [str(arg) for arg in args]
    runpy.run_path(target_path, run_name="__main__")
    sys.exit()


class ActionButton:
    def __init__(self, rect, text, style="green"):
        self.rect = pygame.Rect(rect)
        self.text = text
        self.style = style
        self.hovered = False
        self.pressed = False
        self.font = get_font(22, bold=True)

    def handle_event(self, event):
        if event.type == pygame.MOUSEMOTION:
            self.hovered = self.rect.collidepoint(event.pos)
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.rect.collidepoint(event.pos):
                self.pressed = True
        elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:
            clicked = self.pressed and self.rect.collidepoint(event.pos)
            self.pressed = False
            if clicked:
                return True
        return False

    def draw(self, surface):
        draw_soft_shadow(surface, self.rect, radius=16, alpha=35, offset=(0, 8))

        if self.style == "green":
            base, dark, light = (126, 152, 80), (89, 111, 56), (160, 184, 112)
        elif self.style == "blue":
            base, dark, light = (103, 137, 178), (71, 101, 143), (146, 176, 214)
        else:
            base, dark, light = (116, 63, 36), (82, 42, 23), (141, 85, 52)

        if self.hovered or self.pressed:
            base = tuple(max(0, c - 18) for c in base)
            dark = tuple(max(0, c - 24) for c in dark)

        surf = pygame.Surface(self.rect.size, pygame.SRCALPHA)
        outer = pygame.Rect(0, 0, *self.rect.size)
        pygame.draw.rect(surf, dark, outer, border_radius=14)
        inner = outer.inflate(-4, -4)
        pygame.draw.rect(surf, base, inner, border_radius=12)

        gloss_h = max(10, inner.height // 3)
        gloss = pygame.Rect(inner.x + 6, inner.y + 5, inner.width - 12, gloss_h)
        gloss_layer = pygame.Surface(self.rect.size, pygame.SRCALPHA)
        pygame.draw.rect(gloss_layer, (*light, 40 if not self.pressed else 18), gloss, border_radius=9)
        surf.blit(gloss_layer, (0, 0))
        pygame.draw.rect(surf, (215, 192, 152), inner, width=2, border_radius=12)

        surface.blit(surf, self.rect.topleft)
        draw_text(surface, self.text, self.font, (244, 232, 200), self.rect.center,
                  center=True, shadow=True, shadow_offset=(0, 2), shadow_alpha=120)


class MatchStatsTracker:
    def __init__(self):
        self.reset()

    def reset(self):
        self.prev_health = None
        self.prev_pie_positions = None
        self.pies = [0, 0]
        self.collisions = [0, 0]

    def update(self, state):
        health = list(state.get("health", [0, 0]))
        pies = state.get("pies", [])
        pie_positions = {(p.get("x"), p.get("y"), p.get("kind")) for p in pies if isinstance(p, dict)}

        if self.prev_health is None:
            self.prev_health = health
            self.prev_pie_positions = pie_positions
            return

        for i in range(min(2, len(health), len(self.prev_health))):
            if health[i] > self.prev_health[i]:
                self.pies[i] += 1
            elif health[i] < self.prev_health[i]:
                self.collisions[i] += 1

        self.prev_health = health
        self.prev_pie_positions = pie_positions


# =========================================================
# CHAT INPUT
# =========================================================
class ChatInput:
    def __init__(self):
        self.text = ""
        self.active = False
        self.max_len = 120
        self.cursor_timer = 0
        self.show_cursor = True
        self.font = get_font(18)
        self.input_rect = pygame.Rect(0, 0, 100, 40)
        self.send_rect = pygame.Rect(0, 0, 40, 40)

    def set_rects(self, input_rect, send_rect):
        self.input_rect = pygame.Rect(input_rect)
        self.send_rect = pygame.Rect(send_rect)

    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            self.active = self.input_rect.collidepoint(event.pos)
            if self.send_rect.collidepoint(event.pos):
                return "send"

        if event.type == pygame.KEYDOWN and self.active:
            if event.key == pygame.K_RETURN:
                return "send"
            if event.key == pygame.K_BACKSPACE:
                self.text = self.text[:-1]
            else:
                if len(self.text) < self.max_len and event.unicode.isprintable() and event.unicode not in ["\t", "\r", "\n"]:
                    self.text += event.unicode
        return None

    def update(self):
        self.cursor_timer += 1
        if self.cursor_timer >= 30:
            self.cursor_timer = 0
            self.show_cursor = not self.show_cursor

    def clear(self):
        self.text = ""

    def draw(self, surface, arrow_sprite=None):
        box = pygame.Surface(self.input_rect.size, pygame.SRCALPHA)
        pygame.draw.rect(box, INPUT_FILL, box.get_rect(), border_radius=12)
        pygame.draw.rect(box, INPUT_BORDER, box.get_rect(), width=2, border_radius=12)
        surface.blit(box, self.input_rect.topleft)

        send = pygame.Surface(self.send_rect.size, pygame.SRCALPHA)
        pygame.draw.rect(send, SEND_FILL, send.get_rect(), border_radius=12)
        pygame.draw.rect(send, SEND_BORDER, send.get_rect(), width=2, border_radius=12)
        surface.blit(send, self.send_rect.topleft)

        if arrow_sprite is not None:
            arrow_rect = arrow_sprite.get_rect(center=self.send_rect.center)
            surface.blit(arrow_sprite, arrow_rect)
        else:
            draw_send_icon(surface, self.send_rect, color=(248, 241, 228))

        content = self.text if self.text else "Type a message..."
        color = TEXT_MAIN if self.text else TEXT_FAINT
        text_surf = self.font.render(content, True, color)
        text_rect = text_surf.get_rect(midleft=(self.input_rect.x + 12, self.input_rect.centery))
        surface.blit(text_surf, text_rect)

        if self.active and self.show_cursor:
            cursor_x = min(self.input_rect.right - 10, text_rect.right + 3)
            pygame.draw.line(surface, TEXT_MAIN, (cursor_x, self.input_rect.y + 10), (cursor_x, self.input_rect.bottom - 10), 2)


# =========================================================
# DEMO / FALLBACK CLIENT BRIDGE
# =========================================================
class DummyClient:
    def __init__(self, arena="Beirut", username="Player 1", opponent="Player 2", player_id=1):
        self.username = username
        self.opponent = opponent
        self.connected = True
        self.player_id = player_id
        self.spectating = False
        self.game_started = True
        self.game_over = False
        self.winner = None
        self.final_health = [100, 100]
        self.start_time = time.time()
        self.duration = 180

        self.player_names = [username, opponent] if player_id == 1 else [opponent, username]

        self.chat_messages = [
            (self.player_names[0].upper(), "Good luck!"),
            (self.player_names[1].upper(), "You too!"),
        ]
        self.game_state = {
            "arena": arena,
            "players": self.player_names,
            "snakes": [
                [[4, 4], [3, 4], [2, 4], [1, 4], [1, 5], [2, 5]],
                [[13, 10], [14, 10], [15, 10], [16, 10], [17, 10]],
            ],
            "pies": [
                {"x": 2, "y": 2, "kind": "normal"},
                {"x": 16, "y": 2, "kind": "golden"},
                {"x": 8, "y": 7, "kind": "normal"},
                {"x": 2, "y": 13, "kind": "normal"},
                {"x": 16, "y": 15, "kind": "power"},
            ],
            "obstacles": [
                {"x": 9, "y": 2, "kind": "spike"},
                {"x": 13, "y": 5, "kind": "regular"},
                {"x": 5, "y": 8, "kind": "regular"},
                {"x": 15, "y": 8, "kind": "regular"},
                {"x": 10, "y": 14, "kind": "regular"},
                {"x": 4, "y": 12, "kind": "regular"},
            ],
            "health": [100, 100],
            "time_left": 60,
            "frozen": [False, False],
        }

    def move(self, direction):
        return None

    def send_chat(self, text):
        self.chat_messages.append((str(self.username).upper(), text))

    def close(self):
        pass


# =========================================================
# MAIN PAGE
# =========================================================
class BeirutArenaPage:
    def __init__(self, client=None, arena_name=None):
        self.client = client
        self.player_setup = load_player_setup()
        controls = self.player_setup.get("controls", {}) if isinstance(self.player_setup, dict) else {}
        self.control_labels = {
            "UP": format_key_label(controls.get("up", "w")),
            "DOWN": format_key_label(controls.get("down", "s")),
            "LEFT": format_key_label(controls.get("left", "a")),
            "RIGHT": format_key_label(controls.get("right", "d")),
        }
        self.control_key_map = {}
        for direction, raw_key in (("UP", controls.get("up", "w")), ("DOWN", controls.get("down", "s")), ("LEFT", controls.get("left", "a")), ("RIGHT", controls.get("right", "d"))):
            code = key_name_to_code(raw_key)
            if code is not None:
                self.control_key_map[code] = direction

        self.arena_name = resolve_arena_name(arena_name)
        self.bg_original = load_image(get_arena_background_path(self.arena_name), alpha=False)
        self.pie_original = prepare_sprite(get_arena_pie_path(self.arena_name))
        self.rock_original = prepare_sprite(ASSET_ROCK)
        self.grid_original = prepare_sprite(ASSET_GRID)
        self.arrow_original = prepare_sprite(ASSET_ARROW, clean=False, crop_alpha=True)

        self.last_bg_size = None
        self.bg_surface = None

        self.title_font = get_title_font(88)
        self.subtitle_font = get_font(23, bold=True)
        self.panel_title_font = get_font(19, bold=True)
        self.label_font = get_font(17, bold=True)
        self.text_font = get_font(16)
        self.small_font = get_font(14)
        self.timer_font = get_font(22, bold=True)
        self.footer_font = get_font(18)
        self.chat_input = ChatInput()
        self.stats_tracker = MatchStatsTracker()
        self.punch_sound = safe_load_sound(PUNCH_SOUND_FILE)
        self.last_total_hits = 0
        self.gameover_lobby_btn = ActionButton((0, 0, 140, 44), "LOBBY", "brown")
        self.gameover_quit_btn = ActionButton((0, 0, 140, 44), "QUIT", "green")
        self.result_sound_played = False
        self.winner_sound = safe_load_sound(WINNER_SOUND_FILE)
        self.loser_sound = safe_load_sound(LOSER_SOUND_FILE)

        self.board_rect = pygame.Rect(0, 0, 10, 10)
        self.play_rect = pygame.Rect(0, 0, 10, 10)
        self.left_panel = pygame.Rect(0, 0, 10, 10)
        self.right_panel = pygame.Rect(0, 0, 10, 10)
        self.footer_rect = pygame.Rect(0, 0, 10, 10)
        self.timer_rect = pygame.Rect(0, 0, 10, 10)
        self.chat_box_rect = pygame.Rect(0, 0, 10, 10)

        self.aub_scaled = None
        self.rock_scaled = None
        self.grid_scaled = None
        self.arrow_scaled = None

        self.sync_layout(*SCREEN.get_size())

    def set_arena_assets(self, arena_name):
        self.arena_name = resolve_arena_name(arena_name)
        self.bg_original = load_image(get_arena_background_path(self.arena_name), alpha=False)
        self.pie_original = prepare_sprite(get_arena_pie_path(self.arena_name))
        self.bg_surface = None
        self.last_bg_size = None
        self.sync_layout(*SCREEN.get_size())

    # -----------------------------------------------------
    # STATE
    # -----------------------------------------------------
    def preview_state(self):
        if hasattr(self.client, "start_time"):
            elapsed = int(time.time() - self.client.start_time)
            self.client.game_state["time_left"] = max(0, getattr(self.client, "duration", 180) - elapsed)

        return {
            "arena": self.arena_name,
            "players": list(getattr(self.client, "player_names", ["Player 1", "Player 2"])),
            "snakes": [
                [[4, 4], [3, 4], [2, 4], [1, 4], [1, 5], [2, 5]],
                [[13, 10], [14, 10], [15, 10], [16, 10], [17, 10]],
            ],
            "pies": [
                {"x": 2, "y": 2, "kind": "normal"},
                {"x": 16, "y": 2, "kind": "golden"},
                {"x": 8, "y": 7, "kind": "normal"},
                {"x": 2, "y": 13, "kind": "normal"},
                {"x": 16, "y": 15, "kind": "power"},
            ],
            "obstacles": [
                {"x": 9, "y": 2, "kind": "spike"},
                {"x": 13, "y": 5, "kind": "regular"},
                {"x": 5, "y": 8, "kind": "regular"},
                {"x": 15, "y": 8, "kind": "regular"},
                {"x": 10, "y": 14, "kind": "regular"},
                {"x": 4, "y": 12, "kind": "regular"},
            ],
            "health": [100, 100],
            "time_left": 60,
            "frozen": [False, False],
        }

    def get_state(self):
        raw = getattr(self.client, "game_state", None)

        # In live mode, game_state is None while this page waits for the other player.
        # Do not call raw.get() here, or the window crashes black and disconnects.
        if not isinstance(raw, dict):
            if getattr(self.client, "waiting_for_opponent", False):
                return {
                    "arena": self.arena_name,
                    "players": list(getattr(self.client, "player_names", ["Player 1", "Player 2"])),
                    "snakes": [[], []],
                    "pies": [],
                    "obstacles": [],
                    "health": [100, 100],
                    "time_left": 60,
                    "frozen": [False, False],
                    "player_styles": getattr(self.client, "player_styles", {}),
                    "stats": [{}, {}],
                }
            return self.preview_state()

        arena = raw.get("arena")
        if arena in ARENA_BACKGROUNDS and arena != self.arena_name:
            self.set_arena_assets(arena)

        snakes = raw.get("snakes", [])
        obstacles = raw.get("obstacles", [])
        pies = raw.get("pies", [])
        if snakes or obstacles or pies:
            return {
                "arena": raw.get("arena", self.arena_name),
                "players": raw.get("players", getattr(self.client, "player_names", ["Player 1", "Player 2"])),
                "snakes": raw.get("snakes", [[], []]),
                "pies": raw.get("pies", []),
                "obstacles": raw.get("obstacles", []),
                "health": raw.get("health", [0, 0]),
                "time_left": raw.get("time_left", 0),
                "frozen": raw.get("frozen", [False, False]),
                "player_styles": raw.get("player_styles", getattr(self.client, "player_styles", {})),
                "stats": raw.get("stats", [{}, {}]),
            }
        return self.preview_state()

    def get_chat_messages(self):
        msgs = getattr(self.client, "chat_messages", [])
        cleaned = []
        for item in msgs[-8:]:
            if isinstance(item, dict):
                sender = str(item.get("from", "ALI")).upper()
                message = str(item.get("message", ""))
            elif isinstance(item, (list, tuple)) and len(item) >= 2:
                sender = str(item[0]).upper()
                message = str(item[1])
            else:
                continue
            cleaned.append((sender, message))
        return cleaned

    def get_player_names(self):
        state = self.get_state()
        names = state.get("players") if isinstance(state, dict) else None

        if isinstance(names, list) and len(names) >= 2:
            return str(names[0]).upper(), str(names[1]).upper()

        client_names = getattr(self.client, "player_names", None)
        if isinstance(client_names, list) and len(client_names) >= 2:
            return str(client_names[0]).upper(), str(client_names[1]).upper()

        username = getattr(self.client, "username", "Player 1")
        opponent = getattr(self.client, "opponent", "Player 2")
        player_id = getattr(self.client, "player_id", 1)

        if player_id == 2:
            return str(opponent).upper(), str(username).upper()
        return str(username).upper(), str(opponent).upper()
    def get_player_styles(self):
        state = self.get_state()
        styles = {}
        if isinstance(state, dict):
            styles = state.get("player_styles", {}) or {}
        if not styles:
            styles = getattr(self.client, "player_styles", {}) or {}
        return styles if isinstance(styles, dict) else {}

    def get_snake_palette(self, player_index):
        names = self.get_state().get("players", []) if isinstance(self.get_state(), dict) else []
        styles = self.get_player_styles()
        setup_colors = self.player_setup.get("snake_colors", DEFAULT_P1_COLORS) if isinstance(self.player_setup, dict) else DEFAULT_P1_COLORS

        if isinstance(names, list) and len(names) > player_index:
            raw_name = str(names[player_index])
            entry = styles.get(raw_name) or styles.get(raw_name.upper()) or styles.get(raw_name.lower())
            if isinstance(entry, dict) and isinstance(entry.get("snake_colors"), dict):
                colors = entry["snake_colors"]
            elif player_index == (getattr(self.client, "player_id", 1) - 1):
                colors = setup_colors
            else:
                colors = DEFAULT_P2_COLORS
        elif player_index == 0:
            colors = setup_colors
        else:
            colors = DEFAULT_P2_COLORS

        head = tuple(colors.get("head", DEFAULT_P1_COLORS["head"]))
        body = tuple(colors.get("body", DEFAULT_P1_COLORS["body"]))
        edge = tuple(max(0, c - 34) for c in body)
        light = tuple(min(255, c + 42) for c in body)
        return head, body, edge, light


    # -----------------------------------------------------
    # LAYOUT
    # -----------------------------------------------------
    def sync_layout(self, width, height):
        outer_margin_x = clamp(int(width * 0.020), 20, 30)
        panel_w = clamp(int(width * 0.182), 246, 262)
        panel_gap = clamp(int(width * 0.022), 52, 76)

        self.title_y = 80
        self.subtitle_y = 138

        board_top = 212
        bottom_margin = 22

        max_board_from_height = height - board_top - bottom_margin

        board_w = min(700, width - (panel_w * 2 + panel_gap * 2 + outer_margin_x * 2 + 24))
        board_w = max(560, board_w)

        board_h_from_ratio = int(round(board_w * GRID_ROWS / GRID_COLS))
        if board_h_from_ratio > max_board_from_height:
            board_h = max(492, max_board_from_height)
            board_w = int(round(board_h * GRID_COLS / GRID_ROWS))
        else:
            board_h = board_h_from_ratio

        total_w = panel_w * 2 + panel_gap * 2 + board_w
        max_total_w = width - outer_margin_x * 2
        if total_w > max_total_w:
            overflow = total_w - max_total_w
            board_w = max(520, board_w - overflow)
            board_h = int(round(board_w * GRID_ROWS / GRID_COLS))
            total_w = panel_w * 2 + panel_gap * 2 + board_w

        group_x = max(outer_margin_x, (width - total_w) // 2)
        board_x = group_x + panel_w + panel_gap
        self.board_rect = pygame.Rect(board_x, board_top, board_w, board_h)

        left_h = clamp(int(board_h * 0.84), 390, 500)
        right_h = clamp(int(board_h * 0.80), 350, 460)
        panel_top_offset = clamp(int(board_h * 0.09), 34, 46)

        self.left_panel = pygame.Rect(
            self.board_rect.x - panel_gap - panel_w - 6,
            self.board_rect.y + panel_top_offset,
            panel_w,
            left_h,
        )
        self.right_panel = pygame.Rect(
            self.board_rect.right + panel_gap + 6,
            self.board_rect.y + panel_top_offset + 2,
            panel_w,
            right_h,
        )

        self.footer_rect = pygame.Rect(0, 0, 0, 0)

        self.timer_rect = pygame.Rect(0, 0, 126, 46)
        self.timer_rect.midbottom = (self.board_rect.centerx, self.board_rect.y - 2)

        inset = max(8, int(min(board_w, board_h) * 0.012))
        self.play_rect = pygame.Rect(
            self.board_rect.x + inset,
            self.board_rect.y + inset,
            self.board_rect.width - 2 * inset,
            self.board_rect.height - 2 * inset,
        )

        self.chat_box_rect = pygame.Rect(
            self.right_panel.x + 14,
            self.right_panel.y + 62,
            self.right_panel.width - 28,
            self.right_panel.height - 120,
        )

        self.chat_input.set_rects(
            pygame.Rect(
                self.right_panel.x + 14,
                self.right_panel.bottom - 48,
                self.right_panel.width - 66,
                36
            ),
            pygame.Rect(
                self.right_panel.right - 44,
                self.right_panel.bottom - 48,
                30,
                36
            ),
        )

        self.gameover_lobby_btn.rect = pygame.Rect(self.board_rect.centerx - 155, self.board_rect.centery + 122, 140, 44)
        self.gameover_quit_btn.rect = pygame.Rect(self.board_rect.centerx + 15, self.board_rect.centery + 122, 140, 44)

        cell = min(
            self.play_rect.width / GRID_COLS,
            self.play_rect.height / GRID_ROWS
        )

        if self.pie_original is not None:
          pie_size = max(34, int(cell * SPRITE_CELL_SCALE))
          self.aub_scaled = pygame.transform.smoothscale(self.pie_original, (pie_size, pie_size))
        else:
             self.aub_scaled = None

        if self.rock_original is not None:
            rock_size = max(32, int(cell * ROCK_CELL_SCALE))
            self.rock_scaled = pygame.transform.smoothscale(self.rock_original, (rock_size, rock_size))
        else:
            self.rock_scaled = None

        if self.arrow_original is not None:
            arrow_w = max(15, int(self.chat_input.send_rect.width * 0.54))
            arrow_h = max(15, int(self.chat_input.send_rect.height * 0.54))
            self.arrow_scaled = pygame.transform.smoothscale(self.arrow_original, (arrow_w, arrow_h))
        else:
            self.arrow_scaled = None

        self.grid_scaled = None

    def on_resize(self, width, height):
        self.sync_layout(width, height)
        self.bg_surface = None
        self.last_bg_size = None

    # -----------------------------------------------------
    # RENDER HELPERS
    # -----------------------------------------------------
    def get_background(self, surface):
        size = surface.get_size()
        if self.bg_original is None:
            fallback = pygame.Surface(size)
            fallback.fill(BG_FALLBACK)
            return fallback

        if self.bg_surface is None or self.last_bg_size != size:
            self.bg_surface = scale_image_to_cover(self.bg_original, size)
            self.last_bg_size = size
        return self.bg_surface

    def grid_to_pixel_center(self, gx, gy):
        cell_w = self.play_rect.width / GRID_COLS
        cell_h = self.play_rect.height / GRID_ROWS
        x = self.play_rect.x + gx * cell_w + cell_w / 2
        y = self.play_rect.y + gy * cell_h + cell_h / 2
        return int(x), int(y)

    # -----------------------------------------------------
    # EVENTS / UPDATE
    # -----------------------------------------------------
    def handle_event(self, event):
        if getattr(self.client, "game_over", False):
            if self.gameover_lobby_btn.handle_event(event):
                stop_background_music()
                builtins.PITHON_SHARED_CLIENT = self.client
                target_path = os.path.join(os.path.dirname(__file__), "lobby.py")
                sys.argv = [target_path, getattr(self.client, "username", "Player"), "", ""]
                runpy.run_path(target_path, run_name="__main__")
                return "quit"
            if self.gameover_quit_btn.handle_event(event):
                stop_background_music()
                return "quit"
            return None
        if getattr(self.client, "spectating", False):
            if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                return "quit"
            return None

        result = self.chat_input.handle_event(event)
        if result == "send":
            text = self.chat_input.text.strip()
            if text:
                if hasattr(self.client, "send_chat"):
                    self.client.send_chat(text)
                self.chat_input.clear()

        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                return "quit"

            direction = self.control_key_map.get(event.key)
            if direction is None:
                arrow_fallback = {
                    pygame.K_UP: "UP",
                    pygame.K_DOWN: "DOWN",
                    pygame.K_LEFT: "LEFT",
                    pygame.K_RIGHT: "RIGHT",
                }
                direction = arrow_fallback.get(event.key)

            if direction and hasattr(self.client, "move"):
                self.client.move(direction)
        return None

    def update(self):
        self.chat_input.update()
        state = self.get_state()
        self.stats_tracker.update(state)
        stats = state.get("stats", []) if isinstance(state, dict) else []
        total_hits = 0
        for item in stats:
            if isinstance(item, dict):
                total_hits += int(item.get("obstacles", 0) or 0)
        if total_hits > self.last_total_hits and self.punch_sound is not None:
            try:
                self.punch_sound.play()
            except Exception:
                pass
        self.last_total_hits = total_hits

    # -----------------------------------------------------
    # DRAW SECTIONS
    # -----------------------------------------------------
    def draw_header(self, surface, time_left):
        cx = surface.get_width() // 2

        title_shadow = self.title_font.render("The Lebanese Arena", True, TITLE_SHADOW)
        title_shadow.set_alpha(120)

        title_rect = title_shadow.get_rect(center=(cx, self.title_y))
        surface.blit(title_shadow, (title_rect.x + 2, title_rect.y + 2))

        title_main = self.title_font.render("The Lebanese Arena", True, TEXT_MAIN)
        surface.blit(title_main, title_rect)
        surface.blit(title_main, (title_rect.x + 1, title_rect.y))

        draw_text(
            surface,
            f"{self.arena_name.upper()} ARENA",
            self.subtitle_font,
            BROWN,
            (cx, self.subtitle_y),
            center=True,
            shadow=False
        )

        draw_soft_shadow(surface, self.timer_rect, radius=12, alpha=16, offset=(0, 2))
        capsule = rounded_panel(self.timer_rect.size, TIMER_FILL, TIMER_BORDER, radius=16, border_width=3, alpha=238)
        surface.blit(capsule, self.timer_rect.topleft)

        icon_center = (self.timer_rect.x + 26, self.timer_rect.centery)
        draw_clock_icon(surface, icon_center, radius=8, color=TEXT_MAIN)

        total = max(0, int(time_left))
        mins = total // 60
        secs = total % 60
        time_surf = self.timer_font.render(f"{mins:02d}:{secs:02d}", True, TEXT_MAIN)
        time_rect = time_surf.get_rect(center=(self.timer_rect.centerx + 8, self.timer_rect.centery))
        surface.blit(time_surf, time_rect)

    def draw_board(self, surface, state):
        draw_soft_shadow(surface, self.board_rect, radius=24, alpha=28, offset=(0, 8))
        self.draw_board_fallback(surface)

        self.draw_pies(surface, state.get("pies", []))
        self.draw_obstacles(surface, state.get("obstacles", []))

        snakes = state.get("snakes", [[], []])
        if len(snakes) < 2:
            snakes = [[], []]
        p1_name, p2_name = self.get_player_names()
        p1_head, p1_body, p1_edge, p1_light = self.get_snake_palette(0)
        p2_head, p2_body, p2_edge, p2_light = self.get_snake_palette(1)
        self.draw_snake(surface, snakes[0], p1_body, p1_edge, p1_light, p1_name, p1_head)
        self.draw_snake(surface, snakes[1], p2_body, p2_edge, p2_light, p2_name, p2_head)

    def draw_board_fallback(self, surface):
        outer = self.board_rect
        inner = self.play_rect

        pygame.draw.rect(surface, (240, 225, 196), outer, border_radius=18)
        pygame.draw.rect(surface, BOARD_BORDER, outer, width=GRID_BORDER_WIDTH, border_radius=18)

        rim = outer.inflate(-16, -16)
        pygame.draw.rect(surface, (237, 221, 191), rim, border_radius=12)
        pygame.draw.rect(surface, (198, 171, 129), rim, width=GRID_BORDER_WIDTH, border_radius=12)

        pygame.draw.rect(surface, (243, 229, 199), inner, border_radius=6)
        pygame.draw.rect(surface, (207, 179, 137), inner, width=GRID_BORDER_WIDTH, border_radius=6)

        cell_w = self.play_rect.width / GRID_COLS
        cell_h = self.play_rect.height / GRID_ROWS

        for i in range(GRID_COLS + 1):
            x = int(round(self.play_rect.x + i * cell_w))
            pygame.draw.line(surface, BOARD_LINE, (x, self.play_rect.y), (x, self.play_rect.bottom), 1)

        for i in range(GRID_ROWS + 1):
            y = int(round(self.play_rect.y + i * cell_h))
            pygame.draw.line(surface, BOARD_LINE, (self.play_rect.x, y), (self.play_rect.right, y), 1)

    def draw_pies(self, surface, pies):
        for pie in pies:
            gx = pie.get("x", 0)
            gy = pie.get("y", 0)
            kind = pie.get("kind", "normal")
            cx, cy = self.grid_to_pixel_center(gx, gy)

            if self.aub_scaled is not None:
                if kind == "golden":
                    glow = pygame.Surface(
                        (self.aub_scaled.get_width() + 12, self.aub_scaled.get_height() + 12),
                        pygame.SRCALPHA
                    )
                    pygame.draw.circle(glow, (244, 208, 111, 58), glow.get_rect().center, glow.get_width() // 2)
                    surface.blit(glow, glow.get_rect(center=(cx, cy)))
                elif kind == "power":
                    glow = pygame.Surface(
                        (self.aub_scaled.get_width() + 14, self.aub_scaled.get_height() + 14),
                        pygame.SRCALPHA
                    )
                    pygame.draw.circle(glow, (186, 145, 220, 46), glow.get_rect().center, glow.get_width() // 2)
                    surface.blit(glow, glow.get_rect(center=(cx, cy)))

                rect = self.aub_scaled.get_rect(center=(cx, cy))
                surface.blit(self.aub_scaled, rect)
            else:
                pygame.draw.circle(surface, (180, 126, 88), (cx, cy), 12)
                pygame.draw.circle(surface, (240, 224, 190), (cx, cy), 8)

    def draw_obstacles(self, surface, obstacles):
        for obs in obstacles:
            gx = obs.get("x", 0)
            gy = obs.get("y", 0)
            cx, cy = self.grid_to_pixel_center(gx, gy)
            if self.rock_scaled is not None:
                rect = self.rock_scaled.get_rect(center=(cx, cy))
                surface.blit(self.rock_scaled, rect)
            else:
                pygame.draw.circle(surface, (150, 131, 112), (cx, cy), 16)
                pygame.draw.circle(surface, (179, 159, 136), (cx - 4, cy - 4), 7)

    def draw_snake(self, surface, snake_cells, fill_color, edge_color, light_color, label, label_color):
        if not snake_cells:
            return

        points = [self.grid_to_pixel_center(x, y) for x, y in snake_cells]
        cell = min(
            self.play_rect.width / GRID_COLS,
            self.play_rect.height / GRID_ROWS
        )
        radius = max(9, int(cell * SNAKE_RADIUS_SCALE))

        hx, hy = points[0]

        for a, b in zip(points[:-1], points[1:]):
            pygame.draw.line(surface, edge_color, a, b, radius * 2 + 2)
            pygame.draw.line(surface, fill_color, a, b, radius * 2 - 2)

        for i, (x, y) in enumerate(reversed(points)):
            idx = len(points) - 1 - i
            r = radius
            pygame.draw.circle(surface, edge_color, (x, y), r)
            pygame.draw.circle(surface, fill_color, (x, y), r - 2)
            pygame.draw.circle(surface, light_color, (x - max(2, r // 4), y - max(2, r // 4)), max(2, r // 3))

        if len(points) > 1:
            dx = points[0][0] - points[1][0]
            dy = points[0][1] - points[1][1]
        else:
            dx, dy = 1, 0

        eye_color = (46, 41, 36)
        if abs(dx) >= abs(dy):
            eye_x = 4 if dx >= 0 else -4
            pygame.draw.circle(surface, eye_color, (hx + eye_x, hy - 3), 2)
            pygame.draw.circle(surface, eye_color, (hx + eye_x, hy + 3), 2)
        else:
            eye_y = 4 if dy >= 0 else -4
            pygame.draw.circle(surface, eye_color, (hx - 3, hy + eye_y), 2)
            pygame.draw.circle(surface, eye_color, (hx + 3, hy + eye_y), 2)

    def draw_left_panel(self, surface, state):
        draw_soft_shadow(surface, self.left_panel, radius=18, alpha=24, offset=(0, 7))
        panel = rounded_panel(self.left_panel.size, PANEL_FILL, PANEL_BORDER, radius=22, border_width=3, alpha=222)
        surface.blit(panel, self.left_panel.topleft)

        x, y, w, h = self.left_panel
        health = list(state.get("health", [0, 0]))
        while len(health) < 2:
            health.append(0)

        draw_text(surface, "PLAYERS", self.panel_title_font, TEXT_MAIN, (x + w // 2, y + 30), center=True, shadow=False)

        name_font = get_font(18, bold=True)
        score_font = get_font(18, bold=True)

        row1 = y + 92
        row2 = row1 + 44

        p1_name, p2_name = self.get_player_names()

        p1_head, p1_body, _, _ = self.get_snake_palette(0)
        p2_head, p2_body, _, _ = self.get_snake_palette(1)

        pygame.draw.circle(surface, p1_body, (x + 28, row1), 8)
        ali_surf = name_font.render(p1_name, True, p1_head)
        surface.blit(ali_surf, ali_surf.get_rect(midleft=(x + 48, row1 + 1)))
        score1_surf = score_font.render(str(health[0]), True, TEXT_MAIN)
        surface.blit(score1_surf, score1_surf.get_rect(midright=(x + w - 16, row1 + 1)))

        pygame.draw.circle(surface, p2_body, (x + 28, row2), 8)
        maya_surf = name_font.render(p2_name, True, p2_head)
        surface.blit(maya_surf, maya_surf.get_rect(midleft=(x + 48, row2 + 1)))
        score2_surf = score_font.render(str(health[1]), True, TEXT_MAIN)
        surface.blit(score2_surf, score2_surf.get_rect(midright=(x + w - 16, row2 + 1)))

        divider_y = y + 168
        pygame.draw.line(surface, PANEL_DIVIDER, (x + 14, divider_y), (x + w - 14, divider_y), 1)
        draw_text(surface, "CONTROLS", self.panel_title_font, TEXT_MAIN, (x + w // 2, divider_y + 28), center=True, shadow=False)

        key_y0 = divider_y + 56
        key_h = 38
        row_gap = 13
        label_x = x + 138
        rows = [("UP", self.control_labels.get("UP", "W"), "UP"), ("DOWN", self.control_labels.get("DOWN", "S"), "DOWN"), ("LEFT", self.control_labels.get("LEFT", "A"), "LEFT"), ("RIGHT", self.control_labels.get("RIGHT", "D"), "RIGHT")]

        for i, (icon_dir, letter, label) in enumerate(rows):
            ry = key_y0 + i * (key_h + row_gap)

            arrow_rect = pygame.Rect(x + 18, ry, 38, 38)
            pygame.draw.rect(surface, (247, 239, 219), arrow_rect, border_radius=9)
            pygame.draw.rect(surface, (166, 135, 92), arrow_rect, width=3, border_radius=9)
            draw_direction_icon(surface, arrow_rect.inflate(-4, -4), icon_dir)

            key_rect = pygame.Rect(x + 68, ry, 48, 38)
            pygame.draw.rect(surface, (247, 239, 219), key_rect, border_radius=9)
            pygame.draw.rect(surface, (166, 135, 92), key_rect, width=3, border_radius=9)
            key_font_size = 22 if len(letter) <= 2 else 15
            draw_text(surface, letter, get_font(key_font_size, bold=True), TEXT_MAIN, key_rect.center, center=True, shadow=False)

            label_surf = get_font(20, bold=True).render(label, True, TEXT_MAIN)
            label_rect = label_surf.get_rect(midleft=(label_x, ry + key_h // 2))
            surface.blit(label_surf, label_rect)

    def draw_right_panel(self, surface):
        draw_soft_shadow(surface, self.right_panel, radius=18, alpha=24, offset=(0, 7))
        panel = rounded_panel(self.right_panel.size, PANEL_FILL, PANEL_BORDER, radius=22, border_width=3, alpha=222)
        surface.blit(panel, self.right_panel.topleft)

        draw_text(surface, "CHAT", self.panel_title_font, TEXT_MAIN,
                  (self.right_panel.centerx, self.right_panel.y + 30), center=True, shadow=False)

        pygame.draw.rect(surface, INPUT_FILL, self.chat_box_rect, border_radius=14)
        pygame.draw.rect(surface, INPUT_BORDER, self.chat_box_rect, width=2, border_radius=14)

        y = self.chat_box_rect.y + 12
        sender_font = get_font(16, bold=True)
        body_font = get_font(16)
        for sender, message in self.get_chat_messages():
            p1_name, _ = self.get_player_names()
            sender_color = self.get_snake_palette(0)[0] if sender == p1_name else self.get_snake_palette(1)[0]
            draw_text(surface, f"{sender}:", sender_font, sender_color, (self.chat_box_rect.x + 10, y), shadow=False)
            sender_w = sender_font.size(f"{sender}: ")[0]
            text_rect = pygame.Rect(self.chat_box_rect.x + 10 + sender_w, y, self.chat_box_rect.width - 20 - sender_w, 34)
            draw_wrapped_text(surface, message, body_font, TEXT_MAIN, text_rect, center=False, line_spacing=2)
            y += 35
            if y > self.chat_box_rect.bottom - 28:
                break

        if getattr(self.client, "spectating", False):
            notice_rect = pygame.Rect(self.chat_input.input_rect.x, self.chat_input.input_rect.y, self.chat_input.input_rect.width + self.chat_input.send_rect.width + 8, self.chat_input.input_rect.height)
            pygame.draw.rect(surface, INPUT_FILL, notice_rect, border_radius=12)
            pygame.draw.rect(surface, INPUT_BORDER, notice_rect, width=2, border_radius=12)
            draw_text(surface, "Spectator mode: chat disabled", self.small_font, TEXT_SOFT, notice_rect.center, center=True, shadow=False)
        else:
            self.chat_input.draw(surface, self.arrow_scaled)

    def draw_footer(self, surface):
        draw_soft_shadow(surface, self.footer_rect, radius=18, alpha=24, offset=(0, 6))
        footer = rounded_panel(self.footer_rect.size, FOOTER_FILL, FOOTER_BORDER, radius=18, border_width=3, alpha=234)
        surface.blit(footer, self.footer_rect.topleft)

        footer_text = "Collect pies for +5 health. Walls and rocks each cost -10 health. Highest health wins when time ends."
        draw_wrapped_text(surface, footer_text, self.footer_font, TEXT_MAIN,
                          self.footer_rect.inflate(-30, -4), center=True, line_spacing=2)

    def draw_waiting_overlay(self, surface):
        if not getattr(self.client, "waiting_for_opponent", False) or getattr(self.client, "game_started", False):
            return

        w, h = surface.get_size()
        veil = pygame.Surface((w, h), pygame.SRCALPHA)
        veil.fill((0, 0, 0, 78))
        surface.blit(veil, (0, 0))

        box = pygame.Rect(0, 0, 520, 170)
        box.center = (w // 2, h // 2)
        draw_soft_shadow(surface, box, radius=26, alpha=42, offset=(0, 8))
        panel = rounded_panel(box.size, PANEL_FILL, PANEL_BORDER, radius=24, border_width=3, alpha=246)
        surface.blit(panel, box.topleft)

        draw_text(surface, "Waiting for other user to join", get_font(28, bold=True), TEXT_MAIN,
                  (box.centerx, box.y + 58), center=True, shadow=False)
        draw_text(surface, "The timer and game will begin once both players press Continue.", get_font(18), TEXT_SOFT,
                  (box.centerx, box.y + 104), center=True, shadow=False)

    def draw_game_over(self, surface):
        if not getattr(self.client, "game_over", False):
            return

        if not self.result_sound_played:
            stop_background_music()
            winner_raw = str(getattr(self.client, "winner", "draw") or "draw").lower()
            my_name = str(getattr(self.client, "username", "") or "").lower()
            try:
                if winner_raw != "draw" and my_name and winner_raw == my_name:
                    if self.winner_sound:
                        self.winner_sound.play()
                elif winner_raw != "draw":
                    if self.loser_sound:
                        self.loser_sound.play()
            except Exception:
                pass
            self.result_sound_played = True

        w, h = surface.get_size()
        veil = pygame.Surface((w, h), pygame.SRCALPHA)
        veil.fill((0, 0, 0, 96))
        surface.blit(veil, (0, 0))

        box = pygame.Rect(0, 0, 560, 330)
        box.center = (w // 2, h // 2)
        draw_soft_shadow(surface, box, radius=24, alpha=42, offset=(0, 8))
        panel = rounded_panel(box.size, PANEL_FILL, PANEL_BORDER, radius=22, border_width=3, alpha=248)
        surface.blit(panel, box.topleft)

        winner = getattr(self.client, "winner", "draw")
        final_health = list(getattr(self.client, "final_health", [0, 0]) or [0, 0])
        while len(final_health) < 2:
            final_health.append(0)
        p1_name, p2_name = self.get_player_names()

        stats = getattr(self.client, "final_stats", None)
        if not isinstance(stats, list) or len(stats) < 2:
            stats = self.get_state().get("stats", [{}, {}])
        if not isinstance(stats, list) or len(stats) < 2:
            stats = [{"pies": self.stats_tracker.pies[0], "obstacles": self.stats_tracker.collisions[0]},
                     {"pies": self.stats_tracker.pies[1], "obstacles": self.stats_tracker.collisions[1]}]

        p1_pies = int(stats[0].get("pies", 0) or 0)
        p2_pies = int(stats[1].get("pies", 0) or 0)
        p1_obs = int(stats[0].get("obstacles", 0) or 0)
        p2_obs = int(stats[1].get("obstacles", 0) or 0)

        draw_text(surface, "MATCH OVER", get_font(30, bold=True), TEXT_MAIN, (box.centerx, box.y + 42), center=True, shadow=False)
        draw_text(surface, f"Winner: {winner}", get_font(24, bold=True), TEXT_MAIN, (box.centerx, box.y + 86), center=True, shadow=False)

        y0 = box.y + 132
        draw_text(surface, f"{p1_name.upper()}: Health {final_health[0]}  |  Pies {p1_pies}  |  Obstacles {p1_obs}", get_font(18, bold=True), TEXT_SOFT, (box.centerx, y0), center=True, shadow=False)
        draw_text(surface, f"{p2_name.upper()}: Health {final_health[1]}  |  Pies {p2_pies}  |  Obstacles {p2_obs}", get_font(18, bold=True), TEXT_SOFT, (box.centerx, y0 + 38), center=True, shadow=False)

        self.gameover_lobby_btn.rect.center = (box.centerx - 90, box.bottom - 58)
        self.gameover_quit_btn.rect.center = (box.centerx + 90, box.bottom - 58)
        self.gameover_lobby_btn.draw(surface)
        self.gameover_quit_btn.draw(surface)
    # FULL DRAW
    # -----------------------------------------------------
    def draw(self, surface):
        state = self.get_state()
        surface.blit(self.get_background(surface), (0, 0))
        soften_background(surface)
        self.draw_header(surface, state.get("time_left", 0))
        self.draw_board(surface, state)
        self.draw_left_panel(surface, state)
        self.draw_right_panel(surface)
        self.draw_waiting_overlay(surface)
        self.draw_game_over(surface)


class GameOverPage:
    def __init__(self, client, stats_tracker):
        self.client = client
        self.stats_tracker = stats_tracker

        self.bg_original = load_image(ASSET_GAME_OVER_BG, alpha=False)
        if self.bg_original is None:
            self.bg_original = load_image(ASSET_BG, alpha=False)
        self.bg_surface = None
        self.last_bg_size = None

        self.title_font = get_title_font(78)
        self.heading_font = get_font(34, bold=True)
        self.medium_font = get_font(24, bold=True)
        self.winner_font = get_font(46, bold=True)
        self.card_name_font = get_font(24, bold=True)
        self.stat_font = get_font(18)
        self.value_font = get_font(18, bold=True)

        self.main_panel = pygame.Rect(0, 0, 10, 10)
        self.winner_panel = pygame.Rect(0, 0, 10, 10)
        self.left_card = pygame.Rect(0, 0, 10, 10)
        self.right_card = pygame.Rect(0, 0, 10, 10)

        self.btn_back = ActionButton((0, 0, 220, 54), "BACK TO LOBBY", "brown")
        self.btn_play = ActionButton((0, 0, 220, 54), "PLAY AGAIN", "green")
        self.result_sound_played = False
        self.winner_sound = safe_load_sound(WINNER_SOUND_FILE)
        self.loser_sound = safe_load_sound(LOSER_SOUND_FILE)

        self.sync_layout(*SCREEN.get_size())

    def sync_layout(self, width, height):
        panel_w = min(920, width - 120)
        panel_h = min(620, height - 80)
        self.main_panel.size = (panel_w, panel_h)
        self.main_panel.center = (width // 2, height // 2)

        winner_w = 340
        winner_h = 110
        self.winner_panel.size = (winner_w, winner_h)
        self.winner_panel.center = (self.main_panel.centerx, self.main_panel.y + 200)

        card_w = 300
        card_h = 250
        card_y = self.main_panel.y + 275
        gap = 56
        total_cards_w = card_w * 2 + gap
        cards_x = self.main_panel.centerx - total_cards_w // 2

        self.left_card = pygame.Rect(cards_x, card_y, card_w, card_h)
        self.right_card = pygame.Rect(cards_x + card_w + gap, card_y, card_w, card_h)

        btn_y = self.main_panel.bottom - 84
        self.btn_back.rect = pygame.Rect(self.main_panel.centerx - 240, btn_y, 220, 54)
        self.btn_play.rect = pygame.Rect(self.main_panel.centerx + 20, btn_y, 220, 54)

    def on_resize(self, width, height):
        self.sync_layout(width, height)
        self.bg_surface = None
        self.last_bg_size = None

    def get_background(self, surface):
        size = surface.get_size()
        if self.bg_original is None:
            bg = pygame.Surface(size)
            bg.fill(BG_FALLBACK)
            return bg

        if self.bg_surface is None or self.last_bg_size != size:
            self.bg_surface = scale_image_to_cover(self.bg_original, size)
            self.last_bg_size = size
        return self.bg_surface

    def handle_event(self, event):
        if self.btn_back.handle_event(event):
            launch_file("lobby.py")
            return "quit"

        if self.btn_play.handle_event(event):
            launch_file("snake_setup.py")
            return "quit"

        if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            launch_file("lobby.py")
            return "quit"

        return None

    def draw_player_card(self, surface, rect, name, snake_colors, health, pies, collisions, ribbon_color):
        draw_soft_shadow(surface, rect, radius=18, alpha=28, offset=(0, 8))
        card = rounded_panel(rect.size, PANEL_FILL, PANEL_BORDER, radius=24, border_width=3, alpha=238)
        surface.blit(card, rect.topleft)

        ribbon = pygame.Rect(0, 0, 166, 34)
        ribbon.midtop = (rect.centerx, rect.y - 3)
        ribbon_surf = pygame.Surface(ribbon.size, pygame.SRCALPHA)
        pygame.draw.rect(ribbon_surf, ribbon_color, ribbon_surf.get_rect(), border_radius=16)
        pygame.draw.rect(ribbon_surf, (215, 192, 152), ribbon_surf.get_rect(), width=2, border_radius=16)
        surface.blit(ribbon_surf, ribbon.topleft)
        draw_text(surface, name, self.card_name_font, SOFT_WHITE, ribbon.center, center=True, shadow=False)

        head = tuple(snake_colors.get("head", [94, 132, 74]))
        body = tuple(snake_colors.get("body", [132, 168, 103]))
        edge = tuple(max(0, c - 28) for c in body)
        light = tuple(min(255, c + 38) for c in body)

        centers = [
            (rect.centerx - 34, rect.y + 92),
            (rect.centerx - 12, rect.y + 80),
            (rect.centerx + 14, rect.y + 92),
            (rect.centerx + 40, rect.y + 80),
        ]
        for i, (cx, cy) in enumerate(centers):
            rad = 14 if i == len(centers) - 1 else 12
            base = head if i == len(centers) - 1 else body
            pygame.draw.circle(surface, edge, (cx, cy), rad + 2)
            pygame.draw.circle(surface, base, (cx, cy), rad)
            pygame.draw.circle(surface, light, (cx - 3, cy - 3), max(3, rad // 3))

        eye_y = centers[-1][1]
        pygame.draw.circle(surface, (46, 41, 36), (centers[-1][0] + 4, eye_y - 3), 2)
        pygame.draw.circle(surface, (46, 41, 36), (centers[-1][0] + 4, eye_y + 3), 2)

        stats = [
            ("Final Health", health),
            ("Pies Collected", pies),
            ("Obstacles Hit", collisions),
        ]
        start_y = rect.y + 145
        for idx, (label, value) in enumerate(stats):
            row_y = start_y + idx * 34
            draw_text(surface, label, self.stat_font, TEXT_MAIN, (rect.x + 28, row_y), shadow=False)
            value_text = str(value) if value is not None else "--"
            draw_text(surface, value_text, self.value_font, TEXT_MAIN, (rect.right - 28, row_y), shadow=False)
            if idx < len(stats) - 1:
                pygame.draw.line(surface, PANEL_DIVIDER, (rect.x + 26, row_y + 24), (rect.right - 26, row_y + 24), 1)

    def draw(self, surface):
        w, h = surface.get_size()
        surface.blit(self.get_background(surface), (0, 0))
        soften_background(surface)

        draw_soft_shadow(surface, self.main_panel, radius=32, alpha=50, offset=(0, 16))
        panel = rounded_panel(self.main_panel.size, PANEL_FILL, PANEL_BORDER, radius=28, border_width=3, alpha=214)
        surface.blit(panel, self.main_panel.topleft)

        draw_text(surface, "The Lebanese Arena", self.title_font, TEXT_MAIN,
                  (self.main_panel.centerx, self.main_panel.y + 78),
                  center=True, shadow=True, shadow_offset=(0, 4), shadow_alpha=85)
        draw_text(surface, "GAME OVER", self.heading_font, TEXT_MAIN,
                  (self.main_panel.centerx, self.main_panel.y + 145),
                  center=True, shadow=False)

        draw_soft_shadow(surface, self.winner_panel, radius=18, alpha=22, offset=(0, 6))
        winner_panel_surf = rounded_panel(self.winner_panel.size, (250, 242, 224), PANEL_BORDER, radius=24, border_width=3, alpha=234)
        surface.blit(winner_panel_surf, self.winner_panel.topleft)

        winner = str(getattr(self.client, "winner", "draw") or "draw").upper()
        winner_display = "DRAW" if winner == "DRAW" else winner
        draw_text(surface, "WINNER", self.medium_font if hasattr(self, 'medium_font') else get_font(24, bold=True), TEXT_MAIN,
                  (self.winner_panel.centerx, self.winner_panel.y + 28), center=True, shadow=False)
        draw_text(surface, winner_display, self.winner_font, GREEN if winner != "DRAW" else TEXT_MAIN,
                  (self.winner_panel.centerx, self.winner_panel.y + 72), center=True, shadow=False)

        final_health = getattr(self.client, "final_health", None) or [0, 0]
        while len(final_health) < 2:
            final_health.append(0)

        names = list(getattr(self.client, "player_names", ["Player 1", "Player 2"]))
        while len(names) < 2:
            names.append(f"Player {len(names)+1}")
        styles = getattr(self.client, "player_styles", {}) or {}
        stats = getattr(self.client, "final_stats", None)
        if not isinstance(stats, list) or len(stats) < 2:
            stats = [{"pies": self.stats_tracker.pies[0], "obstacles": self.stats_tracker.collisions[0]},
                     {"pies": self.stats_tracker.pies[1], "obstacles": self.stats_tracker.collisions[1]}]

        def colors_for(index):
            name = str(names[index])
            entry = styles.get(name) or styles.get(name.upper()) or styles.get(name.lower()) or {}
            colors = entry.get("snake_colors") if isinstance(entry, dict) else None
            if not isinstance(colors, dict):
                colors = DEFAULT_P1_COLORS if index == 0 else DEFAULT_P2_COLORS
            return colors

        p1_name, p2_name = str(names[0]).upper(), str(names[1]).upper()
        p1_colors, p2_colors = colors_for(0), colors_for(1)
        left_health, right_health = final_health[0], final_health[1]
        left_pies = int(stats[0].get("pies", 0) or 0)
        right_pies = int(stats[1].get("pies", 0) or 0)
        left_collisions = int(stats[0].get("obstacles", 0) or 0)
        right_collisions = int(stats[1].get("obstacles", 0) or 0)
        left_ribbon = tuple(p1_colors.get("body", DEFAULT_P1_COLORS["body"]))
        right_ribbon = tuple(p2_colors.get("body", DEFAULT_P2_COLORS["body"]))

        if not self.result_sound_played:
            stop_background_music()
            my_name = str(getattr(self.client, "username", "")).lower()
            winner_raw = str(getattr(self.client, "winner", "draw") or "draw").lower()
            try:
                if winner_raw != "draw" and my_name and winner_raw == my_name:
                    if self.winner_sound:
                        self.winner_sound.play()
                elif winner_raw != "draw":
                    if self.loser_sound:
                        self.loser_sound.play()
            except Exception:
                pass
            self.result_sound_played = True

        self.draw_player_card(surface, self.left_card, p1_name, p1_colors, left_health, left_pies, left_collisions, left_ribbon)
        self.draw_player_card(surface, self.right_card, p2_name, p2_colors, right_health, right_pies, right_collisions, right_ribbon)

        self.btn_back.draw(surface)
        self.btn_play.draw(surface)



# =========================================================
# APP BOOTSTRAP
# =========================================================
def read_selected_arena():
    try:
        with open("selected_arena.txt", "r", encoding="utf-8") as f:
            value = f.read().strip()
        return value if value in ARENA_BACKGROUNDS else "Beirut"
    except Exception:
        return "Beirut"


def build_client_for_game(arena):
    """
    Preview mode:
        python game.py Beirut

    Live mode after setup:
        python game.py Beirut <username> <server_ip> <port> <player_id> <opponent> <speed>

    IMPORTANT FIX:
    The lobby/arena/setup pages pass the same connected GameClient through builtins.
    The old code returned that shared client immediately, so setup_ready was never sent.
    That made the game page show the fake preview state (85/90 health, no movement).
    This version sends setup_ready for the shared client before returning it.
    """
    username = sys.argv[2] if len(sys.argv) > 2 else "Player 1"
    host = sys.argv[3] if len(sys.argv) > 3 else "127.0.0.1"
    port_arg = sys.argv[4] if len(sys.argv) > 4 else "5050"
    player_id = int(sys.argv[5]) if len(sys.argv) > 5 and str(sys.argv[5]).isdigit() else 1
    opponent = sys.argv[6] if len(sys.argv) > 6 else "Player 2"
    speed = sys.argv[7] if len(sys.argv) > 7 else "medium"

    def apply_identity(client):
        client.username = username
        client.opponent = opponent
        client.player_id = player_id
        client.arena = arena
        client.speed = speed
        client.player_names = [username, opponent] if player_id == 1 else [opponent, username]
        return client

    def send_ready_once(client):
        setup = load_player_setup()
        colors = setup.get("snake_colors", DEFAULT_P1_COLORS) if isinstance(setup, dict) else DEFAULT_P1_COLORS
        color_name = setup.get("snake_color_name", "") if isinstance(setup, dict) else ""
        # Avoid sending duplicate setup_ready every frame/re-entry.
        marker = (arena, username, str(player_id), str(speed), color_name)
        if getattr(client, "_last_setup_ready_marker", None) != marker:
            client._last_setup_ready_marker = marker
            client.player_styles = getattr(client, "player_styles", {}) or {}
            client.player_styles[username] = {
                "arena": arena,
                "snake_colors": colors,
                "snake_color_name": color_name,
                "speed": speed,
            }
            if hasattr(client, "setup_ready"):
                client.setup_ready(arena, colors, color_name, speed)
        return client

    shared = getattr(builtins, "PITHON_SHARED_CLIENT", None)
    if shared is not None and getattr(shared, "running", False):
        apply_identity(shared)
        send_ready_once(shared)
        return shared

    if GameClient is not None and len(sys.argv) >= 6:
        try:
            client = GameClient()
            apply_identity(client)
            client.connect(host, int(port_arg))
            client.join(username)
            client.start_receiver_thread()
            send_ready_once(client)
            return client
        except Exception as e:
            print(f"[WARN] Could not connect live client: {e}")
            return DummyClient(arena, username=username, opponent=opponent, player_id=player_id)

    if len(sys.argv) >= 4:
        player1 = sys.argv[2]
        player2 = sys.argv[3]
        player_id = int(sys.argv[4]) if len(sys.argv) >= 5 and str(sys.argv[4]).isdigit() else 1
        username = player1 if player_id == 1 else player2
        opponent = player2 if player_id == 1 else player1
        return DummyClient(arena, username=username, opponent=opponent, player_id=player_id)

    return DummyClient(arena)


def main():
    global SCREEN

    explicit_arena = sys.argv[1] if len(sys.argv) > 1 else read_selected_arena()
    resolved_arena = resolve_arena_name(explicit_arena)

    client = build_client_for_game(resolved_arena)
    page = BeirutArenaPage(client, resolved_arena)
    play_background_music()

    running = True
    while running:
        CLOCK.tick(FPS)
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
                break

            if event.type == pygame.VIDEORESIZE:
                new_w = max(MIN_WIDTH, event.w)
                new_h = max(MIN_HEIGHT, event.h)
                SCREEN = pygame.display.set_mode((new_w, new_h), pygame.RESIZABLE)
                page.on_resize(new_w, new_h)
                continue

            result = page.handle_event(event)
            if result == "quit":
                running = False
                break

        page.update()
        page.draw(SCREEN)
        pygame.display.flip()

    stop_background_music()

    if hasattr(client, "close"):
        try:
            client.close()
        except Exception:
            pass

    pygame.quit()
    sys.exit()


if __name__ == "__main__":
    main()
