"""Window, main loop, command line and crash logging."""
import argparse
import os
import sys
import time
import traceback

from . import __version__


def _quiet_console():
    # A windowed Windows build has no console, so printing must not fail
    if sys.stdout is None:
        sys.stdout = open(os.devnull, "w")
    if sys.stderr is None:
        sys.stderr = open(os.devnull, "w")


_quiet_console()
os.environ.setdefault("PYGAME_HIDE_SUPPORT_PROMPT", "1")

import pygame  # noqa: E402

from . import storage  # noqa: E402
from .art import SpriteBook  # noqa: E402
from .audio import Audio  # noqa: E402
from .backgrounds import Background  # noqa: E402
from .config import FPS, HEIGHT, TITLE, WIDTH  # noqa: E402
from .i18n import JAPANESE, LEVEL_NAMES_JA, STRINGS, detect_language, set_language, toggle_language  # noqa: E402
from .ui import LANGUAGE_PILL, draw_language_pill, font_for, resource_path  # noqa: E402


class App:
    def __init__(self, fullscreen=None):
        pygame.mixer.pre_init(22050, -16, 1, 512)
        pygame.init()
        pygame.display.set_caption(TITLE)
        self._set_icon()
        self.settings = storage.load_settings()
        set_language(self.settings.get("language") or detect_language())
        if fullscreen is not None:
            self.settings["fullscreen"] = fullscreen
        self._apply_mode()
        pygame.key.set_repeat()
        self.audio = Audio(self.settings["sound"], self.settings["music"])
        self.muted = False
        self.book = SpriteBook()
        self.clock = pygame.time.Clock()
        self.running = True
        self.scene = None
        self.last_bests = {}
        self._vignette = None
        self._backdrop = None
        self._veil = None

    def _set_icon(self):
        try:
            pygame.display.set_icon(pygame.image.load(resource_path("assets", "icon.png")))
        except (pygame.error, FileNotFoundError):
            pass

    def _apply_mode(self):
        flags = pygame.SCALED
        if self.settings.get("fullscreen"):
            flags |= pygame.FULLSCREEN
        else:
            flags |= pygame.RESIZABLE
        try:
            self.screen = pygame.display.set_mode((WIDTH, HEIGHT), flags, vsync=1)
        except pygame.error:
            try:
                self.screen = pygame.display.set_mode((WIDTH, HEIGHT), flags)
            except pygame.error:
                self.screen = pygame.display.set_mode((WIDTH, HEIGHT))

    def toggle_fullscreen(self):
        self.settings["fullscreen"] = not self.settings.get("fullscreen")
        self._apply_mode()
        storage.save_settings(self.settings)

    def toggle_language(self):
        self.settings["language"] = toggle_language()
        self.audio.play("menu_select")
        storage.save_settings(self.settings)

    def toggle_mute(self):
        self.muted = not self.muted
        self.audio.set_sound_volume(0.0 if self.muted else self.settings["sound"])
        self.audio.set_music_volume(0.0 if self.muted else self.settings["music"])

    def vignette(self):
        """Darkened screen edges, cached because every scene draws it."""
        if self._vignette is None:
            low = pygame.Surface((96, 72), pygame.SRCALPHA)
            for y in range(72):
                for x in range(96):
                    dx, dy = (x - 47.5) / 48, (y - 35.5) / 36
                    k = max(0.0, (dx * dx + dy * dy) ** 0.5 - 0.72) / 0.7
                    low.set_at((x, y), (0, 0, 10, int(min(1.0, k) * 165)))
            self._vignette = pygame.transform.smoothscale(low, (WIDTH, HEIGHT)).convert_alpha()
        return self._vignette

    def menu_veil(self):
        """Dims the menu background so that text stands out."""
        if self._veil is None:
            self._veil = pygame.Surface((WIDTH, HEIGHT))
            self._veil.fill((4, 6, 26))
            self._veil.set_alpha(120)
        return self._veil

    def menu_backdrop(self):
        if self._backdrop is None:
            self._backdrop = Background("nebula", 40, 77)
        return self._backdrop

    def switch(self, scene):
        self.scene = scene

    def quit(self):
        self.running = False

    @staticmethod
    def _pill_rect():
        rect = LANGUAGE_PILL.copy()
        rect.right = WIDTH - 8
        return rect

    def dispatch(self, event):
        if event.type == pygame.QUIT:
            self.running = False
        elif event.type == pygame.KEYDOWN and event.key == pygame.K_F11:
            self.toggle_fullscreen()
        elif event.type == pygame.KEYDOWN and event.key == pygame.K_F2:
            self.toggle_mute()
        elif event.type == pygame.KEYDOWN and event.key == pygame.K_F3:
            if self.scene.language_toggle:
                self.toggle_language()
        elif (event.type == pygame.MOUSEBUTTONDOWN and event.button == 1 and self.scene.language_toggle
              and self._pill_rect().collidepoint(event.pos)):
            self.toggle_language()
        else:
            self.scene.handle_event(event)

    def step(self, dt):
        """Advance the game one frame. The tests drive the game through this too."""
        self.audio.update(dt)
        self.scene.update(dt)
        self.scene.draw(self.screen)
        if self.scene.language_toggle:
            draw_language_pill(self.screen)

    def run(self):
        from .scenes import MainMenu
        if self.scene is None:
            self.switch(MainMenu(self))
        while self.running:
            dt = min(self.clock.tick(FPS) / 1000.0, 0.05)
            for event in pygame.event.get():
                self.dispatch(event)
            self.step(dt)
            pygame.display.flip()
        storage.save_settings(self.settings)
        pygame.quit()


def _smoke_test(path):
    """Run every screen plus some real gameplay and write a report.

    The build scripts run this inside the finished package, which shows that
    fonts, sound and graphics all work there. A windowed .exe has no console, so
    the result goes to a file.
    """
    from .autoplay import Autoplayer
    from .play import PlayScene, Session
    from .scenes import (AboutScene, HighScores, HowToPlay, MainMenu, OptionsScene, ProgressScene)
    started = time.time()
    app = App(fullscreen=False)
    for scene_type in (MainMenu, HighScores, ProgressScene, HowToPlay, AboutScene, OptionsScene):
        app.switch(scene_type(app))
        for _ in range(5):
            app.step(1 / FPS)
    bot = Autoplayer(5.0)
    app.switch(PlayScene(app, Session(seed=1)))
    for _ in range(FPS * 8):
        scene = app.scene
        if isinstance(scene, PlayScene):
            bot.update(1 / FPS, scene)
        app.step(1 / FPS)
    correct = app.scene.stats.correct if isinstance(app.scene, PlayScene) else 0
    # The Japanese font must really be in the package, with every character we use
    japanese = "".join(pair[1] for pair in STRINGS.values()) + "".join(LEVEL_NAMES_JA.values())
    missing = sorted({c for c in japanese if ord(c) >= 0x2E80
                      and font_for(c, 40).metrics(c)[0] is None})
    set_language(JAPANESE)
    for scene_type in (MainMenu, HighScores, ProgressScene, HowToPlay, AboutScene, OptionsScene):
        app.switch(scene_type(app))
        app.step(1 / FPS)
    report = (f"OK version={__version__} letters={correct} audio={app.audio.enabled} "
              f"japanese_chars={len(set(japanese))} seconds={time.time() - started:.1f}\n")
    pygame.quit()
    if correct <= 0:
        report = "FAIL no letters were typed\n"
    elif missing:
        report = f"FAIL Japanese characters missing from the font: {''.join(missing)}\n"
    with open(path, "w", encoding="utf-8") as handle:
        handle.write(report)
    return 0 if report.startswith("OK") else 1


def main(argv=None):
    parser = argparse.ArgumentParser(prog="typestriker", description=f"{TITLE}: a typing vertical shooter")
    parser.add_argument("--version", action="version", version=f"{TITLE} {__version__}")
    parser.add_argument("--fullscreen", action="store_true", help="start in full screen")
    parser.add_argument("--windowed", action="store_true", help="start in a window")
    parser.add_argument("--level", type=int, choices=range(1, 11), metavar="1-10",
                        help="start directly on a level (for practice)")
    parser.add_argument("--smoke-test", metavar="FILE", help=argparse.SUPPRESS)
    args = parser.parse_args(argv)
    try:
        if args.smoke_test:
            return _smoke_test(args.smoke_test)
        fullscreen = True if args.fullscreen else (False if args.windowed else None)
        app = App(fullscreen)
        if args.level:
            from .play import PlayScene, Session
            app.switch(PlayScene(app, Session(start_level=args.level)))
        app.run()
        return 0
    except Exception:
        report = traceback.format_exc()
        path = os.path.join(storage.data_dir(), "crash.log")
        try:
            with open(path, "a", encoding="utf-8") as handle:
                handle.write(f"--- {time.strftime('%Y-%m-%d %H:%M:%S')} v{__version__} {sys.platform}\n{report}\n")
        except OSError:
            pass
        print(report, file=sys.stderr)
        print(f"Type Striker crashed. Details saved to {path}. See BUGREPORT.md.", file=sys.stderr)
        return 1
