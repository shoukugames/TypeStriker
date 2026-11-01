"""The player's ship, enemies, objects, bosses and everything that flies."""
import math
from collections import deque

import pygame

from . import art
from .config import BOSS_SHOTS, DODGE_DISTANCE, HEIGHT, RAIL_AMPLITUDE, RAIL_Y, SHIP_KINDS, TOP_BAR_H, WIDTH

ROCK_TINTS = {"forest": (120, 106, 88), "desert": (170, 120, 80), "ice": (170, 200, 224),
              "lava": (112, 66, 50), "hull": (110, 104, 130)}
DEFAULT_ROCK = (146, 122, 104)

PLAYER_HIT_RADIUS = 15
ROLL_TIME = 0.45

KIND_FACTORS = {
    # speed, collision radius
    "scout": (1.05, 22), "fighter": (1.0, 26), "bomber": (0.82, 36), "saucer": (0.94, 30),
    "interceptor": (1.14, 24), "drone": (0.98, 26), "tank": (1.0, 0), "asteroid": (0.92, 26),
    "missile": (1.32, 16),
}
# How likely each kind is to be the one that opens fire. Rocks and missiles never shoot.
FIRE_WEIGHTS = {"scout": 2, "fighter": 3, "bomber": 4, "saucer": 3, "interceptor": 2.5,
                "drone": 2.5, "tank": 4}
# Extra shots either side of the aimed one, in radians
BOSS_SPREADS = {"aimed": (), "burst": (-0.1, 0.1), "spread3": (-0.22, 0.22),
                "fan5": (-0.4, -0.2, 0.2, 0.4), "ring": (-1.02, -0.68, -0.34, 0.34, 0.68, 1.02)}


class Player:
    def __init__(self, sprite):
        self.sprite = sprite
        self.t = 0.0
        self.x = WIDTH / 2
        self.y = HEIGHT + 120
        self.angle = 0.0
        self.aim = 0.0
        self.recoil = 0.0
        self.invulnerable = 0.0
        self.flame = 0.0
        self.visible = True
        self.target_y = RAIL_Y
        self.offset = 0.0       # sideways jump away from the rail's course while dodging
        self.dodge_goal = 0.0
        self.dodge_hold = 0.0
        self.roll = 0.0
        self.ghosts = deque(maxlen=5)

    def rail_x(self, t):
        """The ship's fixed course along the rail. The player never steers it."""
        return (WIDTH / 2 + RAIL_AMPLITUDE * 0.86 * math.sin(t * 0.42)
                + RAIL_AMPLITUDE * 0.14 * math.sin(t * 1.21))

    def update(self, dt, aim_at=None):
        self.t += dt
        self.flame += dt
        self.dodge_hold = max(0.0, self.dodge_hold - dt)
        if self.dodge_hold > 0:
            self.offset += (self.dodge_goal - self.offset) * min(1.0, dt * 14)
        else:
            self.offset += -self.offset * min(1.0, dt * 3)
        self.x = max(40.0, min(WIDTH - 40.0, self.rail_x(self.t) + self.offset))
        self.roll = max(0.0, self.roll - dt)
        if self.roll > 0:
            self.ghosts.append((self.x, self.y))
        else:
            self.ghosts.clear()
        self.y += (self.target_y + math.sin(self.t * 2.1) * 3 - self.y) * min(1.0, dt * 3.2)
        self.recoil = max(0.0, self.recoil - dt * 40)
        self.invulnerable = max(0.0, self.invulnerable - dt)
        desired = 0.0
        if aim_at is not None:
            dx, dy = aim_at[0] - self.x, self.y - aim_at[1]
            desired = max(-24.0, min(24.0, math.degrees(math.atan2(dx, max(1.0, dy)))))
        self.aim += (desired - self.aim) * min(1.0, dt * 12)

    def x_at(self, later):
        """Where the ship will be along the rail after that many seconds."""
        return self.rail_x(self.t + later) + self.offset

    def dodge(self, hold):
        """Jump clear and stay there for hold seconds, until the shot has gone past."""
        if self.dodge_hold > 0 and self.dodge_goal:
            self.dodge_goal = -self.dodge_goal  # already jumped, so a second shot means the other way
        else:
            self.dodge_goal = DODGE_DISTANCE if self.rail_x(self.t + hold) < WIDTH / 2 else -DODGE_DISTANCE
        self.dodge_hold = max(self.dodge_hold, hold)
        self.roll = ROLL_TIME

    def nose(self):
        rad = math.radians(self.aim)
        return (self.x + math.sin(rad) * 40, self.y - math.cos(rad) * 40)

    def draw(self, surf):
        if not self.visible:
            return
        if self.invulnerable > 0 and int(self.invulnerable * 12) % 2 == 0:
            return
        rad = math.radians(self.aim)
        y = self.y + self.recoil * math.cos(rad)
        x = self.x - self.recoil * math.sin(rad)
        # Engine flames stay behind the hull
        length = 18 + 7 * math.sin(self.flame * 30) + 3 * math.sin(self.flame * 57)
        for dx in (-5.5, 5.5):
            fx = x + math.cos(rad) * dx - math.sin(rad) * 40
            fy = y + math.sin(rad) * dx + math.cos(rad) * 40
            for r, col, reach in ((13, (255, 110, 30), 1.0), (8, (255, 210, 110), 0.6), (5, (255, 255, 240), 0.3)):
                gx, gy = fx - math.sin(rad) * length * reach, fy + math.cos(rad) * length * reach
                glow = art.additive(r, col, 1.2)
                surf.blit(glow, (gx - r, gy - r), special_flags=pygame.BLEND_RGB_ADD)
        rotated = pygame.transform.rotozoom(self.sprite, -self.aim, 1.0)
        if self.roll > 0:
            # A barrel roll: the hull narrows and widens as it turns over
            squash = max(0.2, abs(math.cos((1.0 - self.roll / ROLL_TIME) * math.tau)))
            rotated = pygame.transform.smoothscale(
                rotated, (max(1, int(rotated.get_width() * squash)), rotated.get_height()))
            for i, (gx, gy) in enumerate(self.ghosts):
                rotated.set_alpha(25 + i * 20)
                surf.blit(rotated, (gx - rotated.get_width() / 2, gy - rotated.get_height() / 2))
            rotated.set_alpha(255)
        surf.blit(rotated, (x - rotated.get_width() / 2, y - rotated.get_height() / 2))


class Target:
    """An enemy or flying object carrying one letter or word.

    Each correct letter is one shot, so an enemy takes as many hits as its text
    has letters. Single letters on levels 1-3 therefore take one hit.
    """

    def __init__(self, kind, text, x, level, book, rng, player_x):
        self.kind = kind
        self.text = text
        self.level = level
        self.rng = rng
        self.typed = 0          # letters typed correctly
        self.hits = 0           # shots that have landed
        self.alive = True
        self.locked = False
        self.flash = 0.0
        self.shake = 0.0
        self.t = rng.uniform(0, 6.28)
        self.age = 0.0
        factor, self.radius = KIND_FACTORS[kind]
        self.speed = level.speed * factor
        self.x0 = x
        self.x = x
        self.y = -70.0
        self.offset = 0.0
        self.vx, self.vy = 0.0, self.speed
        self.heading = math.pi / 2
        self.spin = 0.0
        self.spin_rate = 0.0
        self.turret_angle = 180.0
        pal = level.palette
        if kind == "tank":
            self.hull = book.hull(pal)
            self.turret = book.turret(pal)
            self.sprite = self.hull
            self.speed = level.speed
        elif kind == "asteroid":
            size = rng.choice((58, 70, 84))
            tint = ROCK_TINTS.get(level.theme, DEFAULT_ROCK)
            self.sprite = book.asteroid(size, rng.randint(1, 4), tint)
            self.radius = size * 0.34
            self.spin_rate = rng.uniform(-60, 60)
            aim_x = player_x if rng.random() < 0.55 else rng.uniform(80, WIDTH - 80)
            self.vx = (aim_x - x) / ((RAIL_Y + 70) / self.speed)
        elif kind == "missile":
            self.sprite = book.missile(pal)
        else:
            self.sprite = book.enemy(kind, pal)
        self.white = art.flash_copy(self.sprite)
        self.half_h = self.sprite.get_height() / 2

    # ---- typing ---------------------------------------------------------
    @property
    def next_letter(self):
        return self.text[self.typed] if self.typed < len(self.text) else ""

    @property
    def doomed(self):
        return self.typed >= len(self.text)

    @property
    def collides(self):
        return self.kind != "tank" and not self.doomed

    @property
    def on_screen(self):
        """True once the whole letter plate has cleared the score bar."""
        return self.plate_rect().top >= TOP_BAR_H - 2

    @property
    def can_fire(self):
        return self.kind in FIRE_WEIGHTS and not self.doomed and self.on_screen and self.y < RAIL_Y - 250

    # ---- movement -------------------------------------------------------
    def update(self, dt, player):
        self.t += dt
        self.age += dt
        self.flash = max(0.0, self.flash - dt * 6)
        self.shake = max(0.0, self.shake - dt * 4)
        self._move(dt, player)
        half = self.plate_width() / 2 + 6
        self.x = max(half, min(WIDTH - half, self.x))

    def _move(self, dt, player):
        kind = self.kind
        if kind == "asteroid":
            self.spin += self.spin_rate * dt
            self.x0 += self.vx * dt
            self.y += self.speed * dt
            self.x = self.x0 + self.offset
            return
        if kind == "missile":
            want = math.atan2(player.y - self.y, player.x - self.x)
            diff = (want - self.heading + math.pi) % math.tau - math.pi
            # Turning tightens with age, so a missile can never circle the ship forever
            turn = (1.1 + self.age * 0.3) * dt
            self.heading += max(-turn, min(turn, diff))
            self.x0 += math.cos(self.heading) * self.speed * dt
            self.y += math.sin(self.heading) * self.speed * dt
            self.x = self.x0 + self.offset
            return
        if kind == "tank":
            self.y += self.speed * dt
            self.x0 += math.sin(self.t * 0.5) * 16 * dt
            self.x = self.x0 + self.offset
            dx, dy = player.x - self.x, player.y - self.y
            want = math.degrees(math.atan2(-dx, -dy))
            diff = (want - self.turret_angle + 180) % 360 - 180
            self.turret_angle += max(-90 * dt, min(90 * dt, diff))
            return
        self.y += self.speed * dt
        sway = 0.0
        if kind == "scout":
            sway = math.sin(self.t * 1.6) * 46
        elif kind == "saucer":
            sway = math.sin(self.t * 0.9) * 130
        elif kind == "interceptor":
            sway = (abs((self.t * 0.5) % 2 - 1) * 2 - 1) * 90
        elif kind == "drone":
            sway = math.sin(self.t * 2.4) * 34 + math.sin(self.t * 0.7) * 70
        elif kind == "bomber":
            sway = math.sin(self.t * 0.5) * 30
        # Anything still flying near the rail dives at the ship
        if self.y > RAIL_Y - 170:
            pull = player.x - (self.x0 + sway + self.offset)
            self.x0 += max(-220.0, min(220.0, pull * 2.2)) * dt
        self.x = self.x0 + sway + self.offset

    # ---- drawing --------------------------------------------------------
    def plate_width(self):
        n = len(self.text)
        return 46 if n == 1 else n * 20 + 18

    def plate_rect(self):
        w, h = self.plate_width(), 42 if len(self.text) == 1 else 34
        # The plate trails behind the ship, which flies down the screen
        return pygame.Rect(self.x - w / 2, self.y - self.half_h - h + 8, w, h)

    def draw(self, surf):
        x, y = self.x, self.y
        sprite = self.sprite
        if self.kind == "tank":
            hull_r = surf.blit(self.hull, (x - self.hull.get_width() / 2, y - self.hull.get_height() / 2))
            turret = pygame.transform.rotate(self.turret, self.turret_angle)
            surf.blit(turret, (x - turret.get_width() / 2, y - turret.get_height() / 2))
            if self.flash > 0:
                self.white.set_alpha(int(190 * min(1.0, self.flash * 2)))
                surf.blit(self.white, hull_r.topleft)
            return
        if self.kind == "asteroid":
            sprite = pygame.transform.rotate(sprite, self.spin)
        elif self.kind == "missile":
            sprite = pygame.transform.rotate(sprite, 90 - math.degrees(self.heading))
            rad = self.heading
            tail = (x - math.cos(rad) * 32, y - math.sin(rad) * 32)
            glow = art.additive(10, (255, 170, 70), 1.2)
            surf.blit(glow, (tail[0] - 10, tail[1] - 10), special_flags=pygame.BLEND_RGB_ADD)
        elif self.kind in SHIP_KINDS:
            # Exhaust glow behind each ship
            glow = art.additive(int(self.half_h * 0.55), self.level.palette.accent, 1.5)
            surf.blit(glow, (x - glow.get_width() / 2, y - self.half_h - glow.get_height() * 0.28),
                      special_flags=pygame.BLEND_RGB_ADD)
        rect = surf.blit(sprite, (x - sprite.get_width() / 2, y - sprite.get_height() / 2))
        if self.flash > 0 and sprite is self.sprite:
            self.white.set_alpha(int(220 * min(1.0, self.flash * 2)))
            surf.blit(self.white, rect.topleft)


class Boss:
    """Takes exactly ten shots. Each shot is fired by finishing one letter or word."""

    def __init__(self, level, book, dealer, rng):
        self.level = level
        self.rng = rng
        self.sprite = book.boss(level.boss)
        self.white = art.flash_copy(self.sprite)
        self.w, self.h = self.sprite.get_size()
        self.x = WIDTH / 2
        self.home_y = 66 + self.h / 2
        self.y = -self.h
        self.t = 0.0
        self.hits = 0
        self.flash = 0.0
        self.dealer = dealer
        self.text = ""
        self.typed = 0
        self.shots_fired = 0
        self.cooldown = 2.2
        self.alive = True
        self.dying = False
        self.locked = False
        self.shake = 0.0
        self.core = art.BOSS_CORE[level.boss]
        self.new_word()

    kind = "boss"

    def new_word(self, avoid_first=()):
        self.text = self.dealer.deal(self.level.word_length, avoid_first)
        self.typed = 0

    @property
    def next_letter(self):
        return self.text[self.typed] if self.typed < len(self.text) else ""

    @property
    def doomed(self):
        return self.shots_fired >= BOSS_SHOTS

    @property
    def on_screen(self):
        return self.arrived

    @property
    def arrived(self):
        return self.y > self.home_y - 6

    def update(self, dt, fire_volley):
        self.t += dt
        self.flash = max(0.0, self.flash - dt * 6)
        self.shake = max(0.0, self.shake - dt * 4)
        if self.dying:
            self.y += 22 * dt
            return
        self.y += (self.home_y + math.sin(self.t * 1.5) * 8 - self.y) * min(1.0, dt * 1.6)
        margin = self.w / 2 + 8
        swing = max(0.0, WIDTH / 2 - margin)
        self.x = WIDTH / 2 + math.sin(self.t * self.level.boss_speed / 170) * swing
        if self.arrived and not self.doomed:
            self.cooldown -= dt
            if self.cooldown <= 0:
                spread = BOSS_SPREADS[self.level.boss_pattern]
                if fire_volley(self.x, self.y + self.h * 0.38, spread, boss=True):
                    # A boss left alone grows angrier, so it can't simply be ignored
                    anger = max(0.5, 1.0 - max(0.0, self.t - 30.0) / 70.0)
                    self.cooldown = self.level.boss_fire_interval * anger * self.rng.uniform(0.9, 1.1)
                else:
                    self.cooldown = 0.3

    def plate_width(self):
        return 46 if len(self.text) == 1 else len(self.text) * 22 + 22

    def plate_rect(self):
        w, h = self.plate_width(), 42
        cx = max(w / 2 + 8, min(WIDTH - w / 2 - 8, self.x))
        return pygame.Rect(cx - w / 2, self.y + self.h / 2 + 6, w, h)

    def draw(self, surf):
        x = self.x - self.w / 2
        y = self.y - self.h / 2
        if self.dying:
            x += self.rng.uniform(-5, 5)
            y += self.rng.uniform(-3, 3)
        rect = surf.blit(self.sprite, (x, y))
        dx, dy, col = self.core
        pulse = 0.55 + 0.45 * math.sin(self.t * 4)
        radius = int(26 + 12 * pulse)
        glow = art.additive(radius, art.dim(col, 0.4 + 0.5 * pulse), 1.4)
        surf.blit(glow, (self.x + dx - radius, self.y + dy - radius), special_flags=pygame.BLEND_RGB_ADD)
        if self.flash > 0:
            self.white.set_alpha(int(200 * min(1.0, self.flash * 2)))
            surf.blit(self.white, rect.topleft)


class Bullet:
    __slots__ = ("x", "y", "vx", "vy", "sprite", "radius", "half")

    def __init__(self, x, y, vx, vy, sprite, radius):
        self.x, self.y, self.vx, self.vy = x, y, vx, vy
        self.sprite = sprite
        self.radius = radius
        self.half = sprite.get_width() / 2

    def update(self, dt):
        self.x += self.vx * dt
        self.y += self.vy * dt

    @property
    def gone(self):
        return not (-30 < self.x < WIDTH + 30 and -30 < self.y < HEIGHT + 30)

    def draw(self, surf):
        surf.blit(self.sprite, (self.x - self.half, self.y - self.half), special_flags=pygame.BLEND_RGB_ADD)


class Volley:
    """One enemy attack: its bullets, and the letters that dodge it.

    The lead bullet steers to meet the ship exactly when the time is up, so a shot
    always lands unless it is dodged, and every shot gives the same time to react.
    """

    def __init__(self, text, flight, lead, others=()):
        self.text = text
        self.typed = 0
        self.flight = flight
        self.age = 0.0
        self.lead = lead
        self.bullets = [lead, *others]
        self.dodged = False
        self.spent = False      # already hit the ship, so the rest of it can't hurt
        self.shake = 0.0

    @property
    def next_letter(self):
        return self.text[self.typed] if self.typed < len(self.text) else ""

    @property
    def is_threat(self):
        return not self.dodged and not self.spent

    @property
    def time_left(self):
        return max(0.0, self.flight - self.age)

    def update(self, dt, player):
        self.age += dt
        self.shake = max(0.0, self.shake - dt * 4)
        remaining = self.flight - self.age
        if self.is_threat and remaining > 0.03:
            self.lead.vx = (player.x_at(remaining) - self.lead.x) / remaining
            self.lead.vy = (player.y - self.lead.y) / remaining
        for bullet in self.bullets:
            bullet.update(dt)
        self.bullets = [b for b in self.bullets if not b.gone]

    def plate_rect(self):
        n = len(self.text)
        w, h = (46, 42) if n == 1 else (n * 20 + 18, 34)
        rect = pygame.Rect(self.lead.x - w / 2, self.lead.y - h - 12, w, h)
        return rect.clamp(pygame.Rect(4, TOP_BAR_H + 4, WIDTH - 8, HEIGHT))


class Shot:
    """A player's laser. It homes in, so a correct key can never miss."""

    def __init__(self, x, y, target, heavy=False):
        self.x, self.y = x, y
        self.target = target
        self.heavy = heavy
        self.speed = 1100 if heavy else 1650
        self.px, self.py = x, y
        self.done = False

    def update(self, dt):
        self.px, self.py = self.x, self.y
        tx, ty = self.target.x, self.target.y
        dx, dy = tx - self.x, ty - self.y
        dist = math.hypot(dx, dy)
        step = self.speed * dt
        if dist <= step or dist < 8:
            self.x, self.y = tx, ty
            self.done = True
            return
        self.x += dx / dist * step
        self.y += dy / dist * step

    def draw(self, surf):
        if self.heavy:
            for r, col in ((24, (255, 150, 60)), (14, (255, 230, 150)), (7, (255, 255, 255))):
                g = art.additive(r, col, 1.2)
                surf.blit(g, (self.x - r, self.y - r), special_flags=pygame.BLEND_RGB_ADD)
        else:
            pygame.draw.line(surf, (70, 190, 255), (self.px, self.py), (self.x, self.y), 7)
            pygame.draw.line(surf, (190, 240, 255), (self.px, self.py), (self.x, self.y), 3)
            g = art.additive(11, (110, 210, 255), 1.3)
            surf.blit(g, (self.x - 11, self.y - 11), special_flags=pygame.BLEND_RGB_ADD)
