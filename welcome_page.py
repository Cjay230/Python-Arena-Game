import os
import sys
import pygame
import subprocess
import runpy
import socket
import json

pygame.init()

FPS = 60
TITLE = "The Lebanese Arena"
ASSET_BG = "background.png"

# Fill most of the screen while staying a normal window
_display_info = pygame.display.Info()
WIDTH = max(1100, int(_display_info.current_w * 0.90))
HEIGHT = max(700, int(_display_info.current_h * 0.86))
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
SOFT_WHITE = (244, 232, 200)
TEXT_MAIN = (106, 81, 58)
TITLE_SHADOW = (155, 124, 96)
PANEL = (245, 239, 224)
PANEL_BORDER = (222, 188, 126)
INPUT_FILL = (244, 231, 198)
INPUT_BORDER = (226, 194, 132)
INPUT_TEXT = (132, 104, 75)
INPUT_PLACEHOLDER = (176, 149, 116)
GREEN = (126, 152, 80)
GREEN_DARK = (89, 111, 56)
GREEN_LIGHT = (160, 184, 112)
BROWN = (116, 63, 36)
BROWN_DARK = (82, 42, 23)
BROWN_LIGHT = (141, 85, 52)
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
        shadow_rect = shadow_surf.get_rect(center=rect.center if center else rect.topleft)
        if center:
            shadow_rect.center = (rect.centerx + shadow_offset[0], rect.centery + shadow_offset[1])
        else:
            shadow_rect.topleft = (rect.x + shadow_offset[0], rect.y + shadow_offset[1])
        surface.blit(shadow_surf, shadow_rect)

    surface.blit(text_surf, rect)
    return rect


def rounded_panel(size, fill, border, radius=18, border_width=3, alpha=212):
    surf = pygame.Surface(size, pygame.SRCALPHA)
    body = pygame.Rect(0, 0, *size)
    pygame.draw.rect(surf, (*fill, alpha), body, border_radius=radius)
    pygame.draw.rect(surf, border, body, width=border_width, border_radius=radius)
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


def check_username_available(server_ip, port, username, timeout=3.0):
    """Connect briefly and ask the server whether this username is available.
    The welcome page uses this to stop taken usernames before opening the lobby.
    """
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(timeout)
    try:
        sock.connect((server_ip, port))
        payload = {"type": "check_username", "username": username}
        sock.sendall((json.dumps(payload) + "\n").encode("utf-8"))
        buffer = ""
        while "\n" not in buffer:
            chunk = sock.recv(4096).decode("utf-8")
            if not chunk:
                return False, "Server closed the connection"
            buffer += chunk
        line = buffer.split("\n", 1)[0].strip()
        msg = json.loads(line) if line else {}
        if msg.get("type") == "username_ok":
            return True, ""
        if msg.get("type") == "username_taken":
            return False, "Username already taken. Please choose another name."
        return False, msg.get("message", "Could not validate username")
    except Exception as exc:
        return False, f"Connection failed: {exc}"
    finally:
        try:
            sock.close()
        except OSError:
            pass


class TextInput:
    def __init__(self, rect, placeholder="", max_len=18, font_size=24, digits_only=False):
        self.rect = pygame.Rect(rect)
        self.placeholder = placeholder
        self.text = ""
        self.active = False
        self.max_len = max_len
        self.font = get_font(font_size)
        self.cursor_visible = True
        self.cursor_timer = 0
        self.digits_only = digits_only
        self.padding_x = 18

    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            self.active = self.rect.collidepoint(event.pos)
            self.cursor_timer = 0
            self.cursor_visible = True

        if event.type == pygame.KEYDOWN and self.active:
            if event.key == pygame.K_RETURN:
                return "submit"
            if event.key == pygame.K_TAB:
                return "submit"
            if event.key == pygame.K_BACKSPACE:
                self.text = self.text[:-1]
                return None

            char = event.unicode
            if not char or char in ["\t", "\r", "\n"] or not char.isprintable():
                return None
            if self.digits_only and not char.isdigit():
                return None
            if len(self.text) < self.max_len:
                self.text += char
        return None

    def update(self):
        self.cursor_timer += 1
        if self.cursor_timer >= 30:
            self.cursor_timer = 0
            self.cursor_visible = not self.cursor_visible

    def draw(self, surface):
        outer = pygame.Surface((self.rect.width, self.rect.height), pygame.SRCALPHA)
        pygame.draw.rect(outer, INPUT_FILL, outer.get_rect(), border_radius=14)
        pygame.draw.rect(outer, INPUT_BORDER, outer.get_rect(), width=2, border_radius=14)

        inner = pygame.Rect(8, 8, self.rect.width - 16, self.rect.height - 16)
        pygame.draw.rect(outer, (251, 242, 217, 120), inner, width=2, border_radius=10)
        surface.blit(outer, self.rect.topleft)

        show_placeholder = (not self.text) and (not self.active)
        display_text = self.placeholder if show_placeholder else self.text
        color = INPUT_PLACEHOLDER if show_placeholder else INPUT_TEXT

        text_surf = self.font.render(display_text, True, color)
        text_rect = text_surf.get_rect()
        text_rect.midleft = (self.rect.x + self.padding_x, self.rect.centery)
        surface.blit(text_surf, text_rect)

        if self.active and self.cursor_visible:
            cursor_x = text_rect.right + 3 if self.text else self.rect.x + self.padding_x
            cursor_top = self.rect.centery - 12
            cursor_bottom = self.rect.centery + 12
            pygame.draw.line(surface, (140, 112, 86), (cursor_x, cursor_top), (cursor_x, cursor_bottom), 2)


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
        draw_text(surface, self.text, self.font, SOFT_WHITE, self.rect.center,
                  center=True, shadow=True, shadow_offset=(0, 2), shadow_alpha=120)


class WelcomePage:
    def __init__(self):
        self.bg_original = load_image(ASSET_BG, alpha=False)
        self.bg = scale_image_to_cover(self.bg_original, (WIDTH, HEIGHT))
        self.last_bg_size = (WIDTH, HEIGHT)

        self.title_font = get_font(120, path=os.path.join("fonts", "Birthstone", "Birthstone-Regular.ttf"))
        self.label_font = get_font(24, bold=True)
        self.message_font = get_font(20, bold=True)
        self.welcome_font = get_font(32, bold=True)

        # Smaller and slightly lower than before
        self.panel_rect = pygame.Rect(0, 0, 530, 320)
        self.panel_rect.center = (WIDTH // 2, HEIGHT // 2 + 38)

        self.username_box = TextInput((0, 0, 450, 48), "Enter Username...", max_len=18)
        self.server_ip_box = TextInput((0, 0, 326, 48), "Enter Server IP...", max_len=32)
        self.port_box = TextInput((0, 0, 114, 48), "Port", max_len=5, digits_only=True)
        self.input_boxes = [self.username_box, self.server_ip_box, self.port_box]

        self.start_button = Button((0, 0, 450, 44), "START GAME", "green")
        self.quit_button = Button((0, 0, 450, 44), "QUIT", "brown")

        self.message = ""
        self.message_color = (120, 50, 35)
        self.sync_layout()

    def sync_layout(self):
        self.panel_rect.center = (WIDTH // 2, HEIGHT // 2 + 38)
        left = self.panel_rect.x + 40
        top = self.panel_rect.y

        self.username_box.rect.topleft = (left, top + 52)
        self.server_ip_box.rect.topleft = (left, top + 148)
        self.port_box.rect.topleft = (left + 336, top + 148)
        self.start_button.rect.topleft = (left, top + 210)
        self.quit_button.rect.topleft = (left, top + 262)

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

    def activate_only(self, active_index):
        for idx, box in enumerate(self.input_boxes):
            box.active = (idx == active_index)
            if idx == active_index:
                box.cursor_timer = 0
                box.cursor_visible = True

    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            clicked_any = False
            for idx, box in enumerate(self.input_boxes):
                if box.rect.collidepoint(event.pos):
                    self.activate_only(idx)
                    clicked_any = True
                    break
            if not clicked_any:
                for box in self.input_boxes:
                    box.active = False

        submit_requested = False
        for idx, box in enumerate(self.input_boxes):
            result = box.handle_event(event)
            if result == "submit":
                if idx < len(self.input_boxes) - 1:
                    self.activate_only(idx + 1)
                else:
                    submit_requested = True

        if submit_requested:
            return self.try_start()

        if self.start_button.handle_event(event):
            return self.try_start()

        if self.quit_button.handle_event(event):
            return "quit"

        return None

    def try_start(self):
        username = self.username_box.text.strip()
        server_ip = self.server_ip_box.text.strip()
        port_text = self.port_box.text.strip()

        if not username:
            self.message = "Please enter a username"
            self.message_color = (145, 62, 48)
            return None
        if not server_ip:
            self.message = "Please enter the server IP"
            self.message_color = (145, 62, 48)
            return None
        if not port_text:
            self.message = "Please enter the port number"
            self.message_color = (145, 62, 48)
            return None

        try:
            port = int(port_text)
            if not (1 <= port <= 65535):
                raise ValueError
        except ValueError:
            self.message = "Port must be between 1 and 65535"
            self.message_color = (145, 62, 48)
            return None

        self.message = f"Checking username on {server_ip}:{port}..."
        self.message_color = (65, 100, 61)
        ok, error = check_username_available(server_ip, port, username)
        if not ok:
            self.message = error or "Username already taken. Please choose another name."
            self.message_color = (145, 62, 48)
            return None

        self.message = f"Username accepted. Opening lobby..."
        self.message_color = (65, 100, 61)
        return {"username": username, "server_ip": server_ip, "port": port}

    def update(self):
        for box in self.input_boxes:
            box.update()

    def draw_title(self, surface):
        width, _ = surface.get_size()
        title_text = "The Lebanese Arena"

        title_surf = self.title_font.render(title_text, True, TEXT_MAIN)
        title_shadow = self.title_font.render(title_text, True, TITLE_SHADOW)
        title_shadow.set_alpha(120)

        title_rect = title_surf.get_rect(center=(width // 2, 132))
        surface.blit(title_shadow, (title_rect.x + 2, title_rect.y + 2))
        surface.blit(title_surf, title_rect)
        surface.blit(title_surf, (title_rect.x + 1, title_rect.y))

        welcome_surf = self.welcome_font.render("WELCOME", True, TEXT_MAIN)
        welcome_shadow = self.welcome_font.render("WELCOME", True, TITLE_SHADOW)
        welcome_shadow.set_alpha(120)

        welcome_rect = welcome_surf.get_rect(center=(width // 2, 220))
        surface.blit(welcome_shadow, (welcome_rect.x + 2, welcome_rect.y + 2))
        surface.blit(welcome_surf, welcome_rect)
        surface.blit(welcome_surf, (welcome_rect.x + 1, welcome_rect.y))

    def draw(self, surface):
        width, _ = surface.get_size()
        surface.blit(self.get_background(surface), (0, 0))
        draw_vertical_overlay(surface, OVERLAY_TOP, OVERLAY_BOTTOM)
        self.draw_title(surface)

        draw_soft_shadow(surface, self.panel_rect, radius=28, alpha=50, offset=(0, 16))
        panel = rounded_panel(self.panel_rect.size, PANEL, PANEL_BORDER, radius=20, border_width=3, alpha=212)
        surface.blit(panel, self.panel_rect.topleft)

        draw_text(surface, "Enter Your Username:", self.label_font, TEXT_MAIN,
                  (self.panel_rect.centerx, self.panel_rect.y + 28), center=True, shadow=False)
        self.username_box.draw(surface)

        draw_text(surface, "Server Connection:", self.label_font, TEXT_MAIN,
                  (self.panel_rect.centerx, self.panel_rect.y + 120), center=True, shadow=False)
        self.server_ip_box.draw(surface)
        self.port_box.draw(surface)

        self.start_button.draw(surface)
        self.quit_button.draw(surface)

        if self.message:
            draw_text(surface, self.message, self.message_font, self.message_color,
                      (width // 2, self.panel_rect.bottom + 34), center=True, shadow=False)


def main():
    start_background_music()
    global SCREEN, WIDTH, HEIGHT

    page = WelcomePage()
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
                break

            elif isinstance(result, dict):
                print(f"Connecting as {result['username']} to {result['server_ip']}:{result['port']}")

                target_path = os.path.join(os.path.dirname(__file__), "lobby.py")
                sys.argv = [target_path, result["username"], result["server_ip"], str(result["port"])]
                runpy.run_path(target_path, run_name="__main__")
                sys.exit()

        page.update()
        page.draw(SCREEN)
        pygame.display.flip()

    pygame.quit()
    sys.exit()


if __name__ == "__main__":
    main()
