import os
import sys
import pygame
import subprocess
import runpy
import builtins

pygame.init()

FPS = 60
WINDOW_TITLE = "The Lebanese Arena - Lobby"
ASSET_BG = "lobbybackground.png"

# Same window behavior as welcome page
display_info = pygame.display.Info()
WIDTH = max(1100, int(display_info.current_w * 0.90))
HEIGHT = max(700, int(display_info.current_h * 0.86))
SCREEN = pygame.display.set_mode((WIDTH, HEIGHT), pygame.RESIZABLE)
pygame.display.set_caption(WINDOW_TITLE)
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

# Match welcome page title colors
GOLD = (214, 191, 146)
DARK_GOLD = (142, 111, 68)

# Old lighter panel fill + new border color
PANEL = (248, 242, 233)
PANEL_BORDER = (218, 186, 132)

INPUT_TEXT = (125, 98, 72)
TEXT_MAIN = (106, 81, 58)
TEXT_SOFT = (125, 98, 72)
TITLE_SHADOW = (155, 124, 96)

GREEN = (126, 152, 80)
GREEN_DARK = (89, 111, 56)
GREEN_LIGHT = (160, 184, 112)

BLUE = (103, 137, 178)
BLUE_DARK = (71, 101, 143)
BLUE_LIGHT = (146, 176, 214)

BROWN = (116, 63, 36)
BROWN_DARK = (82, 42, 23)
BROWN_LIGHT = (141, 85, 52)

RED = (176, 96, 81)
RED_DARK = (126, 63, 50)
RED_LIGHT = (205, 132, 116)

OVERLAY_TOP = (255, 247, 220, 60)
OVERLAY_BOTTOM = (60, 42, 25, 45)

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


def scale_image_to_cover(img, target_size):
    target_w, target_h = target_size
    src_w, src_h = img.get_size()

    scale = max(target_w / src_w, target_h / src_h)
    scaled_w = int(src_w * scale)
    scaled_h = int(src_h * scale)
    scaled = pygame.transform.smoothscale(img, (scaled_w, scaled_h))

    x = (scaled_w - target_w) // 2
    y = (scaled_h - target_h) // 2
    return scaled.subsurface((x, y, target_w, target_h)).copy()


def get_font(size, bold=False, italic=False, path=None):
    if path and os.path.exists(path):
        return pygame.font.Font(path, size)

    preferred = ["Georgia", "Times New Roman", "Garamond", "Palatino Linotype"]
    for name in preferred:
        f = pygame.font.SysFont(name, size, bold=bold, italic=italic)
        if f:
            return f
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
        shadow_rect = shadow_surf.get_rect(center=rect.center if center else rect.topleft)

        if center:
            shadow_rect.center = (rect.centerx + shadow_offset[0], rect.centery + shadow_offset[1])
        else:
            shadow_rect.topleft = (rect.x + shadow_offset[0], rect.y + shadow_offset[1])

        surface.blit(shadow_surf, shadow_rect)

    surface.blit(text_surf, rect)
    return rect


def draw_wrapped_text(surface, text, font, color, rect, line_spacing=5, center=True):
    words = text.split()
    lines = []
    current = ""

    for word in words:
        test = word if not current else current + " " + word
        if font.size(test)[0] <= rect.width:
            current = test
        else:
            if current:
                lines.append(current)
            current = word

    if current:
        lines.append(current)

    total_height = len(lines) * font.get_height() + max(0, len(lines) - 1) * line_spacing
    start_y = rect.y + (rect.height - total_height) // 2

    for i, line in enumerate(lines):
        y = start_y + i * (font.get_height() + line_spacing)
        if center:
            draw_text(surface, line, font, color,
                      (rect.centerx, y + font.get_height() // 2),
                      center=True, shadow=False)
        else:
            draw_text(surface, line, font, color, (rect.x, y),
                      center=False, shadow=False)


def rounded_panel(size, fill, border, radius=20, border_width=3, alpha=200):
    surf = pygame.Surface(size, pygame.SRCALPHA)
    body = pygame.Rect(0, 0, *size)
    pygame.draw.rect(surf, (*fill, alpha), body, border_radius=radius)
    pygame.draw.rect(surf, border, body, width=border_width, border_radius=radius)
    return surf


def draw_soft_shadow(surface, rect, radius=26, alpha=45, offset=(0, 12)):
    shadow_surf = pygame.Surface((rect.width + radius * 2, rect.height + radius * 2), pygame.SRCALPHA)
    shadow_rect = pygame.Rect(radius, radius, rect.width, rect.height)
    pygame.draw.rect(shadow_surf, (0, 0, 0, alpha), shadow_rect, border_radius=24)
    shadow_surf = pygame.transform.smoothscale(
        shadow_surf, (shadow_surf.get_width(), shadow_surf.get_height())
    )
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


def soften_background(surface):
    width, height = surface.get_size()
    draw_vertical_overlay(surface, OVERLAY_TOP, OVERLAY_BOTTOM)

    veil = pygame.Surface((width, height), pygame.SRCALPHA)
    veil.fill((255, 248, 236, 13))
    surface.blit(veil, (0, 0))


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


# =========================
# BUTTON
# =========================
class Button:
    def __init__(self, rect, text, style="green"):
        self.rect = pygame.Rect(rect)
        self.text = text
        self.style = style
        self.hovered = False
        self.pressed = False
        self.font = get_font(20, bold=True)

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
        elif self.style == "blue":
            base, dark, light = BLUE, BLUE_DARK, BLUE_LIGHT
        elif self.style == "brown":
            base, dark, light = BROWN, BROWN_DARK, BROWN_LIGHT
        else:
            base, dark, light = RED, RED_DARK, RED_LIGHT

        if self.hovered:
            base = tuple(min(255, c + 10) for c in base)
            light = tuple(min(255, c + 10) for c in light)

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
# LOBBY SCREEN
# =========================
class LobbyScreen:
    def __init__(self, client):
        self.client = client

        self.bg_original = load_image(ASSET_BG, alpha=False)
        self.bg = scale_image_to_cover(self.bg_original, (WIDTH, HEIGHT))
        self.last_bg_size = (WIDTH, HEIGHT)

        self.title_font = get_font(
            88, path=os.path.join("fonts", "Birthstone", "Birthstone-Regular.ttf")
        )
        self.subtitle_font = get_font(26, bold=True)
        self.section_font = get_font(28, bold=True)
        self.info_font = get_font(22)
        self.text_font = get_font(20)
        self.small_font = get_font(17)
        self.player_font = get_font(22)

        self.selected_index = None
        self.show_spectate_panel = False
        self.spectate_selected_index = None
        self.spectate_panel_rect = pygame.Rect(0, 0, 10, 10)
        self.spectate_close_rect = pygame.Rect(0, 0, 10, 10)
        self.status_message = "Choose a player to challenge, or spectate."
        self.status_color = TEXT_SOFT

        self.players_rect = pygame.Rect(225, 225, 415, 390)
        self.actions_rect = pygame.Rect(680, 225, 415, 390)

        self.rebuild_layout()

    def rebuild_layout(self):
        gap = 40
        panel_w = 415
        panel_h = 390
        total_w = panel_w * 2 + gap
        start_x = (WIDTH - total_w) // 2
        start_y = 225

        self.players_rect = pygame.Rect(start_x, start_y, panel_w, panel_h)
        self.actions_rect = pygame.Rect(start_x + panel_w + gap, start_y, panel_w, panel_h)

        btn_x = self.actions_rect.x + 40
        btn_w = self.actions_rect.width - 80
        btn_h = 46
        btn_gap = 16
        btn_start_y = self.actions_rect.y + 92

        self.challenge_btn = Button((btn_x, btn_start_y, btn_w, btn_h), "CHALLENGE", "green")
        self.accept_btn = Button((btn_x, btn_start_y + (btn_h + btn_gap), btn_w, btn_h), "ACCEPT CHALLENGE", "blue")
        self.spectate_btn = Button((btn_x, btn_start_y + 2 * (btn_h + btn_gap), btn_w, btn_h), "SPECTATE", "brown")
        self.disconnect_btn = Button((btn_x, btn_start_y + 3 * (btn_h + btn_gap), btn_w, btn_h), "DISCONNECT", "red")

        panel_w = min(560, WIDTH - 140)
        panel_h = 330
        self.spectate_panel_rect = pygame.Rect((WIDTH - panel_w) // 2, 210, panel_w, panel_h)
        self.spectate_close_rect = pygame.Rect(self.spectate_panel_rect.centerx - 80, self.spectate_panel_rect.bottom - 62, 160, 42)

    def on_resize(self, new_width, new_height):
        global WIDTH, HEIGHT
        WIDTH, HEIGHT = new_width, new_height
        self.rebuild_layout()

    def get_background(self, surface):
        current_size = surface.get_size()
        if self.last_bg_size != current_size:
            self.bg = scale_image_to_cover(self.bg_original, current_size)
            self.last_bg_size = current_size
        return self.bg

    def get_players(self):
        return [p for p in self.client.player_list if p != self.client.username]

    def get_player_row_rects(self):
        row_rects = []

        row_x = self.players_rect.x + 24
        row_y = self.players_rect.y + 84
        row_w = self.players_rect.width - 48
        row_h = 56
        gap = 14

        for i, _ in enumerate(self.get_players()):
            row_rects.append(pygame.Rect(row_x, row_y + i * (row_h + gap), row_w, row_h))

        return row_rects

    def update(self):
        if self.client.last_error:
            self.status_message = self.client.last_error
            self.status_color = RED
            self.client.last_error = None

        if self.client.last_challenge_from:
            self.status_message = f"Challenge received from {self.client.last_challenge_from}"
            self.status_color = BLUE

        if getattr(self.client, "go_to_arena", False):
            return "arena"

        if getattr(self.client, "go_to_setup", False):
            return "setup"

        if self.client.game_started:
            return "game"

        return "lobby"

    def get_match_row_rects(self):
        matches = getattr(self.client, "matches", []) or []
        row_rects = []
        row_x = self.spectate_panel_rect.x + 36
        row_y = self.spectate_panel_rect.y + 88
        row_w = self.spectate_panel_rect.width - 72
        row_h = 54
        gap = 12
        for i, _ in enumerate(matches):
            row_rects.append(pygame.Rect(row_x, row_y + i * (row_h + gap), row_w, row_h))
        return row_rects

    def handle_event(self, event):
        if self.show_spectate_panel:
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if self.spectate_close_rect.collidepoint(event.pos):
                    self.show_spectate_panel = False
                    return None
                matches = getattr(self.client, "matches", []) or []
                for i, row_rect in enumerate(self.get_match_row_rects()):
                    if row_rect.collidepoint(event.pos):
                        self.spectate_selected_index = i
                        match_id = matches[i].get("id", "current") if isinstance(matches[i], dict) else "current"
                        if hasattr(self.client, "spectate_match"):
                            self.client.spectate_match(match_id)
                        self.status_message = "Opening spectator view..."
                        self.status_color = BROWN
                        return None
            if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                self.show_spectate_panel = False
            return None

        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            for i, row_rect in enumerate(self.get_player_row_rects()):
                if row_rect.collidepoint(event.pos):
                    self.selected_index = i
                    break

        if self.challenge_btn.handle_event(event):
            players = self.get_players()
            if self.selected_index is not None and 0 <= self.selected_index < len(players):
                target = players[self.selected_index]
                self.client.challenge(target)
                self.status_message = f"Challenge sent to {target}"
                self.status_color = GREEN
            else:
                self.status_message = "Please select a player first."
                self.status_color = RED

        if self.accept_btn.handle_event(event):
            if self.client.last_challenge_from:
                self.client.accept(self.client.last_challenge_from)
                self.status_message = f"Accepted challenge from {self.client.last_challenge_from}"
                self.status_color = BLUE
            else:
                self.status_message = "No incoming challenge to accept."
                self.status_color = RED

        if self.spectate_btn.handle_event(event):
            if hasattr(self.client, "request_matches"):
                self.client.request_matches()
            else:
                self.client.spectate()
            self.show_spectate_panel = True
            self.spectate_selected_index = None
            self.status_message = "Choose a live match to watch."
            self.status_color = BROWN

        if self.disconnect_btn.handle_event(event):
            self.client.close()
            return "quit"

        return None

    def draw_title(self, surface):
        width, _ = surface.get_size()
        title_text = "The Lebanese Arena"

        title_surf = self.title_font.render(title_text, True, TEXT_MAIN)
        title_shadow = self.title_font.render(title_text, True, TITLE_SHADOW)
        title_shadow.set_alpha(120)

        title_rect = title_surf.get_rect(center=(width // 2, 80))
        surface.blit(title_shadow, (title_rect.x + 2, title_rect.y + 2))
        surface.blit(title_surf, title_rect)
        surface.blit(title_surf, (title_rect.x + 1, title_rect.y))

        lobby_surf = self.subtitle_font.render("LOBBY", True, TEXT_MAIN)
        lobby_shadow = self.subtitle_font.render("LOBBY", True, TITLE_SHADOW)
        lobby_shadow.set_alpha(120)

        lobby_rect = lobby_surf.get_rect(center=(width // 2, 132))
        surface.blit(lobby_shadow, (lobby_rect.x + 2, lobby_rect.y + 2))
        surface.blit(lobby_surf, lobby_rect)
        surface.blit(lobby_surf, (lobby_rect.x + 1, lobby_rect.y))

    def draw_logged_in(self, surface):
        draw_text(
            surface,
            f"LOGGED IN AS: {self.client.username}",
            self.info_font,
            TEXT_MAIN,
            (self.players_rect.x, 188),
            center=False,
            shadow=False
        )

    def draw_players_panel(self, surface):
        draw_soft_shadow(surface, self.players_rect, radius=26, alpha=45, offset=(0, 12))
        panel = rounded_panel(self.players_rect.size, PANEL, PANEL_BORDER, radius=20, border_width=3, alpha=200)
        surface.blit(panel, self.players_rect.topleft)

        draw_text(
            surface,
            "Online Players",
            self.section_font,
            TEXT_MAIN,
            (self.players_rect.centerx, self.players_rect.y + 42),
            center=True,
            shadow=False
        )

        players = self.get_players()
        if not players:
            draw_text(
                surface,
                "No other players online yet.",
                self.text_font,
                TEXT_SOFT,
                self.players_rect.center,
                center=True,
                shadow=False
            )
            return

        row_rects = self.get_player_row_rects()
        for i, player in enumerate(players):
            row_rect = row_rects[i]
            row_surf = pygame.Surface(row_rect.size, pygame.SRCALPHA)

            if self.selected_index == i:
                pygame.draw.rect(row_surf, (247, 236, 208, 190), row_surf.get_rect(), border_radius=12)
                pygame.draw.rect(row_surf, DARK_GOLD, row_surf.get_rect(), width=2, border_radius=12)
            else:
                pygame.draw.rect(row_surf, (243, 238, 230, 190), row_surf.get_rect(), border_radius=12)
                pygame.draw.rect(row_surf, (229, 209, 174), row_surf.get_rect(), width=1, border_radius=12)

            surface.blit(row_surf, row_rect.topleft)

            draw_text(
                surface,
                player.upper(),
                self.player_font,
                TEXT_MAIN,
                (row_rect.x + 18, row_rect.y + 15),
                center=False,
                shadow=False
            )

    def draw_actions_panel(self, surface):
        draw_soft_shadow(surface, self.actions_rect, radius=26, alpha=45, offset=(0, 12))
        panel = rounded_panel(self.actions_rect.size, PANEL, PANEL_BORDER, radius=20, border_width=3, alpha=200)
        surface.blit(panel, self.actions_rect.topleft)

        draw_text(
            surface,
            "Actions",
            self.section_font,
            TEXT_MAIN,
            (self.actions_rect.centerx, self.actions_rect.y + 42),
            center=True,
            shadow=False
        )

        self.challenge_btn.draw(surface)
        self.accept_btn.draw(surface)
        self.spectate_btn.draw(surface)
        self.disconnect_btn.draw(surface)

        status_area = pygame.Rect(
            self.actions_rect.x + 30,
            self.actions_rect.bottom - 70,
            self.actions_rect.width - 60,
            40
        )
        draw_wrapped_text(
            surface,
            self.status_message,
            self.small_font,
            self.status_color,
            status_area,
            line_spacing=4,
            center=True
        )

    def draw_spectate_panel(self, surface):
        if not self.show_spectate_panel:
            return
        veil = pygame.Surface(surface.get_size(), pygame.SRCALPHA)
        veil.fill((35, 24, 14, 86))
        surface.blit(veil, (0, 0))

        rect = self.spectate_panel_rect
        draw_soft_shadow(surface, rect, radius=28, alpha=65, offset=(0, 12))
        panel = rounded_panel(rect.size, PANEL, PANEL_BORDER, radius=22, border_width=3, alpha=232)
        surface.blit(panel, rect.topleft)

        draw_text(surface, "Live Matches", self.section_font, TEXT_MAIN, (rect.centerx, rect.y + 42), center=True, shadow=False)
        matches = getattr(self.client, "matches", []) or []
        if not matches:
            draw_text(surface, "No match is happening right now.", self.text_font, TEXT_SOFT, rect.center, center=True, shadow=False)
        else:
            rows = self.get_match_row_rects()
            for i, match in enumerate(matches):
                row_rect = rows[i]
                hovered = row_rect.collidepoint(pygame.mouse.get_pos())
                selected = self.spectate_selected_index == i
                row_surf = pygame.Surface(row_rect.size, pygame.SRCALPHA)
                fill = (224, 206, 172, 220) if (hovered or selected) else (243, 238, 230, 210)
                border = DARK_GOLD if (hovered or selected) else (229, 209, 174)
                pygame.draw.rect(row_surf, fill, row_surf.get_rect(), border_radius=13)
                pygame.draw.rect(row_surf, border, row_surf.get_rect(), width=2, border_radius=13)
                surface.blit(row_surf, row_rect.topleft)
                players = match.get("players", ["Player 1", "Player 2"]) if isinstance(match, dict) else ["Player 1", "Player 2"]
                arena = match.get("arena", "Arena") if isinstance(match, dict) else "Arena"
                label = f"{str(players[0]).upper()}  vs  {str(players[1]).upper()}" if len(players) >= 2 else "LIVE MATCH"
                draw_text(surface, label, self.player_font, TEXT_MAIN, (row_rect.x + 18, row_rect.y + 10), shadow=False)
                draw_text(surface, arena, self.small_font, TEXT_SOFT, (row_rect.x + 20, row_rect.y + 33), shadow=False)

        close_hover = self.spectate_close_rect.collidepoint(pygame.mouse.get_pos())
        close_base = BROWN_DARK if close_hover else BROWN
        surf = create_button_surface(self.spectate_close_rect.size, close_base, BROWN_DARK, BROWN_LIGHT)
        surface.blit(surf, self.spectate_close_rect.topleft)
        draw_text(surface, "CANCEL", self.small_font, SOFT_WHITE, self.spectate_close_rect.center, center=True, shadow=True, shadow_offset=(0, 2), shadow_alpha=100)

    def draw(self, surface):
        surface.blit(self.get_background(surface), (0, 0))
        soften_background(surface)

        self.draw_title(surface)
        self.draw_logged_in(surface)
        self.draw_players_panel(surface)
        self.draw_actions_panel(surface)
        self.draw_spectate_panel(surface)


# =========================
# CLIENT SETUP
# =========================
class DummyClient:
    """Only used if you open lobby.py directly for preview."""
    def __init__(self, username="Preview"):
        self.username = username
        self.player_list = [username]
        self.last_error = None
        self.last_challenge_from = None
        self.game_started = False
        self.go_to_setup = False
        self.go_to_arena = False
        self.opponent = None
        self.connected = True

    def challenge(self, target):
        print(f"Challenge sent to {target}")

    def accept(self, target):
        print(f"Accepted challenge from {target}")

    def spectate(self):
        print("Spectate requested")

    def close(self):
        print("Disconnected")


def build_client_from_args():
    """
    Real mode, launched by welcome_page.py:
        python lobby.py <username> <server_ip> <port>

    Preview mode, opened directly:
        python lobby.py
    """
    shared = getattr(builtins, "PITHON_SHARED_CLIENT", None)
    if shared is not None and getattr(shared, "running", False):
        return shared

    if len(sys.argv) < 4:
        return DummyClient()

    username = sys.argv[1].strip()
    server_ip = sys.argv[2].strip()
    port = int(sys.argv[3])

    try:
        from client import GameClient

        client = GameClient()
        client.connect(server_ip, port)
        client.join(username)
        client.start_receiver_thread()
        return client

    except Exception as e:
        # If server is not running, show username and error instead of fake Ali/Maya/Karim/Nour.
        client = DummyClient(username)
        client.last_error = f"Could not connect to server: {e}"
        return client


def main():
    start_background_music()
    global SCREEN, WIDTH, HEIGHT

    client = build_client_from_args()
    launch_username = sys.argv[1].strip() if len(sys.argv) >= 4 else getattr(client, "username", "Preview")
    launch_host = sys.argv[2].strip() if len(sys.argv) >= 4 else "127.0.0.1"
    launch_port = sys.argv[3].strip() if len(sys.argv) >= 4 else "5050"
    lobby = LobbyScreen(client)
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
                lobby.on_resize(WIDTH, HEIGHT)
                continue

            result = lobby.handle_event(event)
            if result == "quit":
                running = False
                break

        state = lobby.update()

        # Challenger chooses arena and difficulty. Accepter skips arena and goes straight to snake setup.
        if state == "arena":
            opponent = getattr(client, "opponent", "Player 2") or "Player 2"
            player_id = str(getattr(client, "player_id", 1) or 1)
            target_path = os.path.join(os.path.dirname(__file__), "arena_setup.py")
            builtins.PITHON_SHARED_CLIENT = client
            sys.argv = [target_path, launch_username, opponent, launch_host, launch_port, player_id]
            runpy.run_path(target_path, run_name="__main__")
            sys.exit()

        if state == "setup":
            opponent = getattr(client, "opponent", "Player 2") or "Player 2"
            player_id = str(getattr(client, "player_id", 2) or 2)
            arena = getattr(client, "arena", "Beirut")
            target_path = os.path.join(os.path.dirname(__file__), "snake_setup.py")
            speed = getattr(client, "speed", "medium")
            builtins.PITHON_SHARED_CLIENT = client
            sys.argv = [target_path, arena, launch_username, opponent, launch_host, launch_port, player_id, str(speed)]
            runpy.run_path(target_path, run_name="__main__")
            sys.exit()

        if state == "game":
            arena = getattr(client, "arena", "Beirut")
            player_id = str(getattr(client, "player_id", 1) or 1)
            target_path = os.path.join(os.path.dirname(__file__), "game.py")
            builtins.PITHON_SHARED_CLIENT = client
            sys.argv = [target_path, arena, launch_username, launch_host, launch_port, player_id]
            runpy.run_path(target_path, run_name="__main__")
            sys.exit()

        lobby.draw(SCREEN)
        pygame.display.flip()

    if hasattr(client, "close"):
        try:
            client.close()
        except Exception:
            pass

    pygame.quit()
    sys.exit()


if __name__ == "__main__":
    main()
