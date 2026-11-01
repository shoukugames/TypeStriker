"""One game: the session across levels, typing rules, and the level state machine."""
import math
import random

import pygame

from . import art, storage
from .backgrounds import Background
from .config import (BOSS_BONUS, BOSS_SHOTS, HEIGHT, INVULNERABLE_TIME, LEVEL_CLEAR_REPAIR,
                     LEVELS, MAX_HP, POINTS_PER_LETTER, RAIL_Y, START_LIVES, TOP_BAR_H, WIDTH,
                     describe_challenge)
from .effects import Effects
from .entities import PLAYER_HIT_RADIUS, Boss, Bullet, Player, Shot, Target
from .i18n import t
from .ui import MenuList, draw_plate, fancy_title, font, text
from .words import WordDealer

DESTROY_SOUND = {kind: f"destroy_{kind}" for kind in
                 ("scout", "fighter", "bomber", "saucer", "interceptor", "drone", "tank",
                  "asteroid", "missile")}


class LevelStats:
    """Speed and accuracy for one level."""

    def __init__(self, level):
        self.number = level.number
        self.name = level.name
        self.correct = 0
        self.wrong = 0
        self.active_time = 0.0   # time with something on screen to type at
        self.time = 0.0
        self.destroyed = 0
        self.missed = 0
        self.hits_taken = 0
        self.score = 0
        self.completed = False

    @property
    def wpm(self):
        """Words per minute, using the standard five letters per word."""
        if self.active_time <= 0:
            return 0.0
        return (self.correct / 5.0) / (self.active_time / 60.0)

    @property
    def accuracy(self):
        presses = self.correct + self.wrong
        return 100.0 * self.correct / presses if presses else 0.0


class Session:
    """Everything that lasts for one whole game."""

    def __init__(self, start_level=1, seed=None):
        self.rng = random.Random(seed)
        self.dealer = WordDealer(self.rng)
        self.level_index = start_level - 1
        self.score = 0
        self.lives = START_LIVES
        self.hp = MAX_HP
        self.time = 0.0
        self.levels = []
        self.victory = False

    @property
    def level(self):
        return LEVELS[self.level_index]

    @property
    def total_correct(self):
        return sum(s.correct for s in self.levels)

    @property
    def total_wrong(self):
        return sum(s.wrong for s in self.levels)

    @property
    def wpm(self):
        active = sum(s.active_time for s in self.levels)
        return (self.total_correct / 5.0) / (active / 60.0) if active > 0 else 0.0

    @property
    def accuracy(self):
        presses = self.total_correct + self.total_wrong
        return 100.0 * self.total_correct / presses if presses else 0.0

    @property
    def furthest_level(self):
        return self.levels[-1].number if self.levels else self.level.number


def _bullet_sprite(radius, color):
    surf = art.additive(radius, color, 1.1).copy()
    pygame.draw.circle(surf, (255, 255, 255), (radius, radius), max(2, radius // 3))
    return surf


class PlayScene:
    @property
    def language_toggle(self):
        return self.paused  # gameplay stays in English; only the pause menu changes

    def __init__(self, app, session):
        self.app = app
        self.session = session
        self.level = session.level
        self.stats = LevelStats(self.level)
        session.levels.append(self.stats)
        self.rng = session.rng
        self.book = app.book
        self.player = Player(self.book.player())
        self.targets = []
        self.bullets = []
        self.shots = []
        self.boss = None
        self.locked = None
        self.effects = Effects()
        self.background = Background(self.level.theme, self.level.speed, 100 + self.level.number)
        self.world = pygame.Surface((WIDTH, HEIGHT)).convert()
        self.state = "intro"
        self.state_time = 0.0
        self.spawned = 0
        self.spawn_clock = 0.8
        self.streak = 0
        self.best_streak = 0
        self.damage_flash = 0.0
        self.paused = False
        self.pause_menu = None
        self.boss_blasts = 0.0
        self.time = 0.0
        pal = self.level.palette
        self.bullet_sprites = {
            "enemy": _bullet_sprite(10, pal.bullet),
            "shell": _bullet_sprite(9, (255, 170, 70)),
            "boss": _bullet_sprite(13, pal.bullet),
        }
        self.vignette = app.vignette()
        app.audio.play_theme(self.level.music)

    # ---- input ----------------------------------------------------------
    def handle_event(self, event):
        if self.paused:
            self._pause_event(event)
            return
        if event.type == pygame.WINDOWFOCUSLOST and self.state != "dying":
            self.set_paused(True)
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                self.set_paused(True)
            elif event.key == pygame.K_BACKSPACE:
                self._release_lock()
            else:
                char = (event.unicode or "").lower()
                if len(char) != 1 or not "a" <= char <= "z":
                    # A Japanese keyboard in kana mode sends kana, but the key is still known
                    char = chr(event.key) if pygame.K_a <= event.key <= pygame.K_z else ""
                if char:
                    self.press(char)

    def set_paused(self, paused):
        self.paused = paused
        if paused:
            self.pause_menu = MenuList(["pause.resume", "pause.quit"], HEIGHT // 2 + 10, self.app)

    def _pause_event(self, event):
        if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            self.set_paused(False)
            return
        choice = self.pause_menu.handle(event)
        if choice == "pause.resume":
            self.set_paused(False)
        elif choice == "pause.quit":
            from .scenes import MainMenu
            self.app.switch(MainMenu(self.app))

    def can_type(self):
        return self.state in ("wave", "boss")

    def typeable(self):
        """Everything the player could shoot right now, lowest on the screen first."""
        items = [t for t in self.targets if t.alive and not t.doomed and t.on_screen]
        items.sort(key=lambda t: -t.y)
        if self.boss and self.boss.arrived and not self.boss.doomed and self.state == "boss":
            items.append(self.boss)
        return items

    def press(self, char):
        if not self.can_type():
            return
        target = self.locked
        if target is not None and (not target.alive or target.doomed):
            target = self.locked = None
        if target is None:
            available = self.typeable()
            if not available:
                return  # nothing to shoot at, so a stray key costs nothing
            for candidate in available:
                if candidate.next_letter == char:
                    target = candidate
                    break
            if target is None:
                self._wrong_key()
                return
            if len(target.text) > 1:
                self.locked = target
                target.locked = True
                self.app.audio.play("lock", 0.5)
        elif target.next_letter != char:
            target.shake = 0.5
            self._wrong_key()
            return
        self._correct_key(target)

    def _wrong_key(self):
        self.stats.wrong += 1
        self.streak = 0
        self.app.audio.play("wrong", 0.7)

    def _correct_key(self, target):
        self.stats.correct += 1
        self.streak += 1
        self.best_streak = max(self.best_streak, self.streak)
        self.session.score += POINTS_PER_LETTER
        self.stats.score += POINTS_PER_LETTER
        target.typed += 1
        nose = self.player.nose()
        self.player.recoil = 5
        self.effects.spark(nose[0], nose[1], (130, 215, 255), 4, 90, 0.16, 5)
        popup_pos = target.plate_rect().midtop
        self.effects.popup(popup_pos[0], popup_pos[1] - 12,
                           font(30).render(f"+{POINTS_PER_LETTER}", True, (255, 240, 130)))
        if self.streak and self.streak % 25 == 0:
            self.effects.popup(WIDTH / 2, 150, font(44).render(f"{self.streak} IN A ROW!", True, (130, 255, 190)), 1.3)
        if target is self.boss:
            self._boss_key(target, nose)
            return
        self.shots.append(Shot(nose[0], nose[1], target))
        self.app.audio.play("laser")
        if target.doomed:
            self._release_lock()

    def _boss_key(self, boss, nose):
        if boss.typed >= len(boss.text):
            # A finished letter or word fires the heavy shot: one of the ten
            boss.shots_fired += 1
            self.shots.append(Shot(nose[0], nose[1], boss, heavy=True))
            self.app.audio.play("charge_shot")
            self._release_lock()
            if not boss.doomed:
                boss.new_word()
        else:
            self.shots.append(Shot(nose[0], nose[1], _Chip(boss)))
            self.app.audio.play("laser")

    def _release_lock(self):
        if self.locked is not None:
            self.locked.locked = False
        self.locked = None

    # ---- simulation -----------------------------------------------------
    def set_state(self, state):
        self.state = state
        self.state_time = 0.0

    def update(self, dt):
        if self.paused:
            self.pause_menu.update(dt)
            return
        self.time += dt
        self.state_time += dt
        if self.state not in ("intro", "outro"):
            self.session.time += dt
            self.stats.time += dt
        if self.can_type() and self.typeable():
            self.stats.active_time += dt
        self.background.update(dt)
        aim = None
        if self.locked is not None and self.locked.alive:
            aim = (self.locked.x, self.locked.y)
        elif self.boss is not None and self.state == "boss":
            aim = (self.boss.x, self.boss.y)
        else:
            low = self.typeable()
            if low:
                aim = (low[0].x, low[0].y)
        self.player.update(dt, aim)
        self._update_state(dt)
        self._update_targets(dt)
        self._update_boss(dt)
        self._update_shots(dt)
        self._update_bullets(dt)
        ground = self.level.speed if self.background.ground else 0.0
        self.effects.update(dt, ground)
        self.damage_flash = max(0.0, self.damage_flash - dt * 2.4)

    def _update_state(self, dt):
        state = self.state
        if state == "intro":
            if self.state_time > 3.0:
                self.set_state("wave")
        elif state == "wave":
            self._spawn(dt)
            if self.spawned >= self.level.targets and not self.targets:
                self.set_state("warning")
                self.app.audio.stop_music()
                self.app.audio.play("boss_warning")
        elif state == "warning":
            if self.state_time > 2.4:
                self.boss = Boss(self.level, self.book, self.session.dealer, self.rng)
                self.set_state("boss")
                self.app.audio.play_theme(self.level.music, boss=True)
        elif state == "boss_death":
            self.boss_blasts -= dt
            if self.boss_blasts <= 0 and self.state_time < 2.0:
                self.boss_blasts = 0.16
                x = self.boss.x + self.rng.uniform(-self.boss.w * 0.42, self.boss.w * 0.42)
                y = self.boss.y + self.rng.uniform(-self.boss.h * 0.42, self.boss.h * 0.42)
                self.effects.explode("fighter", x, y)
                self.app.audio.play("destroy_fighter", 0.6)
            if self.state_time >= 2.0 and self.boss is not None:
                self.effects.big_blast(self.boss.x, self.boss.y, self.level.palette.accent)
                self.effects.big_blast(self.boss.x - 60, self.boss.y + 20, (255, 170, 80))
                self.effects.big_blast(self.boss.x + 60, self.boss.y - 20, (255, 240, 180))
                self.boss = None
                self.bullets = []
                self.app.audio.play("level_clear")
                self.set_state("outro")
        elif state == "outro":
            if self.state_time > 1.3:
                self.player.target_y = -220
            if self.state_time > 3.2:
                self._finish_level()
        elif state == "dying":
            if self.state_time > 2.8:
                self._finish_game(False)

    def _spawn(self, dt):
        if self.spawned >= self.level.targets:
            return
        self.spawn_clock -= dt
        if self.spawn_clock > 0:
            return
        active = [t for t in self.targets if not t.doomed]
        if len(active) >= self.level.max_on_screen:
            self.spawn_clock = 0.25
            return
        self.spawn_clock = self.level.spawn_interval * self.rng.uniform(0.85, 1.15)
        kinds = list(self.level.weights)
        kind = self.rng.choices(kinds, [self.level.weights[k] for k in kinds])[0]
        avoid = {t.next_letter for t in active}
        word = self.session.dealer.deal(self.level.word_length, avoid)
        # Pick the entry point farthest from whatever just arrived
        recent = [t.x for t in self.targets if t.y < 220]
        margin = 40 + len(word) * 10
        best, best_gap = WIDTH / 2, -1.0
        for _ in range(10):
            x = self.rng.uniform(margin, WIDTH - margin)
            gap = min((abs(x - other) for other in recent), default=999.0)
            if gap > best_gap:
                best, best_gap = x, gap
        self.targets.append(Target(kind, word, best, self.level, self.book, self.rng, self.player.x))
        self.spawned += 1

    def _spawn_bullet(self, x, y, vx, vy, shell=False, boss=False):
        key = "boss" if boss else ("shell" if shell else "enemy")
        self.bullets.append(Bullet(x, y, vx, vy, self.bullet_sprites[key], 7 if boss else 5))
        self.app.audio.play("enemy_shot", 0.5)

    def _update_targets(self, dt):
        for target in self.targets:
            target.update(dt, self.player, self._spawn_bullet)
            if target.kind == "missile" and self.rng.random() < 0.7:
                rad = target.heading
                self.effects.trail(target.x - math.cos(rad) * 34, target.y - math.sin(rad) * 34,
                                   (150, 130, 110), 5, 0.5)
        self._separate_plates(dt)
        px, py = self.player.x, self.player.y
        for target in self.targets:
            if not target.alive:
                continue
            if target.collides and self.state != "dying":
                reach = target.radius + 24
                if abs(target.x - px) < reach and abs(target.y - py) < reach + 6 \
                        and math.hypot(target.x - px, target.y - py) < reach:
                    self._collide(target)
                    continue
            if target.y > HEIGHT + 70 and not target.doomed:
                self._lose_target(target)
                self.stats.missed += 1
        self.targets = [t for t in self.targets if t.alive]

    def _separate_plates(self, dt):
        """Slide overlapping word plates apart so every letter stays readable."""
        items = [t for t in self.targets if not t.doomed]
        for i, a in enumerate(items):
            ra = a.plate_rect()
            for b in items[i + 1:]:
                rb = b.plate_rect()
                if abs(ra.centery - rb.centery) < (ra.height + rb.height) / 2 + 6:
                    overlap = (ra.width + rb.width) / 2 + 10 - abs(ra.centerx - rb.centerx)
                    if overlap > 0:
                        push = min(overlap, 170 * dt)
                        direction = 1 if ra.centerx >= rb.centerx else -1
                        a.offset += push * direction
                        b.offset -= push * direction

    def _lose_target(self, target):
        target.alive = False
        if self.locked is target:
            self._release_lock()

    def _collide(self, target):
        self.effects.explode(target.kind, target.x, target.y, target.level.palette.primary)
        self.app.audio.play(DESTROY_SOUND[target.kind])
        self._lose_target(target)
        self.stats.missed += 1
        self.hurt()

    def _destroy(self, target):
        target.alive = False
        self.stats.destroyed += 1
        self.effects.explode(target.kind, target.x, target.y, target.level.palette.primary)
        self.app.audio.play(DESTROY_SOUND[target.kind])
        if self.locked is target:
            self._release_lock()

    def hurt(self):
        if self.player.invulnerable > 0 or self.state in ("dying", "outro", "boss_death"):
            return
        session = self.session
        session.hp -= 1
        self.stats.hits_taken += 1
        self.damage_flash = 1.0
        self.effects.shake = max(self.effects.shake, 9)
        self.effects.spark(self.player.x, self.player.y, (255, 120, 70), 16, 220, 0.4, 6)
        self.streak = 0
        if session.hp > 0:
            self.app.audio.play("player_hit")
            return
        session.lives -= 1
        self.effects.big_blast(self.player.x, self.player.y, (255, 160, 70))
        self.app.audio.play("life_lost")
        self.bullets = []
        self._release_lock()
        if session.lives > 0:
            session.hp = MAX_HP
            self.player.invulnerable = INVULNERABLE_TIME + 1.0
        else:
            session.hp = 0
            self.player.visible = False
            self.app.audio.stop_music()
            self.set_state("dying")

    def _update_boss(self, dt):
        if self.boss is not None:
            self.boss.update(dt, self.player, self._spawn_bullet)

    def _update_shots(self, dt):
        for shot in self.shots:
            shot.update(dt)
            if shot.heavy:
                self.effects.trail(shot.x, shot.y, (255, 170, 80), 7, 0.25)
            if shot.done:
                self._shot_landed(shot)
        self.shots = [s for s in self.shots if not s.done]

    def _shot_landed(self, shot):
        target = shot.target
        if isinstance(target, _Chip):
            boss = target.boss
            boss.flash = max(boss.flash, 0.25)
            self.effects.spark(shot.x, shot.y, (160, 230, 255), 5, 120, 0.2, 4)
            return
        if target is self.boss:
            target.hits += 1
            target.flash = 1.0
            self.effects.spark(target.x, target.y + target.h * 0.2, (255, 200, 110), 22, 280, 0.5, 8)
            self.effects.ring(target.x, target.y, 110, (255, 220, 150))
            self.effects.shake = max(self.effects.shake, 8)
            self.app.audio.play("boss_hit")
            if target.hits >= BOSS_SHOTS and not target.dying:
                self._boss_defeated(target)
            return
        if not isinstance(target, Target) or not target.alive:
            return
        target.hits += 1
        target.flash = 1.0
        self.effects.spark(shot.x, shot.y, (170, 230, 255), 6, 130, 0.22, 5)
        if target.hits >= len(target.text):
            self._destroy(target)
            self.targets = [t for t in self.targets if t.alive]

    def _boss_defeated(self, boss):
        boss.dying = True
        self.bullets = []
        self.stats.destroyed += 1
        self.session.score += BOSS_BONUS
        self.stats.score += BOSS_BONUS
        self.effects.popup(WIDTH / 2, 240, font(52).render(f"BOSS DESTROYED  +{BOSS_BONUS}", True, (255, 230, 130)), 1.8)
        self.app.audio.stop_music()
        self.app.audio.play("boss_explode")
        self.set_state("boss_death")

    def _update_bullets(self, dt):
        px, py = self.player.x, self.player.y
        for bullet in self.bullets:
            bullet.update(dt)
        hit_any = False
        keep = []
        for bullet in self.bullets:
            if bullet.gone:
                continue
            if self.state != "dying" and math.hypot(bullet.x - px, bullet.y - py) < bullet.radius + PLAYER_HIT_RADIUS:
                hit_any = True
                self.effects.spark(bullet.x, bullet.y, (255, 200, 150), 6, 140, 0.25, 5)
                continue
            keep.append(bullet)
        self.bullets = keep
        if hit_any:
            self.hurt()

    # ---- endings --------------------------------------------------------
    def _record(self):
        self.app.last_bests = storage.record_level(self.stats.number, self.stats.wpm,
                                                   self.stats.accuracy, self.stats.completed)

    def _finish_level(self):
        from .scenes import LevelSummary
        self.stats.completed = True
        self._record()
        self.session.hp = min(MAX_HP, self.session.hp + LEVEL_CLEAR_REPAIR)
        self.app.switch(LevelSummary(self.app, self.session, self.stats, self.app.last_bests))

    def _finish_game(self, victory):
        from .scenes import ResultsScene
        self.session.victory = victory
        if self.stats.correct or self.stats.wrong:
            self._record()
        self.app.audio.play("game_over")
        self.app.switch(ResultsScene(self.app, self.session))

    # ---- drawing --------------------------------------------------------
    def draw(self, surf):
        world = self.world
        self.background.draw(world)
        self.effects.draw_decals(world)
        self._draw_rail(world)
        for target in self.targets:
            if target.kind == "tank":
                target.draw(world)
        for target in self.targets:
            if target.kind != "tank":
                target.draw(world)
        if self.boss:
            self.boss.draw(world)
        for bullet in self.bullets:
            bullet.draw(world)
        self.player.draw(world)
        for shot in self.shots:
            shot.draw(world)
        self.effects.draw(world)
        self._draw_plates(world)
        world.blit(self.vignette, (0, 0))
        ox, oy = self.effects.shake_offset()
        surf.blit(world, (ox, oy))
        if self.damage_flash > 0:
            red = pygame.Surface((WIDTH, HEIGHT))
            red.fill((150, 16, 16))
            red.set_alpha(int(110 * self.damage_flash))
            surf.blit(red, (0, 0))
        from .hud import draw_hud
        draw_hud(surf, self)
        self._draw_banners(surf)
        if self.paused:
            self._draw_pause(surf)

    def _draw_rail(self, surf):
        y = RAIL_Y + 50
        pygame.draw.line(surf, (8, 14, 26), (0, y + 2), (WIDTH, y + 2), 4)
        pygame.draw.line(surf, (70, 180, 240), (0, y), (WIDTH, y), 2)
        offset = int(self.time * 90) % 48
        for x in range(-48 + offset, WIDTH, 48):
            pygame.draw.rect(surf, (150, 225, 255), (x, y - 1, 10, 3))
        if self.player.visible:
            px = int(self.player.x)
            pygame.draw.rect(surf, (20, 30, 52), (px - 24, y - 5, 48, 10), border_radius=4)
            pygame.draw.rect(surf, (255, 170, 80), (px - 24, y - 5, 48, 10), 2, border_radius=4)

    def _draw_plates(self, surf):
        ordered = sorted(self.targets, key=lambda t: t.locked)
        for target in ordered:
            if target.doomed:
                continue
            rect = target.plate_rect()
            if rect.bottom < TOP_BAR_H:
                continue
            nudge = math.sin(target.shake * 40) * 6 * target.shake if target.shake else 0.0
            draw_plate(surf, rect, target.text, target.typed, target.locked,
                       target.y > RAIL_Y - 210, nudge)
        target = self.locked
        if target is not None and target.alive and target is not self.boss:
            self._draw_reticle(surf, target.x, target.y, max(target.sprite.get_width(), 44) * 0.62)
        boss = self.boss
        if boss and not boss.dying and boss.arrived and not boss.doomed:
            draw_plate(surf, boss.plate_rect(), boss.text, boss.typed, boss.locked, False,
                       math.sin(boss.shake * 40) * 6 * boss.shake if boss.shake else 0.0, boss=True)

    def _draw_reticle(self, surf, x, y, r):
        spin = self.time * 3
        for i in range(4):
            a = spin + i * math.pi / 2
            cx, cy = x + math.cos(a) * r, y + math.sin(a) * r
            tangent = a + math.pi / 2
            ex, ey = math.cos(tangent) * 9, math.sin(tangent) * 9
            pygame.draw.line(surf, (255, 215, 90), (cx - ex, cy - ey), (cx + ex, cy + ey), 3)

    def _draw_banners(self, surf):
        level = self.level
        if self.state == "intro":
            k = min(1.0, self.state_time * 2.5, (3.0 - self.state_time) * 2.5)
            layer = pygame.Surface((WIDTH, 300), pygame.SRCALPHA)
            title = fancy_title(f"LEVEL {level.number}", 96, (255, 255, 255), (255, 190, 90), (220, 110, 30))
            layer.blit(title, title.get_rect(center=(WIDTH // 2, 70)))
            text(layer, level.name, 60, (240, 245, 255), (WIDTH // 2, 158), "center")
            text(layer, level.tagline, 32, (190, 220, 255), (WIDTH // 2, 208), "center")
            text(layer, f"Type: {describe_challenge(level)}", 32, (255, 232, 130), (WIDTH // 2, 246), "center")
            layer.set_alpha(int(255 * max(0.0, k)))
            surf.blit(layer, (0, 150))
        elif self.state == "warning":
            if int(self.state_time * 5) % 2 == 0:
                band = pygame.Surface((WIDTH, 110), pygame.SRCALPHA)
                band.fill((170, 20, 20, 150))
                surf.blit(band, (0, 220))
                text(surf, "WARNING", 84, (255, 240, 220), (WIDTH // 2, 262), "center")
                text(surf, f"{level.boss_name} APPROACHING", 34, (255, 220, 180), (WIDTH // 2, 310), "center")
        elif self.state == "outro":
            k = min(1.0, self.state_time * 2.5)
            title = fancy_title("LEVEL CLEAR!", 92, (255, 255, 255), (130, 255, 170), (30, 180, 90))
            title.set_alpha(int(255 * k))
            surf.blit(title, title.get_rect(center=(WIDTH // 2, 300)))
        elif self.state == "dying":
            k = min(1.0, self.state_time * 1.2)
            title = fancy_title("GAME OVER", 110, (255, 255, 255), (255, 90, 90), (190, 20, 20))
            title.set_alpha(int(255 * k))
            surf.blit(title, title.get_rect(center=(WIDTH // 2, 300)))

    def _draw_pause(self, surf):
        veil = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        veil.fill((0, 0, 16, 170))
        surf.blit(veil, (0, 0))
        title = fancy_title(t("pause.title"), 86)
        surf.blit(title, title.get_rect(center=(WIDTH // 2, HEIGHT // 2 - 70)))
        self.pause_menu.draw(surf)
        text(surf, t("pause.note"), 24, (190, 200, 220),
             (WIDTH // 2, HEIGHT // 2 + 112), "center")


class _Chip:
    """Aim point for the small lasers fired while spelling out a boss word."""

    def __init__(self, boss):
        self.boss = boss
        self.dx = boss.rng.uniform(-boss.w * 0.3, boss.w * 0.3)
        self.dy = boss.rng.uniform(-boss.h * 0.2, boss.h * 0.3)

    @property
    def x(self):
        return self.boss.x + self.dx

    @property
    def y(self):
        return self.boss.y + self.dy

