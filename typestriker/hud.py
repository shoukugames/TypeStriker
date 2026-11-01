"""In-game display: score and timer on top, hull and lives at the bottom left."""
import pygame

from . import art
from .config import BOSS_SHOTS, HEIGHT, MAX_HP, TOP_BAR_H, WIDTH
from .ui import panel, text, vertical_gradient, wrap_bar

_cache = {}


def _top_bar():
    if "top" not in _cache:
        bar = vertical_gradient((WIDTH, TOP_BAR_H), (24, 36, 68), (8, 12, 28)).convert_alpha()
        bar.set_alpha(232)
        pygame.draw.line(bar, (100, 170, 240), (0, TOP_BAR_H - 2), (WIDTH, TOP_BAR_H - 2), 2)
        _cache["top"] = bar
    return _cache["top"]


def _life_icon():
    if "life" not in _cache:
        _cache["life"] = art.player_ship(0.30)
    return _cache["life"]


def format_time(seconds):
    seconds = int(seconds)
    return f"{seconds // 60:02d}:{seconds % 60:02d}"


def _hp_color(i):
    t = i / (MAX_HP - 1)
    if t < 0.5:
        return art.mix((240, 60, 50), (250, 200, 60), t * 2)
    return art.mix((250, 200, 60), (70, 230, 110), (t - 0.5) * 2)


def draw_hud(surf, scene):
    session, level, stats = scene.session, scene.level, scene.stats
    surf.blit(_top_bar(), (0, 0))
    # Score and timer sit side by side
    text(surf, "SCORE", 20, (150, 190, 235), (18, 8))
    text(surf, f"{session.score:07d}", 38, (255, 240, 150), (18, 22))
    text(surf, "TIME", 20, (150, 190, 235), (190, 8))
    text(surf, format_time(session.time), 38, (255, 255, 255), (190, 22))
    # Level and wave progress
    text(surf, f"LEVEL {level.number}/10", 20, (150, 190, 235), (WIDTH - 18, 8), "topright")
    text(surf, level.name, 32, (235, 240, 255), (WIDTH - 18, 23), "topright")
    if scene.state in ("wave", "intro"):
        remaining = level.targets - scene.spawned + len(scene.targets)
        fraction = 1.0 - remaining / level.targets
        text(surf, "WAVE", 20, (150, 190, 235), (330, 8))
        wrap_bar(surf, (330, 28, 240, 12), fraction, (90, 200, 255))
    elif scene.state in ("warning", "boss", "boss_death"):
        text(surf, "BOSS", 20, (255, 150, 140), (330, 8))
        wrap_bar(surf, (330, 28, 240, 12), 1.0, (255, 90, 80))
    # Boss health: ten segments, one per shot
    boss = scene.boss
    if boss is not None and boss.y > -boss.h * 0.4:
        remaining = BOSS_SHOTS - boss.hits
        x0 = WIDTH // 2 - 165
        y = TOP_BAR_H + 8
        panel(surf, (x0 - 10, y - 4, 350, 40), (20, 6, 14), 190, (220, 90, 90), 8)
        text(surf, scene.level.boss_name, 20, (255, 205, 195), (WIDTH // 2, y + 8), "center")
        for i in range(BOSS_SHOTS):
            r = pygame.Rect(x0 + i * 33, y + 16, 30, 11)
            pygame.draw.rect(surf, (255, 86, 70) if i < remaining else (60, 30, 36), r, border_radius=2)
            pygame.draw.rect(surf, (255, 180, 170) if i < remaining else (90, 60, 66), r, 1, border_radius=2)
    # Bottom left: hull bar and lives
    x, y = 14, HEIGHT - 62
    panel(surf, (x - 6, y - 6, 306, 62), (8, 12, 28), 200, (100, 170, 240), 9)
    text(surf, "HULL", 22, (170, 205, 240), (x + 2, y + 1))
    for i in range(MAX_HP):
        r = pygame.Rect(x + 50 + i * 24, y - 1, 21, 20)
        filled = i < session.hp
        col = _hp_color(i) if filled else (36, 42, 60)
        pygame.draw.rect(surf, col, r, border_radius=3)
        if filled:
            pygame.draw.rect(surf, art.shade(col, 1.35), (r.x, r.y, r.w, 6), border_radius=3)
        pygame.draw.rect(surf, (8, 10, 20), r, 1, border_radius=3)
    text(surf, "LIVES", 22, (170, 205, 240), (x + 2, y + 29))
    icon = _life_icon()
    for i in range(session.lives):
        surf.blit(icon, (x + 54 + i * 30, y + 22))
    # Bottom right: live speed and accuracy
    x = WIDTH - 200
    panel(surf, (x, HEIGHT - 50, 190, 40), (8, 12, 28), 190, (100, 170, 240), 9)
    speed = f"{stats.wpm:.0f} WPM"
    acc = f"{stats.accuracy:.0f}%" if stats.correct + stats.wrong else "--"
    text(surf, speed, 26, (150, 240, 255), (x + 12, HEIGHT - 39))
    text(surf, acc, 26, (180, 255, 180), (x + 178, HEIGHT - 39), "topright")
    if scene.locked is not None:
        panel(surf, (WIDTH // 2 - 50, HEIGHT - 38, 220, 26), (8, 12, 28), 190, None, 7)
        text(surf, "BACKSPACE: change target", 21, (240, 225, 160), (WIDTH // 2 + 60, HEIGHT - 25), "center")
