"""The player's ship, enemies, objects, bosses and everything that flies."""
import math

import pygame

from . import art
from .config import BOSS_SHOTS, HEIGHT, RAIL_AMPLITUDE, RAIL_Y, SHIP_KINDS, TOP_BAR_H, WIDTH

ROCK_TINTS = {"forest": (120, 106, 88), "desert": (170, 120, 80), "ice": (170, 200, 224),
              "lava": (112, 66, 50), "hull": (110, 104, 130)}
DEFAULT_ROCK = (146, 122, 104)

AIM_SCATTER = 95
PLAYER_HIT_RADIUS = 15

KIND_FACTORS = {
    # speed, collision radius
    "scout": (1.05, 22), "fighter": (1.0, 26), "bomber": (0.82, 36), "saucer": (0.94, 30),
    "interceptor": (1.14, 24), "drone": (0.98, 26), "tank": (1.0, 0), "asteroid": (0.92, 26),
    "missile": (1.32, 16),
}
FIRE_FACTORS = {"scout": 1.5, "fighter": 1.0, "bomber": 0.72, "saucer": 1.1, "interceptor": 1.3,
                "drone": 1.2, "tank": 0.75}


class Player:
    def __init__(self, sprite):
        self.sprite = sprite
        self.t = 0.0
        self.x = WIDTH / 2
        self.y = HEIGHT + 120
        self.prev_x = self.x
        self.angle = 0.0
        self.aim = 0.0
        self.recoil = 0.0
        self.invulnerable = 0.0
        self.flame = 0.0
        self.visible = True
        self.target_y = RAIL_Y

    def rail_x(self, t):
        """The ship's fixed course along the rail. The player never steers it."""
        return (WIDTH / 2 + RAIL_AMPLITUDE * 0.86 * math.sin(t * 0.42)
                + RAIL_AMPLITUDE * 0.14 * math.sin(t * 1.21))

    def update(self, dt, aim_at=None):
        self.t += dt
        self.flame += dt
        self.prev_x = self.x
        self.x = self.rail_x(self.t)
        self.y += (self.target_y + math.sin(self.t * 2.1) * 3 - self.y) * min(1.0, dt * 3.2)
        self.recoil = max(0.0, self.recoil - dt * 40)
        self.invulnerable = max(0.0, self.invulnerable - dt)
        desired = 0.0
        if aim_at is not None:
            dx, dy = aim_at[0] - self.x, self.y - aim_at[1]
            desired = max(-24.0, min(24.0, math.degrees(math.atan2(dx, max(1.0, dy)))))
        self.aim += (desired - self.aim) * min(1.0, dt * 12)

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
        self.cooldown = 0.0
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
        if kind in FIRE_FACTORS:
            self.fire_every = level.fire_interval * FIRE_FACTORS[kind]
            self.cooldown = rng.uniform(0.4, 1.0) * self.fire_every
        else:
            self.fire_every = 0

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

    # ---- movement -------------------------------------------------------
    def update(self, dt, player, spawn_bullet):
        self.t += dt
        self.age += dt
        self.flash = max(0.0, self.flash - dt * 6)
        self.shake = max(0.0, self.shake - dt * 4)
        self._move(dt, player)
        half = self.plate_width() / 2 + 6
        self.x = max(half, min(WIDTH - half, self.x))
        if self.fire_every and not self.doomed and 40 < self.y < RAIL_Y - 190:
            self.cooldown -= dt
            if self.cooldown <= 0:
                self.cooldown = self.fire_every * self.rng.uniform(0.85, 1.15)
                self._fire(player, spawn_bullet)

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

    def _fire(self, player, spawn_bullet):
        lead = self.rng.uniform(0.0, 1.0)
        speed = self.level.bullet_speed
        muzzle_y = self.y + self.half_h * 0.6
        dist = max(1.0, math.hypot(player.x - self.x, player.y - muzzle_y))
        flight = dist / speed
        velocity = (player.x - player.prev_x) * 60
        # The ship can't dodge, so enemy aim is deliberately imperfect
        aim_x = player.x + velocity * flight * lead + self.rng.uniform(-AIM_SCATTER, AIM_SCATTER)
        a = math.atan2(player.y - muzzle_y, aim_x - self.x)
        shell = self.kind == "tank"
        spawn_bullet(self.x, muzzle_y, math.cos(a) * speed, math.sin(a) * speed, shell)

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

    def new_word(self):
        self.text = self.dealer.deal(self.level.word_length)
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

    def update(self, dt, player, spawn_bullet):
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
                # A boss left alone grows angrier, so it can't simply be ignored
                anger = max(0.35, 1.0 - max(0.0, self.t - 30.0) / 70.0)
                self.cooldown = self.level.boss_fire_interval * anger * self.rng.uniform(0.9, 1.1)
                self._fire(player, spawn_bullet)

    def _fire(self, player, spawn_bullet):
        speed = self.level.bullet_speed * 0.95
        mx, my = self.x, self.y + self.h * 0.38
        aim_x = player.x + self.rng.uniform(-AIM_SCATTER, AIM_SCATTER) * 0.7
        base = math.atan2(player.y - my, aim_x - mx)
        pattern = self.level.boss_pattern
        if pattern == "aimed":
            angles = [base]
        elif pattern == "spread3":
            angles = [base - 0.22, base, base + 0.22]
        elif pattern == "fan5":
            angles = [base + i * 0.2 for i in (-2, -1, 0, 1, 2)]
        elif pattern == "burst":
            angles = [base - 0.1, base + 0.1]
        else:  # ring
            angles = [math.pi / 2 + i * 0.34 for i in range(-3, 4)]
        for a in angles:
            spawn_bullet(mx, my, math.cos(a) * speed, math.sin(a) * speed, False, True)

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
