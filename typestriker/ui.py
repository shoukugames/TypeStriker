"""Fonts, text helpers and the small UI pieces shared by every screen."""
import functools
import os
import sys

import pygame

from .art import shade
from .i18n import LANGUAGE_NAMES, get_language, t


def resource_path(*parts):
    """Find a bundled file both from source and inside a PyInstaller build."""
    base = getattr(sys, "_MEIPASS", os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    return os.path.join(base, *parts)


@functools.lru_cache(maxsize=64)
def font(size):
    return pygame.font.Font(None, size)


JAPANESE_FONT = ("assets", "fonts", "MPLUS1p-Bold.ttf")
JAPANESE_SCALE = 0.72  # pygame's built-in font draws smaller than its nominal size


@functools.lru_cache(maxsize=64)
def japanese_font(size):
    try:
        return pygame.font.Font(resource_path(*JAPANESE_FONT), max(8, int(size * JAPANESE_SCALE)))
    except (OSError, pygame.error):
        return font(size)


def font_for(string, size):
    """The right font for this text. Japanese characters all sit above U+2E80."""
    if any(ord(char) >= 0x2E80 for char in string):
        return japanese_font(size)
    return font(size)


def text(surf, string, size, color, pos, anchor="topleft", shadow=True):
    chosen = font_for(string, size)
    image = chosen.render(string, True, color)
    rect = image.get_rect(**{anchor: pos})
    if shadow:
        dark = chosen.render(string, True, (0, 0, 0))
        dark.set_alpha(170)
        surf.blit(dark, rect.move(2, 2))
    surf.blit(image, rect)
    return rect


@functools.lru_cache(maxsize=512)
def glyph(char, size, color):
    return font(size).render(char, True, color)


def panel(surf, rect, color=(8, 12, 28), alpha=190, border=(90, 130, 190), radius=10, width=1):
    rect = pygame.Rect(rect)
    layer = pygame.Surface(rect.size, pygame.SRCALPHA)
    pygame.draw.rect(layer, (*color, alpha), layer.get_rect(), border_radius=radius)
    if border:
        pygame.draw.rect(layer, (*border, 220), layer.get_rect(), width, border_radius=radius)
    surf.blit(layer, rect)
    return rect


def vertical_gradient(size, top, bottom):
    low = pygame.Surface((1, 64))
    for y in range(64):
        t = y / 63
        low.set_at((0, y), tuple(int(top[i] + (bottom[i] - top[i]) * t) for i in range(3)))
    return pygame.transform.smoothscale(low, size)


@functools.lru_cache(maxsize=16)
def fancy_title(string, size, top=(255, 255, 255), bottom=(70, 170, 255), glow=(30, 120, 255)):
    """Big text with a metallic gradient and a soft glow."""
    chosen = font_for(string, size)
    mask = chosen.render(string, True, (255, 255, 255))
    w, h = mask.get_size()
    pad = 34
    out = pygame.Surface((w + pad * 2, h + pad * 2), pygame.SRCALPHA)
    halo = chosen.render(string, True, glow)
    layer = pygame.Surface(out.get_size(), pygame.SRCALPHA)
    layer.blit(halo, (pad, pad))
    for factor in (0.08, 0.16, 0.3):
        small = pygame.transform.smoothscale(layer, (max(1, int(out.get_width() * factor)),
                                                     max(1, int(out.get_height() * factor))))
        out.blit(pygame.transform.smoothscale(small, out.get_size()), (0, 0))
    edge = chosen.render(string, True, (10, 24, 60))
    out.blit(edge, (pad + 3, pad + 4))
    fill = vertical_gradient((w, h), top, bottom).convert_alpha()
    fill.blit(mask, (0, 0), special_flags=pygame.BLEND_RGBA_MIN)
    # BLEND_RGBA_MIN keeps the gradient only where the white text has alpha
    out.blit(fill, (pad, pad))
    return out


PLATE_NORMAL = ((10, 16, 36), (110, 170, 240))
PLATE_LOCKED = ((40, 26, 6), (255, 210, 90))
PLATE_DANGER = ((54, 10, 18), (255, 90, 90))


def draw_plate(surf, rect, string, typed, locked=False, danger=False, nudge=0.0, boss=False):
    """The tile behind an enemy that shows what to type next."""
    rect = pygame.Rect(rect)
    fill, border = PLATE_LOCKED if locked else (PLATE_DANGER if danger else PLATE_NORMAL)
    if nudge:
        rect.x += int(nudge)
    pygame.draw.rect(surf, (0, 0, 0), rect.move(2, 3), border_radius=9)
    panel(surf, rect, fill, 232, border, 9, 2)
    size = 44 if len(string) == 1 else (36 if boss else 32)
    step = 22 if boss else 20
    total = step * len(string)
    x = rect.centerx - total / 2
    y = rect.centery + 1
    for i, char in enumerate(string.upper()):
        if i < typed:
            color = (84, 110, 104)
        elif i == typed:
            color = (255, 232, 90) if len(string) > 1 else (255, 255, 255)
        else:
            color = (238, 244, 255)
        image = glyph(char, size, color)
        surf.blit(image, image.get_rect(center=(x + step / 2, y)))
        x += step


LANGUAGE_PILL = pygame.Rect(0, 8, 172, 30)


def draw_language_pill(surf):
    """The clickable language toggle in the top right corner."""
    from .config import WIDTH
    rect = LANGUAGE_PILL.copy()
    rect.right = WIDTH - 8
    panel(surf, rect, (8, 12, 28), 210, (120, 170, 230), 15)
    for code, area in zip(LANGUAGE_NAMES, (pygame.Rect(rect.x, rect.y, 86, 30), pygame.Rect(rect.x + 86, rect.y, 86, 30))):
        active = code == get_language()
        if active:
            panel(surf, area.inflate(-4, -4), (40, 110, 200), 255, None, 13)
        text(surf, LANGUAGE_NAMES[code], 24, (255, 255, 255) if active else (150, 170, 200), area.center, "center", shadow=False)
    return rect


class MenuList:
    """A keyboard and mouse menu list. Items are keys into the translation table."""

    def __init__(self, items, top, app, spacing=46, size=38, center=None):
        from .config import WIDTH
        self.items = items
        self.top = top
        self.app = app
        self.spacing = spacing
        self.size = size
        self.center = center or WIDTH // 2
        self.index = 0
        self.time = 0.0

    def rect(self, i):
        return pygame.Rect(self.center - 170, self.top + i * self.spacing - self.spacing // 2 + 4, 340, self.spacing - 4)

    def handle(self, event):
        """Returns the chosen item's name, or None."""
        if event.type == pygame.KEYDOWN:
            if event.key in (pygame.K_UP, pygame.K_w):
                self.index = (self.index - 1) % len(self.items)
                self.app.audio.play("menu_move")
            elif event.key in (pygame.K_DOWN, pygame.K_s):
                self.index = (self.index + 1) % len(self.items)
                self.app.audio.play("menu_move")
            elif event.key in (pygame.K_RETURN, pygame.K_KP_ENTER, pygame.K_SPACE):
                self.app.audio.play("menu_select")
                return self.items[self.index]
        elif event.type == pygame.MOUSEMOTION:
            for i in range(len(self.items)):
                if self.rect(i).collidepoint(event.pos) and i != self.index:
                    self.index = i
                    self.app.audio.play("menu_move")
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            for i, item in enumerate(self.items):
                if self.rect(i).collidepoint(event.pos):
                    self.index = i
                    self.app.audio.play("menu_select")
                    return item
        return None

    def update(self, dt):
        self.time += dt

    def draw(self, surf):
        for i, item in enumerate(self.items):
            y = self.top + i * self.spacing
            active = i == self.index
            if active:
                panel(surf, self.rect(i), (20, 60, 120), 180, (120, 210, 255), 10, 2)
            text(surf, t(item), self.size, (255, 240, 150) if active else (205, 220, 240),
                 (self.center, y + 2), "center")


def hint(surf, string, y=None):
    from .config import HEIGHT, WIDTH
    text(surf, string, 24, (170, 190, 215), (WIDTH // 2, y if y else HEIGHT - 26), "center")


def wrap_bar(surf, rect, fraction, color, back=(30, 36, 56), border=(90, 110, 150)):
    rect = pygame.Rect(rect)
    pygame.draw.rect(surf, back, rect, border_radius=3)
    if fraction > 0:
        inner = rect.copy()
        inner.width = max(2, int(rect.width * min(1.0, fraction)))
        pygame.draw.rect(surf, color, inner, border_radius=3)
        pygame.draw.rect(surf, shade(color, 1.3), (inner.x, inner.y, inner.width, max(1, inner.height // 3)), border_radius=3)
    if border:
        pygame.draw.rect(surf, border, rect, 1, border_radius=3)
