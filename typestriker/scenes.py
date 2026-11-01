"""Every screen other than the game itself."""
import math
import random
import webbrowser

import pygame

from . import __version__, art, storage
from .config import (AUTHOR, EMAIL, HEIGHT, LEVEL_CLEAR_REPAIR, LEVELS, MAX_HP, NAME_LENGTH,
                     START_LIVES, TOP_SCORES, WEBSITE, WIDTH)
from .effects import Effects
from .i18n import LANGUAGE_NAMES, challenge, get_language, level_name, t
from .hud import format_time
from .play import PlayScene, Session
from .ui import MenuList, fancy_title, hint, panel, text, wrap_bar


def _confirm(event):
    return event.type == pygame.KEYDOWN and event.key in (pygame.K_RETURN, pygame.K_KP_ENTER, pygame.K_SPACE)


def _back(event):
    if event.type == pygame.KEYDOWN and event.key in (pygame.K_ESCAPE, pygame.K_RETURN, pygame.K_KP_ENTER, pygame.K_SPACE):
        return True
    return event.type == pygame.MOUSEBUTTONDOWN and event.button == 3


class BackdropScene:
    """A screen drawn over the shared moving starfield."""

    language_toggle = True

    def __init__(self, app):
        self.app = app
        self.time = 0.0

    def handle_event(self, event):
        pass

    def update(self, dt):
        self.time += dt
        self.app.menu_backdrop().update(dt)

    def draw(self, surf):
        self.app.menu_backdrop().draw(surf)
        surf.blit(self.app.menu_veil(), (0, 0))
        surf.blit(self.app.vignette(), (0, 0))


class MainMenu(BackdropScene):
    ITEMS = ["menu.start", "menu.top10", "menu.progress", "menu.howto", "menu.about", "menu.options", "menu.quit"]

    def __init__(self, app):
        super().__init__(app)
        self.menu = MenuList(self.ITEMS, 318, app, spacing=48)
        app.audio.play_theme()
        self.ship = art.player_ship(1.5)

    def handle_event(self, event):
        choice = self.menu.handle(event)
        app = self.app
        if choice == "menu.start":
            app.switch(PlayScene(app, Session()))
        elif choice == "menu.top10":
            app.switch(HighScores(app))
        elif choice == "menu.progress":
            app.switch(ProgressScene(app))
        elif choice == "menu.howto":
            app.switch(HowToPlay(app))
        elif choice == "menu.about":
            app.switch(AboutScene(app))
        elif choice == "menu.options":
            app.switch(OptionsScene(app))
        elif choice == "menu.quit":
            app.quit()

    def update(self, dt):
        super().update(dt)
        self.menu.update(dt)

    def draw(self, surf):
        super().draw(surf)
        bob = math.sin(self.time * 1.6) * 8
        title = fancy_title(t("title"), 130)
        surf.blit(title, title.get_rect(center=(WIDTH // 2, 112 + bob * 0.3)))
        text(surf, t("tagline"), 32, (200, 225, 255), (WIDTH // 2, 186), "center")
        x = WIDTH // 2 + math.sin(self.time * 0.5) * 300
        y = 248 + bob
        for dx in (-8, 8):
            size = int(24 + 6 * math.sin(self.time * 25))
            glow = art.additive(size, (255, 140, 50), 1.2)
            surf.blit(glow, (x + dx - size, y + 58 - size), special_flags=pygame.BLEND_RGB_ADD)
        ship = pygame.transform.smoothscale(self.ship, (int(self.ship.get_width() * 0.75), int(self.ship.get_height() * 0.75)))
        surf.blit(ship, ship.get_rect(center=(x, y)))
        self.menu.draw(surf)
        hint(surf, t("hint.menu"))


class HighScores(BackdropScene):
    def __init__(self, app, highlight=None):
        super().__init__(app)
        self.scores = storage.load_scores()
        self.highlight = highlight

    def handle_event(self, event):
        if _back(event):
            self.app.audio.play("menu_select")
            self.app.switch(MainMenu(self.app))

    def draw(self, surf):
        super().draw(surf)
        title = fancy_title(t("top10.title"), 84, (255, 255, 255), (255, 200, 90), (220, 120, 30))
        surf.blit(title, title.get_rect(center=(WIDTH // 2, 64)))
        panel(surf, (80, 118, WIDTH - 160, 530))
        columns = [(112, "#"), (160, t("col.name")), (500, t("col.score")), (610, t("col.level")),
                   (720, t("col.wpm")), (850, t("col.accuracy"))]
        for i, (x, label) in enumerate(columns):
            anchor = "topleft" if i < 2 else "topright"
            text(surf, label, 24, (140, 190, 240), (x, 132), anchor)
        pygame.draw.line(surf, (90, 130, 190), (100, 156), (WIDTH - 100, 156))
        for i in range(TOP_SCORES):
            y = 170 + i * 46
            medal = {0: (255, 215, 90), 1: (214, 224, 236), 2: (226, 158, 96)}.get(i, (200, 215, 235))
            if i < len(self.scores):
                row = self.scores[i]
                if self.highlight == i:
                    panel(surf, (94, y - 7, WIDTH - 188, 42), (70, 60, 10), 170, (255, 220, 110), 7)
                text(surf, str(i + 1), 34, medal, (112, y))
                text(surf, row["name"], 34, medal, (160, y))
                text(surf, f"{row['score']:,}", 34, (255, 255, 255), (500, y), "topright")
                text(surf, str(row["level"]), 34, (205, 220, 240), (610, y), "topright")
                text(surf, f"{row['wpm']:.0f}", 34, (150, 240, 255), (720, y), "topright")
                text(surf, f"{row['accuracy']:.0f}%", 34, (180, 255, 180), (850, y), "topright")
            else:
                text(surf, str(i + 1), 34, (84, 96, 120), (112, y))
                text(surf, "- - - - -", 30, (84, 96, 120), (160, y + 2))
        hint(surf, t("hint.back"))


class ProgressScene(BackdropScene):
    """Speed and accuracy recorded for each level across all games."""

    def __init__(self, app):
        super().__init__(app)
        self.progress = storage.load_progress()

    def handle_event(self, event):
        if _back(event):
            self.app.audio.play("menu_select")
            self.app.switch(MainMenu(self.app))

    def draw(self, surf):
        super().draw(surf)
        title = fancy_title(t("progress.title"), 76, (255, 255, 255), (130, 255, 190), (30, 170, 110))
        surf.blit(title, title.get_rect(center=(WIDTH // 2, 54)))
        panel(surf, (24, 100, WIDTH - 48, 556))
        last, best = t("progress.last"), t("progress.best")
        head = [(44, t("col.level"), "topleft"), (280, t("progress.played"), "topright"), (360, last, "topright"),
                (430, best, "topright"), (520, t("progress.trend"), "topleft"), (780, last, "topright"),
                (850, best, "topright"), (925, t("progress.clears"), "topright")]
        text(surf, t("progress.speed"), 20, (150, 240, 255), (395, 110), "center")
        text(surf, t("col.accuracy"), 20, (180, 255, 180), (815, 110), "center")
        for x, label, anchor in head:
            text(surf, label, 22, (140, 190, 240), (x, 130), anchor)
        pygame.draw.line(surf, (90, 130, 190), (40, 152), (WIDTH - 40, 152))
        for i, level in enumerate(LEVELS):
            y = 166 + i * 48
            row = self.progress.get(str(level.number))
            text(surf, f"{level.number}. {level_name(level)}", 28, (225, 235, 250) if row else (110, 122, 145), (44, y))
            if not row:
                text(surf, t("progress.none"), 22, (90, 102, 126), (280, y + 3), "topleft")
                continue
            text(surf, str(row.get("plays", 0)), 28, (205, 220, 240), (280, y), "topright")
            text(surf, f"{row.get('last_wpm', 0):.0f}", 28, (150, 240, 255), (360, y), "topright")
            text(surf, f"{row.get('best_wpm', 0):.0f}", 28, (255, 240, 150), (430, y), "topright")
            self._trend(surf, (520, y - 3, 170, 28), row.get("history", []))
            text(surf, f"{row.get('last_accuracy', 0):.0f}%", 28, (180, 255, 180), (780, y), "topright")
            text(surf, f"{row.get('best_accuracy', 0):.0f}%", 28, (255, 240, 150), (850, y), "topright")
            text(surf, str(row.get("clears", 0)), 28, (205, 220, 240), (925, y), "topright")
        hint(surf, t("progress.hint"), HEIGHT - 28)

    @staticmethod
    def _trend(surf, rect, history):
        x, y, w, h = rect
        values = [float(row.get("wpm", 0)) for row in history if isinstance(row, dict)][-20:]
        pygame.draw.rect(surf, (20, 28, 48), rect, border_radius=4)
        if not values:
            return
        top = max(max(values), 1.0)
        bar = w / max(len(values), 1)
        bar_w = max(2, min(14, int(bar) - 2))
        for i, value in enumerate(values):
            height = max(2, int(value / top * (h - 4)))
            color = (255, 220, 110) if i == len(values) - 1 else (90, 190, 240)
            pygame.draw.rect(surf, color, (x + 2 + i * bar, y + h - 2 - height, bar_w, height), border_radius=1)


class HowToPlay(BackdropScene):
    @staticmethod
    def lines():
        return [t("howto.1"), t("howto.2"), t("howto.3"), t("howto.4"), t("howto.5"), t("howto.6"), t("howto.7"),
                t("howto.8", lives=START_LIVES, hp=MAX_HP), t("howto.9", repair=LEVEL_CLEAR_REPAIR)]

    def handle_event(self, event):
        if _back(event):
            self.app.audio.play("menu_select")
            self.app.switch(MainMenu(self.app))

    def draw(self, surf):
        super().draw(surf)
        title = fancy_title(t("howto.title"), 84)
        surf.blit(title, title.get_rect(center=(WIDTH // 2, 64)))
        panel(surf, (50, 118, WIDTH - 100, 400))
        for i, line in enumerate(self.lines()):
            text(surf, line, 27, (225, 235, 250), (74, 136 + i * 41))
        panel(surf, (50, 530, WIDTH - 100, 118))
        text(surf, t("howto.keys"), 27, (255, 232, 130), (WIDTH // 2, 556), "center")
        text(surf, t("howto.saved1"), 27, (190, 220, 255), (WIDTH // 2, 592), "center")
        text(surf, t("howto.saved2"), 27, (190, 220, 255), (WIDTH // 2, 622), "center")
        hint(surf, t("hint.back"))


class AboutScene(BackdropScene):
    def __init__(self, app):
        super().__init__(app)
        self.site_rect = pygame.Rect(0, 0, 0, 0)
        self.mail_rect = pygame.Rect(0, 0, 0, 0)
        self.ship = art.player_ship(1.6)

    def _open(self, url):
        self.app.audio.play("menu_select")
        try:
            webbrowser.open(url)
        except webbrowser.Error:
            pass

    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.site_rect.collidepoint(event.pos):
                self._open(WEBSITE)
                return
            if self.mail_rect.collidepoint(event.pos):
                self._open(f"mailto:{EMAIL}")
                return
        if _back(event):
            self.app.audio.play("menu_select")
            self.app.switch(MainMenu(self.app))

    def draw(self, surf):
        super().draw(surf)
        title = fancy_title(t("about.title"), 88)
        surf.blit(title, title.get_rect(center=(WIDTH // 2, 66)))
        panel(surf, (120, 124, WIDTH - 240, 500))
        surf.blit(self.ship, self.ship.get_rect(center=(WIDTH // 2, 214)))
        text(surf, t("about.game", version=__version__), 44, (255, 255, 255), (WIDTH // 2, 310), "center")
        text(surf, t("about.written_by"), 26, (170, 195, 225), (WIDTH // 2, 358), "center")
        text(surf, t("about.author", author=AUTHOR), 38, (255, 232, 130), (WIDTH // 2, 390), "center")
        text(surf, t("about.website"), 26, (170, 195, 225), (WIDTH // 2, 436), "center")
        self.site_rect = text(surf, WEBSITE, 34, (120, 215, 255), (WIDTH // 2, 466), "center")
        pygame.draw.line(surf, (120, 215, 255), self.site_rect.bottomleft, self.site_rect.bottomright)
        text(surf, t("about.email"), 26, (170, 195, 225), (WIDTH // 2, 508), "center")
        self.mail_rect = text(surf, EMAIL, 34, (120, 215, 255), (WIDTH // 2, 538), "center")
        pygame.draw.line(surf, (120, 215, 255), self.mail_rect.bottomleft, self.mail_rect.bottomright)
        text(surf, t("about.license"), 24, (170, 195, 225), (WIDTH // 2, 592), "center")
        hint(surf, t("about.hint"))


class OptionsScene(BackdropScene):
    def __init__(self, app):
        super().__init__(app)
        self.index = 0

    ROWS = ("options.sound", "options.music", "options.fullscreen", "options.language", "options.back")
    BACK = 4

    def _change(self, direction):
        audio, settings = self.app.audio, self.app.settings
        if self.index == 0:
            settings["sound"] = round(max(0.0, min(1.0, settings["sound"] + direction * 0.1)), 1)
            audio.set_sound_volume(settings["sound"])
            audio.play("destroy_scout")
        elif self.index == 1:
            settings["music"] = round(max(0.0, min(1.0, settings["music"] + direction * 0.1)), 1)
            audio.set_music_volume(settings["music"])
            audio.play("menu_move")
        elif self.index == 2:
            self.app.toggle_fullscreen()
            audio.play("menu_select")
        elif self.index == 3:
            self.app.toggle_language()
        storage.save_settings(settings)

    def handle_event(self, event):
        if event.type != pygame.KEYDOWN:
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 3:
                self.app.switch(MainMenu(self.app))
            return
        if event.key == pygame.K_ESCAPE:
            self.app.switch(MainMenu(self.app))
        elif event.key == pygame.K_UP:
            self.index = (self.index - 1) % len(self.ROWS)
            self.app.audio.play("menu_move")
        elif event.key == pygame.K_DOWN:
            self.index = (self.index + 1) % len(self.ROWS)
            self.app.audio.play("menu_move")
        elif event.key == pygame.K_LEFT:
            self._change(-1)
        elif event.key == pygame.K_RIGHT:
            self._change(1)
        elif event.key in (pygame.K_RETURN, pygame.K_KP_ENTER, pygame.K_SPACE):
            if self.index == self.BACK:
                self.app.audio.play("menu_select")
                self.app.switch(MainMenu(self.app))
            elif self.index in (2, 3):
                self._change(1)

    def draw(self, surf):
        super().draw(surf)
        title = fancy_title(t("options.title"), 88)
        surf.blit(title, title.get_rect(center=(WIDTH // 2, 80)))
        panel(surf, (160, 170, WIDTH - 320, 340))
        settings = self.app.settings
        for i, label in enumerate(self.ROWS):
            y = 210 + i * 64
            active = i == self.index
            if active:
                panel(surf, (180, y - 27, WIDTH - 360, 54), (20, 60, 120), 180, (120, 210, 255), 9, 2)
            text(surf, t(label), 36, (255, 240, 150) if active else (205, 220, 240), (204, y), "midleft")
            if i in (0, 1):
                value = settings["sound"] if i == 0 else settings["music"]
                wrap_bar(surf, (500, y - 11, 220, 22), value, (90, 200, 255))
                text(surf, f"{int(value * 100)}%", 28, (235, 240, 255), (760, y), "midright")
            elif i == 2:
                text(surf, t("options.on") if settings["fullscreen"] else t("options.off"), 34, (235, 240, 255), (760, y), "midright")
            elif i == 3:
                text(surf, LANGUAGE_NAMES[get_language()], 34, (235, 240, 255), (760, y), "midright")
        hint(surf, t("options.hint"))


class LevelSummary(BackdropScene):
    """Shown after each level with that level's speed and accuracy."""

    def __init__(self, app, session, stats, bests):
        super().__init__(app)
        self.session = session
        self.stats = stats
        self.bests = bests or {}
        self.final = stats.number >= len(LEVELS)
        self.stars = self._rating()
        if self.bests.get("wpm") or self.bests.get("accuracy"):
            app.audio.play("new_best")
        app.audio.play_theme()

    def _rating(self):
        s = self.stats
        stars = 1
        if s.accuracy >= 85 and s.hits_taken <= 5:
            stars = 2
        if s.accuracy >= 95 and s.hits_taken <= 2:
            stars = 3
        return stars

    def handle_event(self, event):
        # A short pause keeps leftover typing from skipping this screen
        if self.time > 0.7 and _confirm(event):
            self.app.audio.play("menu_select")
            session = self.session
            if self.final:
                session.victory = True
                self.app.audio.play("victory")
                self.app.switch(ResultsScene(self.app, session))
            else:
                session.level_index += 1
                self.app.switch(PlayScene(self.app, session))

    def draw(self, surf):
        super().draw(surf)
        s = self.stats
        title = fancy_title(t("summary.title", n=s.number), 84, (255, 255, 255), (130, 255, 170), (30, 170, 90))
        surf.blit(title, title.get_rect(center=(WIDTH // 2, 66)))
        text(surf, level_name(LEVELS[s.number - 1]), 38, (225, 235, 250), (WIDTH // 2, 126), "center")
        for i in range(3):
            self._star(surf, WIDTH // 2 + (i - 1) * 76, 186, 30, i < self.stars and self.time > 0.2 + i * 0.22)
        panel(surf, (170, 234, WIDTH - 340, 366))
        rows = [
            (t("summary.speed"), f"{s.wpm:.1f} WPM", (150, 240, 255), self.bests.get("wpm")),
            (t("summary.accuracy"), f"{s.accuracy:.1f}%", (180, 255, 180), self.bests.get("accuracy")),
            (t("summary.letters"), f"{s.correct}", (235, 240, 255), False),
            (t("summary.wrong"), f"{s.wrong}", (235, 240, 255), False),
            (t("summary.destroyed"), f"{s.destroyed}", (235, 240, 255), False),
            (t("summary.missed"), f"{s.missed}", (235, 240, 255), False),
            (t("summary.hits"), f"{s.hits_taken}", (235, 240, 255), False),
            (t("summary.level_score"), f"{s.score:,}", (255, 240, 150), False),
            (t("summary.total_score"), f"{self.session.score:,}", (255, 240, 150), False),
        ]
        for i, (label, value, col, best) in enumerate(rows):
            y = 262 + i * 37
            text(surf, label, 32, (190, 210, 235), (210, y), "midleft")
            text(surf, value, 34, col, (WIDTH - 210, y), "midright")
            if best:
                text(surf, t("summary.best"), 24, (255, 215, 90), (WIDTH // 2 + 20, y), "midleft")
        text(surf, t("summary.repair", repair=LEVEL_CLEAR_REPAIR, hp=self.session.hp, max_hp=MAX_HP, lives=self.session.lives),
             26, (190, 220, 255), (WIDTH // 2, 628), "center")
        if self.final:
            hint(surf, t("summary.final"))
        else:
            next_level = LEVELS[s.number]
            hint(surf, t("summary.next", name=level_name(next_level), challenge=challenge(next_level)))

    @staticmethod
    def _star(surf, x, y, r, lit):
        pts = []
        for i in range(10):
            radius = r if i % 2 == 0 else r * 0.45
            a = -math.pi / 2 + i * math.pi / 5
            pts.append((x + math.cos(a) * radius, y + math.sin(a) * radius))
        pygame.draw.polygon(surf, (255, 215, 80) if lit else (46, 54, 76), pts)
        pygame.draw.polygon(surf, (255, 245, 180) if lit else (84, 94, 120), pts, 2)


class ResultsScene(BackdropScene):
    """The stats from the game just played, shown after victory or game over."""

    def __init__(self, app, session):
        super().__init__(app)
        self.session = session
        self.qualified = storage.qualifies(session.score)
        self.effects = Effects()
        self.firework = 0.2
        app.audio.play_theme()

    def handle_event(self, event):
        if self.time > 0.8 and _confirm(event):
            self.app.audio.play("menu_select")
            if self.qualified:
                self.app.switch(NameEntry(self.app, self.session))
            else:
                self.app.switch(HighScores(self.app))

    def update(self, dt):
        super().update(dt)
        self.effects.update(dt)
        if self.session.victory:
            self.firework -= dt
            if self.firework <= 0:
                self.firework = random.uniform(0.25, 0.7)
                color = random.choice(((255, 120, 120), (120, 255, 180), (130, 180, 255), (255, 220, 110), (240, 130, 255)))
                self.effects.spark(random.uniform(60, WIDTH - 60), random.uniform(30, 130), color, 40, 230, 0.9, 6)

    def draw(self, surf):
        super().draw(surf)
        session = self.session
        if session.victory:
            title = fancy_title(t("results.victory"), 74, (255, 255, 255), (255, 215, 90), (220, 130, 30))
        else:
            title = fancy_title(t("results.gameover"), 80, (255, 255, 255), (255, 110, 110), (190, 30, 30))
        surf.blit(title, title.get_rect(center=(WIDTH // 2, 48)))
        self.effects.draw(surf)
        panel(surf, (40, 90, WIDTH - 80, 76))
        destroyed = sum(s.destroyed for s in session.levels)
        missed = sum(s.missed for s in session.levels)
        summary = [(t("col.score"), f"{session.score:,}", (255, 240, 150)),
                   (t("col.time"), format_time(session.time), (255, 255, 255)),
                   (t("col.speed"), f"{session.wpm:.1f} WPM", (150, 240, 255)),
                   (t("col.accuracy"), f"{session.accuracy:.1f}%", (180, 255, 180)),
                   (t("col.destroyed"), str(destroyed), (235, 240, 255)),
                   (t("col.missed"), str(missed), (235, 240, 255))]
        widths = [190, 110, 165, 135, 130, 110]
        x = 56
        for (label, value, col), w in zip(summary, widths):
            text(surf, label, 20, (140, 190, 240), (x, 100))
            text(surf, value, 32, col, (x, 122))
            x += w
        panel(surf, (40, 176, WIDTH - 80, 456))
        heads = [(58, t("col.level"), "topleft"), (400, t("col.speed"), "topright"), (530, t("col.accuracy"), "topright"),
                 (620, t("col.time"), "topright"), (710, t("col.hits"), "topright"), (790, t("col.score"), "topright"),
                 (900, t("col.result"), "topright")]
        for hx, label, anchor in heads:
            text(surf, label, 22, (140, 190, 240), (hx, 188), anchor)
        pygame.draw.line(surf, (90, 130, 190), (54, 210), (WIDTH - 54, 210))
        top_speed = max([s.wpm for s in session.levels] + [1.0])
        by_number = {s.number: s for s in session.levels}
        for i, level in enumerate(LEVELS):
            y = 220 + i * 40
            s = by_number.get(level.number)
            if s is None:
                text(surf, f"{level.number}. {level_name(level)}", 26, (88, 100, 124), (58, y + 4))
                continue
            text(surf, f"{level.number}. {level_name(level)}", 26, (225, 235, 250), (58, y + 4))
            wrap_bar(surf, (262, y + 8, 80, 12), s.wpm / top_speed, (90, 200, 255), border=None)
            text(surf, f"{s.wpm:.0f}", 28, (150, 240, 255), (400, y + 2), "topright")
            text(surf, f"{s.accuracy:.0f}%", 28, (180, 255, 180), (530, y + 2), "topright")
            text(surf, format_time(s.time), 28, (225, 235, 250), (620, y + 2), "topright")
            text(surf, str(s.hits_taken), 28, (225, 235, 250), (710, y + 2), "topright")
            text(surf, f"{s.score:,}", 28, (255, 240, 150), (790, y + 2), "topright")
            done = s.completed
            text(surf, t("results.clear") if done else t("results.lost"), 24, (130, 255, 170) if done else (255, 120, 120), (900, y + 4), "topright")
        if self.qualified:
            pulse = 200 + int(55 * math.sin(self.time * 5))
            text(surf, t("results.qualified"), 32, (255, pulse, 90), (WIDTH // 2, HEIGHT - 44), "center")
        else:
            hint(surf, t("results.continue"), HEIGHT - 44)


class NameEntry(BackdropScene):
    def __init__(self, app, session):
        super().__init__(app)
        self.session = session
        self.name = ""

    def handle_event(self, event):
        if event.type != pygame.KEYDOWN:
            return
        if event.key == pygame.K_BACKSPACE:
            self.name = self.name[:-1]
            self.app.audio.play("menu_move")
        elif event.key in (pygame.K_RETURN, pygame.K_KP_ENTER):
            if self.name.strip():
                self._submit()
        else:
            char = event.unicode or ""
            if len(char) == 1 and char.isprintable() and (char.isalnum() or char in " -_.") \
                    and len(self.name) < NAME_LENGTH:
                self.name += char
                self.app.audio.play("key")

    def _submit(self):
        session = self.session
        rank = storage.add_score(self.name, session.score, session.furthest_level, session.wpm, session.accuracy)
        self.app.audio.play("level_clear")
        self.app.switch(HighScores(self.app, rank))

    def draw(self, surf):
        super().draw(surf)
        title = fancy_title(t("name.title"), 76, (255, 255, 255), (255, 215, 90), (220, 130, 30))
        surf.blit(title, title.get_rect(center=(WIDTH // 2, 130)))
        text(surf, t("name.points", score=f"{self.session.score:,}"), 56, (255, 240, 150), (WIDTH // 2, 222), "center")
        text(surf, t("name.prompt", n=NAME_LENGTH), 34, (205, 220, 240), (WIDTH // 2, 300), "center")
        box_w = 44
        x0 = WIDTH // 2 - NAME_LENGTH * box_w / 2
        for i in range(NAME_LENGTH):
            rect = pygame.Rect(x0 + i * box_w + 2, 340, box_w - 4, 64)
            current = i == len(self.name)
            lit = current and int(self.time * 3) % 2 == 0
            panel(surf, rect, (20, 40, 80), 220, (255, 225, 110) if lit else (100, 150, 210), 7, 2)
            if i < len(self.name):
                text(surf, self.name[i], 54, (255, 255, 255), rect.center, "center")
        count = f"{len(self.name)} / {NAME_LENGTH}"
        text(surf, count, 28, (170, 195, 225), (WIDTH // 2, 432), "center")
        hint(surf, t("name.save"), 492)
