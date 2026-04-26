import os
import sys
import subprocess
import runpy
import pygame

pygame.init()

FPS = 60
TITLE = "The Lebanese Arena - Choose Arena"
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


# =========================
# COLORS
# =========================
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

IMAGE_FRAME_FILL = (241, 233, 219)
IMAGE_FRAME_BORDER = (214, 188, 145)

GREEN = (126, 152, 80)
GREEN_DARK = (89, 111, 56)
GREEN_LIGHT = (160, 184, 112)

BROWN = (116, 63, 36)
BROWN_DARK = (82, 42, 23)
BROWN_LIGHT = (141, 85, 52)

OVERLAY_TOP = (255, 247, 220, 60)
OVERLAY_BOTTOM = (60, 42, 25, 45)

ARENA_FILE = "selected_arena.txt"
LOBBY_FILE = "lobby.py"
SNAKE_SETUP_FILE = "snake_setup.py"

ARENA_IMAGES = {
    "Beirut": "beirut.png",
    "Byblos": "byblos.png",
    "Baalbek": "baalbek.png",
    "Sidon": "sidon.png"
}


# =========================
# HELPERS
# =========================
def load_image(path, size=None, alpha=True):
    if not os.path.exists(path):
        raise FileNotFoundError(f"Missing asset: {path}")
    img = pygame.image.load(path)
    img = img.convert_alpha() if alpha else img.convert()
    if size:
        img = pygame.transform.smoothscale(img, size)
    return img


def safe_load_optional_image(path):
    if path and os.path.exists(path):
        return pygame.image.load(path).convert_alpha()
    return None


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


def write_selected_arena(arena_name):
    with open(ARENA_FILE, "w", encoding="utf-8") as arena_file:
        arena_file.write(arena_name)


def launch_file(filename, *args):
    target_path = os.path.join(os.path.dirname(__file__), filename)
    sys.argv = [target_path] + [str(arg) for arg in args]
    runpy.run_path(target_path, run_name="__main__")
    sys.exit()


# =========================
# BUTTON
# =========================
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
            base = tuple(max(0, c - 18) for c in base)
            dark = tuple(max(0, c - 24) for c in dark)

        btn = create_button_surface(self.rect.size, base, dark, light, pressed=self.pressed)
        surface.blit(btn, self.rect.topleft)

        draw_text(
            surface,
            self.text,
            self.font,
            SOFT_WHITE,
            self.rect.center,
            center=True,
            shadow=True,
            shadow_offset=(0, 2),
            shadow_alpha=120
        )


# =========================
# ARENA CARD
# =========================
class ArenaCard:
    def __init__(self, name, image_path=None):
        self.name = name
        self.rect = pygame.Rect(0, 0, 100, 100)
        self.hovered = False
        self.image_original = safe_load_optional_image(image_path)
        self.scaled_image = None
        self.last_image_size = None

    def set_rect(self, rect):
        self.rect = pygame.Rect(rect)

    def handle_event(self, event):
        if event.type == pygame.MOUSEMOTION:
            self.hovered = self.rect.collidepoint(event.pos)
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.rect.collidepoint(event.pos):
                return True
        return False

    def get_image_rect(self):
        return pygame.Rect(
            self.rect.x + 14,
            self.rect.y + 46,
            self.rect.width - 28,
            self.rect.height - 52
    )

    def draw_image_area(self, surface):
        image_rect = self.get_image_rect()
        frame = pygame.Surface(image_rect.size, pygame.SRCALPHA)
        pygame.draw.rect(frame, (*IMAGE_FRAME_FILL, 240), frame.get_rect(), border_radius=14)
        pygame.draw.rect(frame, IMAGE_FRAME_BORDER, frame.get_rect(), width=2, border_radius=14)
        surface.blit(frame, image_rect.topleft)
        if self.image_original:
            inner_rect = image_rect.inflate(-8, -8)

            if self.last_image_size != inner_rect.size:
                self.scaled_image = scale_image_to_cover(
                    self.image_original,
                    inner_rect.size,
                    vertical_focus=0.3
                )
                self.last_image_size = inner_rect.size
                
            clip_surface = pygame.Surface(inner_rect.size, pygame.SRCALPHA)
            pygame.draw.rect(
                clip_surface,
                (255, 255, 255, 255),
                clip_surface.get_rect(),
                border_radius=12
            )
            image_surface = pygame.Surface(inner_rect.size, pygame.SRCALPHA)
            image_surface.blit(self.scaled_image, (0, 0))
            image_surface.blit(clip_surface, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)
            surface.blit(image_surface, inner_rect.topleft)
        else:
            draw_text(
                surface,
                "Image not found",
                get_font(18, italic=True),
                (160, 136, 108),
                image_rect.center,
                center=True,
                shadow=False
            )

    def draw(self, surface, selected=False):
        draw_soft_shadow(surface, self.rect, radius=16, alpha=28, offset=(0, 8))

        fill = CARD_FILL_SELECTED if selected else CARD_FILL
        if self.hovered and not selected:
            fill = (249, 243, 233)

        card_surface = pygame.Surface(self.rect.size, pygame.SRCALPHA)
        pygame.draw.rect(card_surface, (*fill, 230), card_surface.get_rect(), border_radius=18)
        pygame.draw.rect(card_surface, CARD_BORDER, card_surface.get_rect(), width=2, border_radius=18)

        if selected:
            tint = pygame.Surface(self.rect.size, pygame.SRCALPHA)
            pygame.draw.rect(tint, CARD_SELECTED_TINT, tint.get_rect(), border_radius=18)
            card_surface.blit(tint, (0, 0))

        surface.blit(card_surface, self.rect.topleft)

        draw_text(
            surface,
            self.name,
            get_font(26, bold=True),
            TEXT_MAIN,
            (self.rect.centerx, self.rect.y + 26),
            center=True,
            shadow=False
        )

        self.draw_image_area(surface)


# =========================
# PAGE
# =========================
class ArenaSetupPage:
    def __init__(self, username=None, opponent=None, server_ip=None, port=None, player_id="1"):
        self.username = username or "Player 1"
        self.opponent = opponent or "Player 2"
        self.server_ip = server_ip or "127.0.0.1"
        self.port = str(port or "5050")
        self.player_id = str(player_id or "1")
        self.bg_original = load_image(ASSET_BG, alpha=False)
        self.bg = scale_image_to_cover(self.bg_original, (WIDTH, HEIGHT))
        self.last_bg_size = (WIDTH, HEIGHT)

        self.title_font = get_font(88, path=os.path.join("fonts", "Birthstone", "Birthstone-Regular.ttf"))
        self.heading_font = get_font(26, bold=True)

        self.panel_rect = pygame.Rect(0, 0, int(WIDTH * 0.78), int(HEIGHT * 0.88))

        self.cards = [
            ArenaCard("Beirut", ARENA_IMAGES["Beirut"]),
            ArenaCard("Byblos", ARENA_IMAGES["Byblos"]),
            ArenaCard("Baalbek", ARENA_IMAGES["Baalbek"]),
            ArenaCard("Sidon", ARENA_IMAGES["Sidon"]),
        ]
        self.selected_arena = "Beirut"

        self.back_btn = Button((0, 0, 220, 50), "BACK", "brown")
        self.continue_btn = Button((0, 0, 220, 50), "CONTINUE", "green")
        self.choosing_speed = False
        self.selected_speed = "medium"
        self.speed_buttons = [
            Button((0, 0, 180, 48), "SLOW", "brown"),
            Button((0, 0, 180, 48), "MEDIUM", "green"),
            Button((0, 0, 180, 48), "FAST", "blue"),
        ]

        self.sync_layout()

    def sync_layout(self):
        panel_w = min(max(1060, int(WIDTH * 0.78)), WIDTH - 90)
        panel_h = min(max(620, int(HEIGHT * 0.72)), HEIGHT - 110)
        self.panel_rect.size = (panel_w, panel_h)
        self.panel_rect.center = (WIDTH // 2, HEIGHT // 2 - 10)

        top_margin = 160
        side_margin = 40
        gap_x = 26
        gap_y = 12
        bottom_reserved = 102

        usable_h = self.panel_rect.height - top_margin - bottom_reserved
        card_w = (self.panel_rect.width - side_margin * 2 - gap_x) // 2

        base_card_h = (usable_h - gap_y) // 2
        card_h = base_card_h + 30

        positions = [
            (self.panel_rect.x + side_margin, self.panel_rect.y + top_margin),
            (self.panel_rect.x + side_margin + card_w + gap_x, self.panel_rect.y + top_margin),
            (self.panel_rect.x + side_margin, self.panel_rect.y + top_margin + card_h + gap_y),
            (self.panel_rect.x + side_margin + card_w + gap_x, self.panel_rect.y + top_margin + card_h + gap_y),
        ]

        for card, (x, y) in zip(self.cards, positions):
            card.set_rect((x, y, card_w, card_h))

        btn_y = self.panel_rect.bottom - 60
        button_gap = 75
        button_w = 220
        button_h = 50
        total_btn_w = button_w * 2 + button_gap
        start_x = self.panel_rect.centerx - total_btn_w // 2

        self.continue_btn.rect = pygame.Rect(start_x, btn_y, button_w, button_h)
        self.back_btn.rect = pygame.Rect(start_x + button_w + button_gap, btn_y, button_w, button_h)

        speed_w, speed_h, speed_gap = 180, 48, 22
        speed_total = speed_w * 3 + speed_gap * 2
        speed_x = self.panel_rect.centerx - speed_total // 2
        speed_y = self.panel_rect.centery + 70
        for i, btn in enumerate(self.speed_buttons):
            btn.rect = pygame.Rect(speed_x + i * (speed_w + speed_gap), speed_y, speed_w, speed_h)

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

    def handle_event(self, event):
        if self.choosing_speed:
            for speed_name, btn in zip(["slow", "medium", "fast"], self.speed_buttons):
                if btn.handle_event(event):
                    self.selected_speed = speed_name
                    write_selected_arena(self.selected_arena)
                    launch_file(SNAKE_SETUP_FILE, self.selected_arena, self.username, self.opponent, self.server_ip, self.port, self.player_id, self.selected_speed)
                    return "quit"
            return None

        for card in self.cards:
            if card.handle_event(event):
                self.selected_arena = card.name
                return None

        if self.continue_btn.handle_event(event):
            self.choosing_speed = True
            return None

        if self.back_btn.handle_event(event):
            launch_file(LOBBY_FILE)
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

        draw_text(
            surface,
            "CHOOSE YOUR ARENA",
            self.heading_font,
            TEXT_MAIN,
            (width // 2, self.panel_rect.y + 122),
            center=True,
            shadow=False
        )

    def draw(self, surface):
        surface.blit(self.get_background(surface), (0, 0))
        draw_vertical_overlay(surface, OVERLAY_TOP, OVERLAY_BOTTOM)

        draw_soft_shadow(surface, self.panel_rect, radius=30, alpha=50, offset=(0, 16))
        panel = rounded_panel(self.panel_rect.size, PANEL, PANEL_BORDER, radius=24, border_width=3, alpha=200)
        surface.blit(panel, self.panel_rect.topleft)

        self.draw_title(surface)

        for card in self.cards:
            card.draw(surface, selected=(card.name == self.selected_arena))

        self.continue_btn.draw(surface)
        self.back_btn.draw(surface)

        if self.choosing_speed:
            overlay = pygame.Surface(surface.get_size(), pygame.SRCALPHA)
            overlay.fill((20, 14, 10, 110))
            surface.blit(overlay, (0, 0))

            popup = pygame.Rect(0, 0, 680, 250)
            popup.center = surface.get_rect().center
            draw_soft_shadow(surface, popup, radius=30, alpha=60, offset=(0, 12))
            pop_surf = rounded_panel(popup.size, PANEL, PANEL_BORDER, radius=28, border_width=3, alpha=238)
            surface.blit(pop_surf, popup.topleft)

            draw_text(surface, "Choose Snake Speed", self.heading_font, TEXT_MAIN,
                      (popup.centerx, popup.y + 58), center=True, shadow=False)
            draw_text(surface, "This difficulty applies to both players.", get_font(19, bold=True), TEXT_SOFT,
                      (popup.centerx, popup.y + 95), center=True, shadow=False)

            for btn in self.speed_buttons:
                btn.draw(surface)


def main():
    start_background_music()
    global SCREEN, WIDTH, HEIGHT

    username = sys.argv[1] if len(sys.argv) > 1 else "Player 1"
    opponent = sys.argv[2] if len(sys.argv) > 2 else "Player 2"
    server_ip = sys.argv[3] if len(sys.argv) > 3 else "127.0.0.1"
    port = sys.argv[4] if len(sys.argv) > 4 else "5050"
    player_id = sys.argv[5] if len(sys.argv) > 5 else "1"
    page = ArenaSetupPage(username, opponent, server_ip, port, player_id)
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